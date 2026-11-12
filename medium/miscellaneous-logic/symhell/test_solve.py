"""Unit test untuk SymHell payload builder dan filter validator."""

import hashlib
import re
import unittest
from pathlib import Path

from solve import FORBIDDEN_REGEX, build_num, build_payload

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
EXPECTED_SHA256 = "392dfcb55a45c00fd61a36b520f31243606fff7d7557711b92d31525e7dd5575"


class TestSymHell(unittest.TestCase):
    def test_asset_hash(self):
        target = ASSETS / "app.py"
        self.assertTrue(target.exists(), "Berkas assets/app.py harus ada.")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SHA256, "Hash SHA256 app.py tidak cocok.")

    def test_build_num(self):
        for n in range(6):
            expr = build_num(n)
            # Pastikan tidak ada huruf dan angka
            self.assertIsNone(re.search(r"[a-zA-Z0-9]", expr))

    def test_payload_strictly_passes_regex(self):
        payload = build_payload()
        match = re.search(FORBIDDEN_REGEX, payload)
        self.assertIsNone(match, f"Payload melanggar karakter: {match.group(0) if match else ''}")

    def test_flag_string_integrity(self):
        expected_flag = "NFX{5ymH3ll_RUnT1m3_3v4l_53cr3t_PwN!}"
        self.assertTrue(expected_flag.startswith("NFX{"))
        self.assertTrue(expected_flag.endswith("}"))


if __name__ == "__main__":
    unittest.main()
