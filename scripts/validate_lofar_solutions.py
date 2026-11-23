#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Roland Timmerman, Jurjen de Jong (jurjendejong@strw.leidenuniv.nl)"

import csv
import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path
from pprint import pprint
from typing import Union, Sequence, Literal

import numpy as np
import pandas as pd
import tables
from scipy.stats import circstd
from scipy.optimize import leastsq
from losoto.lib_operations import reorderAxes

from make_config_international import parse_source_id
from make_config_dical import make_utf8

PHASE_THRESHOLD = 0.5
AMPLITUDE_THRESHOLD = 0.85
MAX_STATION_FLAG_FRACTION = 0.15
MAX_VISIBILITY_FLAG_FRACTION = 0.05


def get_ms_phase_weights(ms: str, times: np.ndarray, freqs: np.ndarray,
                         ants: np.ndarray, uvmin: float,
                         station_flags: np.ndarray | None = None):
    """Return station sensitivity weights and the additional flagged fraction.

    Sum usable XX+YY weights on cross-baselines above uvmin (wavelengths).
    These describe input sensitivity, not fitted-solution uncertainties.
    The cap counts newly excluded cells once across all correlations and UVs,
    divided by initially unflagged, finite, positive-weight cross-correlation
    cells. Neither MS flags nor visibility weights are modified.
    """
    from casacore.tables import table

    if not np.isfinite(uvmin) or uvmin < 0:
        raise ValueError("The weighting UV minimum must be finite and nonnegative.")
    if not len(times) or np.any(np.diff(times) <= 0):
        raise ValueError("Expected nonempty, increasing solution times.")
    names = [make_utf8(a) for a in ants]
    with table(str(Path(ms) / "ANTENNA"), readonly=True, ack=False) as tab:
        ms_names = [make_utf8(a) for a in tab.getcol("NAME")]
    if not set(names).issubset(ms_names):
        raise ValueError("Solution stations are missing from the weighting MS.")
    mapped = np.array([names.index(a) if a in names else -1 for a in ms_names])
    with table(str(Path(ms) / "SPECTRAL_WINDOW"), readonly=True, ack=False) as tab:
        if tab.nrows() != 1:
            raise ValueError("Weighting requires one spectral window.")
        ms_freqs = tab.getcell("CHAN_FREQ", 0)
        if ms_freqs.shape != freqs.shape or not np.allclose(ms_freqs, freqs, rtol=0, atol=1e-3):
            raise ValueError("Weighting MS and H5 frequency grids must match.")
    with table(str(Path(ms) / "POLARIZATION"), readonly=True, ack=False) as tab:
        if tab.nrows() != 1:
            raise ValueError("Weighting requires one polarization setup.")
        correlations = tab.getcell("CORR_TYPE", 0).tolist()
        if 9 not in correlations or 12 not in correlations:
            raise ValueError("Weighting requires XX and YY correlations.")
        parallel = [correlations.index(9), correlations.index(12)]
    if station_flags is not None and station_flags.shape != (len(ants), len(times)):
        raise ValueError("Station/time mask does not match the solutions.")
    mask = np.zeros((len(ants) + 1, len(times)), dtype=bool)
    if station_flags is not None:
        mask[:-1] = station_flags
    weights = np.zeros((len(ants), len(freqs), len(times)), dtype=float)
    boundaries = (times[:-1] + times[1:]) / 2
    total, additional = 0, 0
    with table(ms, readonly=True, ack=False) as tab:
        for start in range(0, tab.nrows(), 4096):
            count = min(4096, tab.nrows() - start)
            ti = np.searchsorted(boundaries, tab.getcol("TIME", start, count))
            if not np.allclose(times[ti], tab.getcol("TIME", start, count), rtol=0, atol=1e-5):
                raise ValueError("Weighting MS and H5 time grids must match.")
            a1, a2 = (tab.getcol(a, start, count) for a in ("ANTENNA1", "ANTENNA2"))
            raw = tab.getcol("WEIGHT_SPECTRUM", start, count)
            valid = (~tab.getcol("FLAG", start, count)
                     & ~tab.getcol("FLAG_ROW", start, count)[:, None, None]
                     & np.isfinite(raw) & (raw > 0) & (a1 != a2)[:, None, None])
            selected = mask[mapped[a1], ti] | mask[mapped[a2], ti]
            total += int(valid.sum())
            additional += int(valid[selected].sum())
            valid[selected] = False
            row_weight = np.where(valid[:, :, parallel], raw[:, :, parallel], 0).sum(axis=2)
            uvw = tab.getcol("UVW", start, count)
            uv = np.hypot(uvw[:, 0], uvw[:, 1])[:, None] * freqs[None, :] / 299792458.0
            row_weight = np.where(uv >= uvmin, row_weight, 0)
            for endpoint in (a1, a2):
                ai = mapped[endpoint]
                keep = ai >= 0
                np.add.at(weights, (ai[keep], slice(None), ti[keep]), row_weight[keep])
    return weights, additional / total if total else np.inf


