"""Unit test untuk solver Wujud Aseli Atmin."""

import hashlib
import unittest
from pathlib import Path

from solve import solve, INPUT_IMAGE

EXPECTED_FLAG = "NFX{NFCC_Goes_to_NCSC_2026}"
EXPECTED_SHA256 = "ab61ce519d0776ecae6695649c1a98d741b9cc2ded82e11a508305ae7385a3d9"


class TestWujudAseliAtmin(unittest.TestCase):
    def test_asset_hash(self):
        self.assertTrue(INPUT_IMAGE.exists(), "Berkas dokumentasi.png harus ada.")
        digest = hashlib.sha256(INPUT_IMAGE.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SHA256, "Hash SHA256 input tidak cocok.")

    def test_solve_reproduces_flag(self):
        flag = solve(INPUT_IMAGE)
        self.assertEqual(flag, EXPECTED_FLAG, "Flag hasil rekonstruksi tidak cocok.")


if __name__ == "__main__":
    unittest.main()
