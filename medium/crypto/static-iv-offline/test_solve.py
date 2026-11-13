#!/usr/bin/env python3
"""Tests for Static IV Offline solver."""

import hashlib
import importlib.util
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve_mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(solve_mod)
    HAVE_DEPS = True
except ModuleNotFoundError:
    HAVE_DEPS = False


class TestStaticIVOffline(unittest.TestCase):
    def test_assets_exist_and_hash(self):
        chall_path = ASSETS / "challenge.py"
        output_path = ASSETS / "output.txt"
        self.assertTrue(chall_path.is_file(), "assets/challenge.py harus ada")
        self.assertTrue(output_path.is_file(), "assets/output.txt harus ada")

        chall_sha256 = hashlib.sha256(chall_path.read_bytes()).hexdigest()
        output_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()

        self.assertEqual(
            chall_sha256,
            "9db56543f1a9e477b346b4f17c648d3617f959ecae2d04a15b3e95e7d870ae00",
        )
        self.assertEqual(
            output_sha256,
            "9b02a67da90ec0ae31f8f7a183a95f9561bc5131c453429a6dc1f002a66eb970",
        )

    def test_solve(self):
        if not HAVE_DEPS:
            self.skipTest("Dependensi pycryptodome belum terpasang.")

        flag = solve_mod.solve(str(ASSETS / "output.txt"))
        expected_flag = "NXCTF{cbc_1v_r3u53_l34k5_k3y5tr34m_b0fbd4d35f80}"
        self.assertEqual(flag, expected_flag)


if __name__ == "__main__":
    unittest.main()