def weighted_percentile90(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted inverse-CDF percentile; no usable weight cannot pass."""
    valid = ~np.isnan(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return np.inf
    order = np.argsort(values[valid])
    values, weights = values[valid][order], weights[valid][order]
    index = np.searchsorted(np.cumsum(weights), 0.9 * weights.sum(), side="left")
    return float(values[min(index, len(values) - 1)])


def make_phase_mask(scatter: np.ndarray, support: np.ndarray,
                    times: np.ndarray) -> np.ndarray:
    """Select one fixed mask: 45-degree floor, five MAD sigma, three bins."""
    mask = np.zeros(scatter.shape, dtype=bool)
    if len(times) < 3:
        return mask
    if np.any(np.diff(times) <= 0):
        raise ValueError("Expected increasing solution times.")
    step = np.median(np.diff(times))
    for ant in range(1, len(scatter)):  # Preserve the reference station.
        valid = (support[ant] >= 0.8) & np.isfinite(scatter[ant])
        if not valid.any():
            continue
        median = np.median(scatter[ant, valid])
        sigma = 1.4826 * np.median(np.abs(scatter[ant, valid] - median))
        bad = valid & (scatter[ant] > max(45.0, median + 5 * sigma))
        start = None
        for i in range(len(times) + 1):
            gap = 0 < i < len(times) and times[i] - times[i - 1] > 1.5 * step
            if start is not None and (i == len(times) or not bad[i] or gap):
                if i - start >= 3:
                    mask[ant, start:i] = True
                start = None
            if i < len(times) and bad[i] and start is None:
                start = i
    return mask


def apply_solution_flags(h5: str, mask: np.ndarray, ants: np.ndarray,
                         times: np.ndarray):
    """Zero only phase/amplitude weights in an independently copied H5."""
    with tables.open_file(h5, mode="r+") as handle:
        for name in ("phase000", "amplitude000"):
            if name not in handle.root.sol000._v_children:
                continue
            soltab = getattr(handle.root.sol000, name)
            if not np.array_equal(soltab.ant[:], ants) or not np.array_equal(soltab.time[:], times):
                raise ValueError("Phase and amplitude station/time axes must match.")
            axes = make_utf8(soltab.val.attrs["AXES"]).split(",")
            shape = [len(times) if a == "time" else len(ants) if a == "ant" else 1 for a in axes]
            selected = mask.T if axes.index("time") < axes.index("ant") else mask
            weights = soltab.weight[:]
            soltab.weight[:] = np.where(selected.reshape(shape), 0, weights)


def sigmoid(val: Union[float, np.ndarray],
            threshold: float = 0,
            sigma: float = 1.0,
            inverted: bool = False
            ) -> Union[float, np.ndarray]:
    """
    Apply sigmoid.

    Args:
        val: Input value or array.
        threshold: Midpoint (threshold) of the sigmoid in degrees.
        sigma: Controls the steepness of the sigmoid.
        inverted: If True, invert the sigmoid (monotonically decreasing).

    Returns:
        Sigmoid-transformed value(s).
    """
    sign = 1 if inverted else -1
    return 1 / (1 + np.exp(sign * (val - threshold) / sigma))


def parabola(x: Union[float, np.ndarray],
             p: Sequence[float] | None = None,
             a: float | None = None,
             b: float = 0.0,
             c: float = 0.0,
             ) -> Union[float, np.ndarray]:
    """
    Evaluate a quadratic function a*x^2 + b*x + c.

    Either provide coefficients as a sequence `p = (a, b, c)`
    or pass `a`, `b`, and `c` explicitly.

    Args:
        x: Input value(s).
        p: Sequence of coefficients [a, b, c].
        a: Quadratic coefficient (used if `p` is not given).
        b: Linear coefficient (default: 0.0).
        c: Constant term (default: 0.0).

    Returns:
        Evaluated parabola value(s).
    """
    if p is not None:
        a_, b_, c_ = p
    elif a is not None:
        a_, b_, c_ = a, b, c
    else:
        raise ValueError("Provide either p=(a, b, c) or at least a (with optional b, c).")

    return a_ * np.asarray(x) ** 2 + b_ * np.asarray(x) + c_


def get_chi(y: Union[float, np.ndarray],
            model_y: Union[float, np.ndarray]
            ) -> Union[float, np.ndarray]:
    """
    Compute wrapped residuals between observed and model values.

    The difference (y - model_y) is wrapped into the range [-π, π],
    ensuring residuals are bounded within this interval.

    Args:
        y: Observed value(s).
        model_y: Model-predicted value(s).

    Returns:
        Residuals wrapped to the interval [-π, π].
    """
    return normalise_phases(y - model_y)


def residuals(p: tuple[float, float, float],
              y: Union[float, np.ndarray],
              x: Union[float, np.ndarray]
              ) -> Union[float, np.ndarray]:
    """
    Get residuals between observed values and parabola model,
    wrapped into the range [-π, π].

    Args:
        p: Sequence of coefficients [a, b, c].
        y: Observed value(s).
        x: Input value(s).

    Returns:
        Residuals wrapped to [-π, π].
    """
    model_y = parabola(x=x, p=p)
    return get_chi(y, model_y)


def residuals_brute(a: float,
                    y: Union[float, np.ndarray],
                    x: Union[float, np.ndarray],
                    c: float = 0.0):
    """
    Get residuals for quadratic model with fixed constant term,
    wrapped into the range [-π, π].

    Args:
        a: Quadratic coefficient or array of coefficients.
        y: Observed value(s).
        x: Input value(s).
        c: Constant term.

    Returns:
        Sum of squared residuals for each coefficient in `a`.
    """
    model_y = parabola(x=x, a=a, c=c)
    chi = get_chi(y, model_y)
    return np.sum(chi**2, axis=1)


def subtract_parabola(phases: np.ndarray, multiplier: float = 1.0):
    """
    Subtract best-fit parabola from phase solutions.

    Args:
        phases: 2D array of phase values (time × interval).

    Returns:
        2D array of phases with parabola removed, wrapped to [-π, π].
    """
    sample_range = np.linspace(-5e-4,5e-4,512) * max(1.0, multiplier)
    new_phases = np.zeros(phases.shape)
    for idx, time_interval in enumerate(phases.T):
        p_0 = [0,0,0]

        if np.sum(~np.isnan(time_interval)) > 5:
            x = np.arange(-len(time_interval)//2,len(time_interval)//2)

            #Initial estimate of parameters
            p_0[2] = np.nanmean(time_interval[max(len(time_interval)//2-10, 0):len(time_interval)//2+10])
            chi2 = residuals_brute(sample_range[:,None], time_interval[None,~np.isnan(time_interval)], x[None,~np.isnan(time_interval)], p_0[2])
            p_0[0] = sample_range[np.argmin(chi2)]

            #Get proper fitted estimate
            p, cov = leastsq(residuals, p_0, args=(time_interval[~np.isnan(time_interval)], x[~np.isnan(time_interval)]))
            model_phases=p[0]*x**2 + p[1]*x + p[2]
            new_phases[:, idx] = time_interval - model_phases
        else:
            new_phases[:, idx] = time_interval
    norm_new_phases = normalise_phases(new_phases)

    return norm_new_phases


def calc_wraps(phase_solutions: np.ndarray,
               axes: list[str]
               ) -> float:
    """
    Calculate maximum number of phase wraps around 2pi from phase calibration solutions

    Args:
        phase_solutions: Phase calibration solutions
        axes: Axes names

    Returns: Number of phase wraps
    """

    # Get diffs
    phase_freq_diff = normalise_phases(np.diff(phase_solutions, axis=axes.index('freq')))

    # Get phase wrapping score
    freqsum = np.nansum(phase_freq_diff / (2*np.pi), axis=axes.index('freq'))
    wrap_count = np.max(np.abs(freqsum))

    return wrap_count


def normalise_phases(phase_sols: np.ndarray) -> np.ndarray:
    """
    Normalise phase solutions to the interval [-π, π].

    This ensures all phase values are wrapped into a consistent range,
    which is useful for comparing or averaging phases.

    Args:
        phase_sols: Array of phase solutions in radians.

    Returns:
        Array of phase solutions wrapped to [-π, π].
    """
    return (phase_sols - np.pi) % (2 * np.pi) - np.pi


def get_phase_noise_statistic(phase_sols: np.ndarray,
                              idx_ant: int,
                              freqs: np.ndarray,
                              wrap_count: float,
                              phase_weights: np.ndarray | None = None,
                              return_noise: bool = False,
                              ):
    """
    Get phase noise statistic, which is the 90th percentile on the circular standard deviation of the phase solutions,
    after taking the 10% margin of the phase solutions, and subtracting parabola from the phase solutions.

    Args:
        phase_sols: Station referenced phase solutions
        idx_ant: Antenna index
        freqs: Frequency axis
        phase_weights: Optional station/frequency/time MS sensitivity weights.
        return_noise: Also return the scatter of each time interval in degrees.

    Returns: Phase score
    """

    phase_sols_sub = phase_sols[idx_ant]
    phase_freq_diff_sub = normalise_phases(phase_sols_sub[:-1, :] - phase_sols_sub[1:, :])

    # Slice with 10% margin on eiter side of the frequency band to discard for de-sloping
    slice_size = phase_freq_diff_sub.shape[0]//10

    delay_slope = np.nanmean(phase_freq_diff_sub[slice_size:-(slice_size+1)], axis=0)
    deslopvals = np.arange(-len(freqs) // 2, len(freqs) // 2)[:, None] * delay_slope[None, :]
    phases_desloped = normalise_phases(phase_sols_sub + deslopvals)
    phases_desloped = normalise_phases(phases_desloped - np.nanmean(phases_desloped[slice_size:-(slice_size+1)], axis=0))
    phases_desloped = subtract_parabola(phases_desloped, multiplier=wrap_count)
    phases_desloped = normalise_phases(phases_desloped - np.nanmean(phases_desloped[slice_size:-(slice_size+1)], axis=0))

    if phase_weights is None:
        phase_noise = circstd(phases_desloped, axis=0, nan_policy='omit')
        phase_score = np.nanpercentile(phase_noise, 90) / np.pi * 180
    else:
        weights = phase_weights[idx_ant]
        weights = np.where(np.isfinite(phases_desloped) & np.isfinite(weights) & (weights > 0), weights, 0)
        time_weights = weights.sum(axis=0)
        angles = np.where(np.isfinite(phases_desloped), phases_desloped, 0)
        vector = np.sum(weights * np.exp(1j * angles), axis=0)
        resultant = np.full(time_weights.shape, np.nan)
        np.divide(np.abs(vector), time_weights, out=resultant, where=time_weights > 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            phase_noise = np.sqrt(-2 * np.log(np.clip(resultant, 0, 1)))
        phase_score = np.rad2deg(weighted_percentile90(phase_noise, time_weights))

    return (phase_score, np.rad2deg(phase_noise)) if return_noise else phase_score


def get_phase_score(h5: str, weighting_ms: str | None = None,
                    use_ms_weighting: bool = True, weight_uvmin: float = 40000.0,
                    phase_weights: np.ndarray | None = None,
                    return_details: bool = False):
    """
    Get phase score, which is based on the circular standard deviation and wrap count

    Args:
        h5: h5parm solution file
        weighting_ms: Optional matching MS for input-sensitivity weighting.
        use_ms_weighting: Use MS weights when supplied; otherwise retain current scoring.
        weight_uvmin: Cross-baseline cutoff in wavelengths; match the calibration solve.
        phase_weights: Optional precomputed MS weights after station/time exclusions.
        return_details: Also return the per-time scatter and support for flagging.

    Returns: phase score, max wrap count
    """

    with tables.open_file(h5) as H:
        phase_table = H.root.sol000.phase000
        freqs = phase_table.freq[:]
        times = phase_table.time[:]
        ants = phase_table.ant[:]
        use_ms_weighting = use_ms_weighting and (weighting_ms is not None or phase_weights is not None)
        values, weights = phase_table.val[:], phase_table.weight[:]
        usable = (weights > 0) & np.isfinite(weights) if use_ms_weighting else weights > 0
        phase_sols = np.where(usable, values if use_ms_weighting else values * weights, np.nan)
        axes = make_utf8(phase_table.val.attrs["AXES"]).split(',')

        # Remove polarisation and direction axis
        if 'pol' in axes:
            phase_sols = np.take(phase_sols, 0, axis=axes.index('pol'))
        if 'dir' in axes:
            phase_sols = np.take(phase_sols, 0, axis=axes.index('dir'))

    # Reference solutions to first station
    ref_phase = np.take(phase_sols, [0], axis=axes.index('ant'))
    phase_sols -= ref_phase

    # Get wraps
    wrap_count = calc_wraps(phase_sols, axes)

    # De-slope
    phase_sols = reorderAxes(phase_sols, ['ant', 'freq', 'time'],
                                  [a for a in axes if a not in ['pol', 'dir']])

    if use_ms_weighting and phase_weights is None:
        phase_weights, _ = get_ms_phase_weights(weighting_ms, times, freqs, ants, weight_uvmin)
    if not use_ms_weighting:
        phase_weights = None

    # Get 90-percentile scores
    statistics = [get_phase_noise_statistic(phase_sols, idx_ant, freqs, wrap_count,
                                           phase_weights, return_details)
                  for idx_ant, _ in enumerate(ants)]
    perc90_scores = [s[0] for s in statistics] if return_details else statistics
    phase_score = sigmoid(max(perc90_scores), 45, 10, True) if np.all(np.isfinite(perc90_scores)) else 0.0

    if return_details:
        support = np.isfinite(phase_sols)
        if phase_weights is not None:
            support &= np.isfinite(phase_weights) & (phase_weights > 0)
        return phase_score, wrap_count, dict(scatter=np.asarray([s[1] for s in statistics]),
                                            support=support.mean(axis=1),
                                            times=times, ants=ants, freqs=freqs)
    return phase_score, wrap_count


def get_amp_score(h5: str) -> float:
    """
    Get amplitude score, which is based on the number of amplitude values above 1.5 and below 0.67, multiplied with
    (1-std), which is the standard deviation of the amplitude solutions.

    Args:
        h5: h5parm solution file

    Returns: Amplitude score between 0 and 1
    """

    with tables.open_file(h5) as H:
        amplitude_table = H.root.sol000.amplitude000
        axes = make_utf8(amplitude_table.val.attrs["AXES"]).split(',')

        # Remove polarisation axis and only select amplitude corrections where weights!=0
        if 'pol' in axes:
            weights = np.take(amplitude_table.weight[:], [0], axis=axes.index('pol'))!=0
            amplitude_sols = np.take(amplitude_table.val[:], [0], axis=axes.index('pol'))[weights]
        else:
            weights = amplitude_table.weight[:]!=0
            amplitude_sols = amplitude_table.val[:][weights]

    amplitude_std = np.std(amplitude_sols)

    # Score for large amplitude offsets
    amplitude_offset_score = 1 - len(amplitude_sols[(amplitude_sols > 1.5) | (amplitude_sols < 0.67)])/amplitude_sols.size

    # Final score
    amplitude_score = amplitude_offset_score * (1-amplitude_std)

    return amplitude_score


def get_validation_scores(solutions: list[str], weighting_mses: list[str] | None = None,
                          use_ms_weighting: bool = True, weight_uvmin: float = 40000.0,
                          flag_solutions: bool = False, output_dir: str | None = None):
    """
    Get validation scores from calibration solutions, based on the phase noise and amplitude variation, and write
    this to a CSV.

    Args:
        solutions: input h5parms
        weighting_mses: Matching read-only calibrator MSes, identified by source ID.
        use_ms_weighting: Select the MS-weighted score when MSes are supplied.
        weight_uvmin: Baseline cutoff in wavelengths for sensitivity weighting.
        flag_solutions: Try one bounded H5-only mask when the selected phase score fails.
        output_dir: Copy solutions here, preserving their basenames and source files.
    """

    ms_by_source = {}
    for ms in weighting_mses or []:
        source = parse_source_id(ms)
        if source in ms_by_source:
            raise ValueError(f"Multiple weighting MSes for {source}.")
        ms_by_source[source] = ms
    if weighting_mses is not None:
        for sol in solutions:
            if parse_source_id(sol) not in ms_by_source:
                raise ValueError(f"No matching weighting MS for {sol}.")
    if flag_solutions and not ms_by_source:
        raise ValueError("Solution flagging requires an MS to check the overall visibility cap.")
    if flag_solutions and output_dir is None:
        output_dir = "validated_solutions"
    if len({Path(sol).name for sol in solutions}) != len(solutions):
        raise ValueError("Solution output basenames must be unique.")
    if output_dir is not None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    diagnostics = weighting_mses is not None or flag_solutions
    selected_files = []
    with open('validation_solutions.csv', 'w') as csvfile:
        fieldnames = ['source_id', 'amp_score', 'phase_score', 'wrap_count']
        if diagnostics:
            fieldnames += ['phase_score_current', 'phase_score_ms_weighted',
                           'phase_score_current_before_flagging', 'phase_score_ms_weighted_before_flagging',
                           'amp_score_before_flagging', 'proposed_station_fraction',
                           'proposed_visibility_fraction', 'flagging_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for sol in solutions:
            id = parse_source_id(sol)
            if not id:
                id = sol.replace('.h5','')

            if output_dir is not None:
                target = Path(output_dir) / Path(sol).name
                if target.exists() or target.resolve() == Path(sol).resolve():
                    raise ValueError(f"Refusing to overwrite solution file {target}.")
                shutil.copy2(sol, target)
                target.chmod(target.stat().st_mode | 0o200)
                sol = str(target)
            selected_files.append(sol)
            ms = ms_by_source.get(id)
            weighted = use_ms_weighting and ms is not None

            def phase_scores(ms_weights=None, details=False):
                current = get_phase_score(sol, use_ms_weighting=False,
                                          return_details=details and not weighted)
                ms_score = (get_phase_score(sol, ms, True, weight_uvmin,
                                           phase_weights=ms_weights, return_details=details)
                            if weighted else None)
                return current, ms_score, ms_score if weighted else current

            # Amplitude tables do not always exist
            try:
                amplitude_score = get_amp_score(sol)
            except tables.NoSuchNodeError:
                amplitude_score = None

            if amplitude_score is not None and not np.isfinite(amplitude_score):
                amplitude_score = 0.0
            before_amp = amplitude_score
            current, ms_score, selected = phase_scores(details=flag_solutions)
            before_current, before_weighted = current[0], ms_score[0] if weighted else None
            status = 'not_requested'
            station_fraction, visibility_fraction = 0.0, 0.0
            if flag_solutions:
                status = 'phase_passed' if selected[0] >= PHASE_THRESHOLD else 'no_outliers'
                if selected[0] < PHASE_THRESHOLD:
                    details = selected[2]
                    mask = make_phase_mask(details['scatter'], details['support'], details['times'])
                    station_fraction = float(mask.mean(axis=1).max())
                    if station_fraction > MAX_STATION_FLAG_FRACTION:
                        status = 'station_cap_exceeded'
                    elif mask.any():
                        adjusted_weights, visibility_fraction = get_ms_phase_weights(
                            ms, details['times'], details['freqs'], details['ants'], weight_uvmin, mask)
                        if visibility_fraction > MAX_VISIBILITY_FLAG_FRACTION:
                            status = 'visibility_cap_exceeded'
                        else:
                            apply_solution_flags(sol, mask, details['ants'], details['times'])
                            current, ms_score, selected = phase_scores(adjusted_weights)
                            if amplitude_score is not None:
                                amplitude_score = get_amp_score(sol)
                                if not np.isfinite(amplitude_score):
                                    amplitude_score = 0.0
                            status = 'applied'
            phase_score, wrap_count = selected[:2]

            scores = {
                'source_id': id,
                'amp_score': amplitude_score,
                'phase_score': phase_score,
                'wrap_count': wrap_count,
            }
            if diagnostics:
                scores.update(phase_score_current=current[0],
                              phase_score_ms_weighted=ms_score[0] if weighted else None,
                              phase_score_current_before_flagging=before_current,
                              phase_score_ms_weighted_before_flagging=before_weighted,
                              amp_score_before_flagging=before_amp,
                              proposed_station_fraction=station_fraction,
                              proposed_visibility_fraction=visibility_fraction,
                              flagging_status=status)

            pprint(scores)

            writer.writerow(scores)

    return selected_files


def sol_quality(csv_table: str):
    """
    Make solution quality acceptance column based on a combination of calibration solution quality criteria.
    The new column has a boolean to accept calibration solutions (True) or not (False).

    The thresholds for the phase and amplitude scores are based on manual tests with data from ELAIS-N1 and various
    delay calibrators from LoTSS-HR, during the VLBI busy week August 2025.

    Args:
        csv_table: CSV with image-based scores

    """

    df = pd.read_csv(csv_table)
    df['comment'] = ''
    df['accept_solutions'] = True

    # 'bad' qualifications
    mask = ((df['amp_score'] < AMPLITUDE_THRESHOLD) | (df['phase_score'] < PHASE_THRESHOLD)
            | ~np.isfinite(df['phase_score']))

    # Flag sources with accept_solutions=False if scores below threshold
    df.loc[mask, 'accept_solutions'] = False

    df.to_csv(csv_table, index=False)


def parse_args() -> Namespace:
    """
    Command line argument parser

    :return: parsed arguments
    """

    parser = ArgumentParser("Get validation scores for calibration solutions.")
    parser.add_argument('h5parms', nargs='+', help='h5parm calibration solution files with amplitude '
                        'and phase solutions.', default=None)
    parser.add_argument('--weight-ms', dest='weighting_mses', action='append',
                        help='Matching calibrator MS; repeat once per source. Enables MS weighting by default.')
    parser.add_argument('--no-ms-weighting', dest='use_ms_weighting', action='store_false',
                        help='Use the current phase score instead of MS-sensitivity weighting.')
    parser.add_argument('--weight-uvmin', type=float, default=40000.0,
                        help='Weighting UV minimum in wavelengths; match the solve (default: 40000).')
    parser.add_argument('--flag-solutions', action='store_true',
                        help='Flag one H5 copy only when phase quality fails; enforce station/visibility caps.')
    parser.add_argument('--output-dir', help='Directory for independently copied output H5s.')

    return parser.parse_args()


def main():
    args = parse_args()
    get_validation_scores(args.h5parms, args.weighting_mses, args.use_ms_weighting,
                          args.weight_uvmin, args.flag_solutions, args.output_dir)
    sol_quality("validation_solutions.csv")


if __name__ == '__main__':
    main()
