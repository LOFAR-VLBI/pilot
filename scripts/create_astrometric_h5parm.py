#!/usr/bin/env python

from astropy import constants
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from losoto.h5parm import h5parm
from pathlib import Path

import argparse
import astropy.units as u
import casacore.tables as ct
import numpy as np


class MSAstrometryCorrector:
    def __init__(self, ms):
        self.ms = ms.rstrip("/")
        self.phase_centre = None
        self.l = None
        self.m = None
        self.n = None
        self.new_uvw = None

    def get_phase_centre(self) -> SkyCoord:
        """Get the phase centre from the Measurement Set.

        Returns:
            phase centre as a SkyCoord.
        """
        with ct.table(self.ms + "::FIELD", ack=False, readonly=True) as table:
            pc = table.getcol("PHASE_DIR").squeeze()
            pc_coord = SkyCoord(pc[0], pc[1], unit="rad")
            self.phase_centre = pc_coord
            return pc_coord

    def calculate_lmn(self, new_coord: SkyCoord) -> tuple[float, float, float]:
        """Calculates the (l, m, n) direction vector for the new position.

        Args:
            new_coord: position that the data will be shifted towards.

        Returns:
            (l, m, n) tuple representing the new direction vector.
        """
        l = np.cos(new_coord.dec.rad) * np.sin(
            new_coord.ra.rad - self.phase_centre.ra.rad
        )
        m = np.sin(new_coord.dec.rad) * np.cos(self.phase_centre.dec.rad) - np.cos(
            new_coord.dec.rad
        ) * np.sin(self.phase_centre.dec.rad) * np.cos(
            new_coord.ra.rad - self.phase_centre.ra.rad
        )
        n = np.sqrt(1 - l**2 - m**2)
        print("Derived new direction vector:")
        print(f"{l=:.9f}, {m=:.9f}, {n=:.9f}")
        self.l = l
        self.m = m
        self.n = n
        return (l, m, n)

    def calculate_new_station_uvw(self, new_coord: SkyCoord):
        """Calculates the UVW coordinates corresponding to the position of the source.
        that is shifted towards.

        Args:
            new_coord (SkyCoord): position of the astrometric source position to shift towards.

        Returns:
            uvw (ndarray): array of (Nt, Nant, 3) with the new UVW coordinates in metres.
        """
        ms_times = ct.taql(f"SELECT DISTINCT TIME FROM {self.ms}").getcol("TIME")
        times = Time(ms_times / 86400.0, format="mjd", scale="utc")
        with ct.table(self.ms + "::ANTENNA", ack=False, readonly=True) as tab:
            xyz = tab.getcol("POSITION")
            names = tab.getcol("NAME")
        ra = new_coord.icrs.ra.rad
        dec = new_coord.icrs.dec.rad

        # unit vectors: east (u), north (v), towards source (w), in GCRS axes
        e_u = np.array([-np.sin(ra), np.cos(ra), 0.0])
        e_v = np.array(
            [-np.sin(dec) * np.cos(ra), -np.sin(dec) * np.sin(ra), np.cos(dec)]
        )
        e_w = np.array(
            [np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)]
        )
        R = np.vstack([e_u, e_v, e_w])  # (3, 3)

        uvw = np.empty((len(times), len(xyz), 3))
        for k, (x, y, z) in enumerate(xyz):
            print(f"Calculating new UVW for {names[k]}")
            loc = EarthLocation.from_geocentric(x * u.m, y * u.m, z * u.m)
            pos, _ = loc.get_gcrs_posvel(times)  # geocentric, GCRS axes
            p = np.stack(
                [pos.x.to_value(u.m), pos.y.to_value(u.m), pos.z.to_value(u.m)], axis=-1
            )  # (Nt, 3)
            uvw[:, k, :] = p @ R.T
        self.new_uvw = uvw
        return uvw

    def calculate_delays(self):
        """Calculate delays for each antenna, for each time step to achieve the desired
        positional shift for the source."""
        # (time, ant, 3)
        self.delays = (
            self.new_uvw[:, :, 0] * self.l
            + self.new_uvw[:, :, 1] * self.m
            + self.new_uvw[:, :, 2] * (self.n - 1)
        ) / constants.c.value

    def write_astrometric_h5parm(
        self,
        h5file,
        solset="sol000",
        soltab="clock000",
        overwrite=True,
    ):
        """Write the astrometric corrections to an h5parm.

        Args:
            h5file (str): name of the h5parm file.
            solset (str): name of the solset to store the correction in.
            soltab (str): name of the soltab to store the correction in.
            overwrite (bool): if the soltab exists, remove it and create a fresh one.

        Raises:
            RuntimeError: if the soltab exists and overwrite is False.
        """
        times = ct.taql(f"SELECT DISTINCT TIME FROM {self.ms}").getcol("TIME")

        with ct.table(self.ms + "::ANTENNA", ack=False, readonly=True) as tab:
            xyz = tab.getcol("POSITION")
            names = tab.getcol("NAME")
        assert self.delays.shape == (len(times), len(names)), self.delays.shape

        h5 = h5parm(h5file, readonly=False)
        ss = h5.makeSolset(solset)
        ss.obj.antenna.append(list(zip(names, np.asarray(xyz, dtype="f4"))))
        ss.obj.source.append(
            [("pointing", [self.phase_centre.ra.rad, self.phase_centre.dec.rad])]
        )
        if solset in ss.getSoltabNames():
            if not overwrite:
                raise RuntimeError(f"solset {solset} already exists")
            st = ss.getSoltab(soltab)
            st.delete()
        ss.makeSoltab(
            soltype="clock",
            soltabName=soltab,
            axesNames=["time", "ant"],
            axesVals=[times, np.array(names)],
            vals=self.delays,
            weights=np.ones_like(self.delays),
        )
        h5.close()


def encode_astrometric_correction(
    ms: str, delta_ra: float, delta_dec: float, h5name: str
):
    """Encodes an positional shift for right ascension and declination as a per-station
    clock correction (i.e. delays) in an h5parm that can be applied with DP3.

    Args:
        ms (str): the Measurement Set for which the correction will be calculated.
        delta_ra: the offset in right ascension in degrees.
        delta_dec: the offset in decliation in degrees.
    """
    corrector = MSAstrometryCorrector(ms)
    pc = corrector.get_phase_centre()
    pc_new = SkyCoord(pc.ra.deg + delta_ra, pc.dec.deg + delta_dec, unit="deg")
    print(
        f"Separation between current phase centre and target: {pc.separation(pc_new).to('arcsec'):.3f}"
    )
    corrector.calculate_lmn(pc_new)
    corrector.calculate_new_station_uvw(pc_new)
    corrector.calculate_delays()
    corrector.write_astrometric_h5parm(h5name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ms",
        type=Path,
        required=True,
        help="MeasurementSet from which the phase centre and antenna positions will be taken.",
    )
    parser.add_argument(
        "--delta-ra",
        type=float,
        required=False,
        help="Right ascension shift in degrees.",
    )
    parser.add_argument(
        "--delta-dec",
        type=float,
        required=False,
        help="Declination shift in degrees.",
    )
    args = parser.parse_args()
    encode_astrometric_correction(
        args.ms,
        args.delta_ra,
        args.delta_dec,
        args.ms.with_suffix(".astrometry.h5").name,
    )


if __name__ == "__main__":
    main()
