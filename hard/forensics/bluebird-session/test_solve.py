"""Tests for the Bluebird Session solver.

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


class BluebirdSessionTests(unittest.TestCase):
    def test_reproduces_flag(self):
        flag = solve.extract_flag(solve.DEFAULT_INPUT)
        self.assertEqual(flag, "NFX{MizoreCanFly2077!@}")

    def test_keyring_metadata_and_label(self):
        data = solve.DEFAULT_INPUT.read_bytes()
        label, secret = solve.parse_and_decrypt_keyring(data, solve.PASSWORD)
        self.assertEqual(label, "Mizore Promise Note")
        self.assertIn("For Nozomi,", secret)
        self.assertIn("MizoreCanFly2077!@", secret)

    def test_rejects_wrong_password(self):
        data = solve.DEFAULT_INPUT.read_bytes()
        with self.assertRaises(ValueError):
            solve.parse_and_decrypt_keyring(data, "WrongPassword123!")


if __name__ == "__main__":
    unittest.main()
