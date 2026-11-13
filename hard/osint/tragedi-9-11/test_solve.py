"""Unit test untuk solver Tragedi 9/11 OSINT."""

import hashlib
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve_mod)

EXPECTED_FLAG = "NFX{OS1NT_DU4R_D34_D0R}"


class TestTragedi911(unittest.TestCase):
    def test_patch_exists_and_hash(self):
        self.assertTrue(solve_mod.PATCH_FILE.exists(), "Berkas commit_df34505.patch harus tersedia.")
        digest = hashlib.sha256(solve_mod.PATCH_FILE.read_bytes()).hexdigest()
        self.assertEqual(digest, solve_mod.EXPECTED_SHA256, "Hash SHA256 patch tidak cocok.")

    def test_solve_reproduces_flag(self):
        flag = solve_mod.solve(online=False)
        self.assertEqual(flag, EXPECTED_FLAG, "Flag hasil ekstraksi tidak cocok.")
        self.assertTrue(flag.startswith("NFX{"))
        self.assertTrue(flag.endswith("}"))


if __name__ == "__main__":
    unittest.main()
