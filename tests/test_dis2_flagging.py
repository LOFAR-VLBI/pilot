"""Exercise DIS2 conversion/flagging orchestration without a radio-data fixture.

The real converter script runs against small command-line stubs. Numerical
LoSoTo behaviour is covered separately by the native field-data validation.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / "scripts" / "convert_DIS2_to_h5parm.sh"
PARSET = ROOT / "pipeline_config_files" / "losoto_dis2_flagging.parset"
TOOL = ROOT / "steps" / "gatherdis2.cwl"

STUB = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

program = Path(sys.argv[0]).name
arguments = sys.argv[1:]
with open(os.environ["FAKE_DIS2_EVENTS"], "a") as events:
    events.write(json.dumps({"program": program, "arguments": arguments}) + "\n")
if os.environ.get("FAKE_DIS2_FAIL_PROGRAM") == program:
    print("simulated process failure", file=sys.stderr)
    sys.exit(23)
if program == "killMS2H5parm.py":
    output = next(argument for argument in arguments if argument.endswith(".h5"))
    Path(output).write_text("converted\n")
elif program == "h5_merger":
    output = arguments[arguments.index("--h5_out") + 1]
    Path(output).write_text("merged\n")
elif program == "losoto":
    mode = os.environ.get("FAKE_DIS2_LOSOTO_MODE", "success")
    h5, parset = arguments[-2:]
    if not Path(h5).is_file() or not Path(parset).is_file():
        print("ERROR: missing LoSoTo input")
        sys.exit(1)
    if mode == "incomplete":
        print("ERROR: Step 'flagamp' incomplete. Try to continue anyway.")
        print("Step 'flagphase' completed successfully.")
    elif mode == "missing_phase":
        print("Step 'flagamp' completed successfully.")
    else:
        print("Step 'flagamp' completed successfully.")
        print("Step 'flagphase' completed successfully.")
        if mode == "error_despite_markers":
            print("ERROR: an operation failed despite the success messages")
        elif mode == "traceback_despite_markers":
            print("Traceback (most recent call last):")
        else:
            if mode == "benign_error_filename":
                print("INFO: reading /tmp/incomplete/ERROR.parset")
            with open(h5, "a") as output:
                output.write("flagged\n")
'''


class Dis2FlaggingTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dis2 flagging ")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.binary = self.directory / "bin"
        self.binary.mkdir()
        for name in ("killMS2H5parm.py", "h5_merger", "losoto"):
            executable = self.binary / name
            executable.write_text(STUB)
            executable.chmod(0o755)
        self.solutions = self.directory / "source solutions"
        self.solutions.mkdir()
        self.reference_ms = self.directory / "reference station list.ms"
        self.reference_ms.mkdir()
        self.parset = self.directory / "flagging recipe.parset"
        self.parset.write_text("[flagamp]\noperation = FLAG\n[flagphase]\noperation = FLAG\n")
        self.work = self.directory / "work"
        self.work.mkdir()
        self.events_path = self.directory / "events.jsonl"
        self.environment = os.environ.copy()
        self.environment["PATH"] = os.pathsep.join(
            [str(self.binary), str(CONVERTER.parent), os.environ["PATH"]])
        self.environment["FAKE_DIS2_EVENTS"] = str(self.events_path)

    def add_solution(self, observation):
        directory = self.solutions / observation
        directory.mkdir()
        path = directory / "killMS.DIS2_full.sols.npz"
        path.write_bytes(b"unmodified native solution fixture")
        return path

    def events(self):
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text().splitlines()]

    def run_converter(self):
        return subprocess.run(
            ["bash", str(CONVERTER), str(self.solutions), str(self.reference_ms), str(self.parset)],
            cwd=self.work, env=self.environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def test_converts_then_merges_then_flags_with_spaces_in_paths(self):
        sources = [self.add_solution("L100_120MHz.ms"), self.add_solution("L100_122MHz.ms")]
        result = self.run_converter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        events = self.events()
        self.assertEqual([event["program"] for event in events],
                         ["killMS2H5parm.py", "killMS2H5parm.py", "h5_merger", "losoto"])
        self.assertEqual({event["arguments"][-1] for event in events[:2]},
                         {str(path) for path in sources})
        merger = events[2]["arguments"]
        self.assertEqual(merger[merger.index("--ms") + 1], str(self.reference_ms))
        self.assertEqual(events[-1]["arguments"], ["-v", "DIS2_full.h5", str(self.parset)])
        self.assertEqual((self.work / "DIS2_full.h5").read_text(), "merged\nflagged\n")

    def test_only_current_converted_files_are_merged(self):
        self.add_solution("L100_120MHz.ms")
        (self.work / "DIS2_unrelated.h5").write_text("not an input to this conversion")
        result = self.run_converter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        converted = next(event["arguments"] for event in self.events()
                         if event["program"] == "h5_merger")
        selected = converted[converted.index("--h5_tables") + 1:converted.index("--h5_out")]
        self.assertEqual(selected, ["DIS2_00.h5"])

    def test_no_native_solutions_fails_before_external_commands(self):
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events(), [])

    def test_missing_parset_fails_before_conversion(self):
        self.add_solution("L100_120MHz.ms")
        self.parset.unlink()
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events(), [])

    def test_conversion_failure_never_merges_or_flags(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_FAIL_PROGRAM"] = "killMS2H5parm.py"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([event["program"] for event in self.events()], ["killMS2H5parm.py"])

    def test_merge_failure_never_runs_losoto(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_FAIL_PROGRAM"] = "h5_merger"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([event["program"] for event in self.events()],
                         ["killMS2H5parm.py", "h5_merger"])

    def test_nonzero_losoto_exit_fails_conversion(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_FAIL_PROGRAM"] = "losoto"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)

    def test_zero_exit_with_incomplete_losoto_step_is_rejected(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_LOSOTO_MODE"] = "incomplete"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)

    def test_zero_exit_without_both_successful_steps_is_rejected(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_LOSOTO_MODE"] = "missing_phase"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)

    def test_success_markers_do_not_hide_losoto_error(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_LOSOTO_MODE"] = "error_despite_markers"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)

    def test_success_markers_do_not_hide_worker_traceback(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_LOSOTO_MODE"] = "traceback_despite_markers"
        result = self.run_converter()
        self.assertNotEqual(result.returncode, 0)

    def test_error_words_in_a_filename_are_not_operation_failures(self):
        self.add_solution("L100_120MHz.ms")
        self.environment["FAKE_DIS2_LOSOTO_MODE"] = "benign_error_filename"
        result = self.run_converter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(importlib.util.find_spec("cwltool"), "cwltool is an optional test dependency")
    def test_cwl_stages_default_recipe_without_a_container(self):
        self.add_solution("L100_120MHz.ms")
        job = self.directory / "job.json"
        job.write_text(json.dumps({
            "msin": {"class": "Directory", "path": str(self.reference_ms)},
            "ddf_solsdir": {"class": "Directory", "path": str(self.solutions)},
        }))
        output = self.directory / "cwl-output"
        result = subprocess.run(
            [sys.executable, "-c", "from cwltool.main import main; raise SystemExit(main())",
             "--no-container", "--quiet", "--relax-path-checks",
             "--preserve-environment", "FAKE_DIS2_EVENTS", "--outdir", str(output),
             str(TOOL), str(job)],
            cwd=self.directory, env=self.environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.strip(), result.stderr)
        outputs = json.loads(result.stdout)
        reported_h5 = outputs["dis2_h5parm"]
        location = urlparse(reported_h5["location"])
        self.assertEqual(location.scheme, "file", reported_h5)
        flagged_h5 = Path(unquote(location.path)).resolve()
        self.assertIn(output.resolve(), flagged_h5.parents, reported_h5)
        self.assertEqual(flagged_h5.read_text(), "merged\nflagged\n")
        losoto = next(event for event in self.events() if event["program"] == "losoto")
        self.assertEqual(Path(losoto["arguments"][-1]).name, PARSET.name)
        files = outputs["logfile"]
        self.assertIn("losoto-dis2.log", {entry["basename"] for entry in files})


if __name__ == "__main__":
    unittest.main()
