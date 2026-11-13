#!/usr/bin/env python3
"""Tests for RSA Coppersmith cihuy solver."""

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
    HAVE_DEPS = getattr(solve_mod, "fmpz", None) is not None
except Exception:
    HAVE_DEPS = False


class TestRSACoppersmithCihuy(unittest.TestCase):
    def test_assets_exist_and_hash(self):
        chall_path = ASSETS / "chall.py"
        self.assertTrue(chall_path.is_file(), "assets/chall.py harus ada")

        chall_sha256 = hashlib.sha256(chall_path.read_bytes()).hexdigest()
        self.assertEqual(
            chall_sha256,
            "be1635552e0b4fd1d83259896b5dee6498d7bbd944c82d0292c1b0fc32d33cf1",
        )

    def test_solve(self):
        if not HAVE_DEPS:
            self.skipTest(
                "Pustaka python-flint belum terpasang di environment Python ini."
            )

        flag = solve_mod.solve(str(ASSETS / "chall.py"))
        expected_flag = "NFXCTF{C0pp3rsm1th_p4rt14l_k3y_3xp0sur3_9617eda9}"
        self.assertEqual(flag, expected_flag)


if __name__ == "__main__":
    unittest.main()
