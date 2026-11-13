#!/usr/bin/env python3
"""Unit test untuk solve.py Medium RC4."""
import unittest
from pathlib import Path

from solve import solve, rc4

BIN = Path(__file__).with_name("medium_rc4")
EXPECTED = "NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}"


class TestMediumRC4(unittest.TestCase):
    def test_flag(self):
        self.assertEqual(solve(BIN), EXPECTED)

    def test_rc4_simetris(self):
        key = b"n0t_s3cur3_k3y_2026"
        msg = b"NFX{roundtrip}"
        self.assertEqual(rc4(key, rc4(key, msg)), msg)


if __name__ == "__main__":
    unittest.main()
