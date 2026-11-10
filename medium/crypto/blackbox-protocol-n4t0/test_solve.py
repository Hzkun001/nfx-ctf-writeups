"""Tests for the Black Box Protocol N4T0 solver.

Run from this folder:
    python3 -m unittest -v
"""

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve)


class BlackBoxProtocolTests(unittest.TestCase):
    def test_reproduces_flag(self):
        shared, sheet = solve.load_workbook(solve.DEFAULT_INPUT)
        flag, a, b, c = solve.decode(shared, sheet)
        self.assertEqual(a, "N4T0PH0N3T1C1N1")
        self.assertEqual(b, "C0mbO_H3X_")
        self.assertEqual(c, "fl0At_b4r4ng")
        self.assertEqual(flag, "NFX{N4T0_PH0N3T1C_1N1_C0mbO_H3X_fl0At_b4r4ng}")

    def test_rejects_wrong_input(self):
        bad = HERE / "assets" / "flight_recovery_manifest.xlsx"
        data = bytearray(bad.read_bytes())
        data[-1] ^= 0xFF
        tmp = HERE / "_tampered.xlsx"
        tmp.write_bytes(bytes(data))
        try:
            with self.assertRaises(ValueError):
                solve.load_workbook(tmp)
        finally:
            tmp.unlink()

    def test_mask_matches_supplied_format(self):
        shared, sheet = solve.load_workbook(solve.DEFAULT_INPUT)
        flag, *_ = solve.decode(shared, sheet)
        mask = "".join(
            "0" if ch.isdigit() else "X" if ch.isupper() else "x" if ch.islower() else ch
            for ch in flag
        )
        self.assertEqual(mask, solve.EXPECTED_MASK)


if __name__ == "__main__":
    unittest.main()
