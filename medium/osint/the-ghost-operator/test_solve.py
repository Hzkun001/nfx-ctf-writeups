"""Unit test untuk solver The Ghost Operator OSINT."""

import hashlib
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve_mod)

EXPECTED_FLAG = "NFX{villa_istana_bunga_lembang}"


class TestTheGhostOperator(unittest.TestCase):
    def test_transmission_file_hash(self):
        self.assertTrue(
            solve_mod.TRANSMISSION_FILE.exists(),
            "Berkas rentry_transmission.txt harus tersedia di assets/",
        )
        digest = hashlib.sha256(
            solve_mod.TRANSMISSION_FILE.read_bytes()
        ).hexdigest()
        self.assertEqual(
            digest, solve_mod.EXPECTED_SHA256, "Hash SHA256 teks transmisi tidak cocok."
        )

    def test_rentry_slug_extraction(self):
        slug = solve_mod.extract_rentry_slug_from_commit()
        self.assertEqual(slug, "ghost-route-0914", "Slug rentry tidak cocok.")

    def test_solve_reproduces_flag(self):
        flag = solve_mod.solve(online=False)
        self.assertEqual(flag, EXPECTED_FLAG, "Flag hasil ekstraksi tidak cocok.")
        self.assertTrue(flag.startswith("NFX{"))
        self.assertTrue(flag.endswith("}"))


if __name__ == "__main__":
    unittest.main()
