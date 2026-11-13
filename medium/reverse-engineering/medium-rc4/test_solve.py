#!/usr/bin/env python3
"""Unit test untuk solver Medium RC4."""

import hashlib
import unittest
from pathlib import Path

from solve import EXPECTED_SHA256, TARGET_FILE, rc4, solve

EXPECTED_FLAG = "NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}"
KEY = b"n0t_s3cur3_k3y_2026"


class TestMediumRC4(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas lampiran harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_flag(self):
        """Solver harus memulihkan flag yang benar."""
        self.assertEqual(solve(TARGET_FILE), EXPECTED_FLAG)

    def test_rc4_simetris(self):
        """RC4 simetris: enkripsi lalu dekripsi mengembalikan plaintext."""
        msg = b"NFX{roundtrip}"
        self.assertEqual(rc4(KEY, rc4(KEY, msg)), msg)

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        from solve import check_input
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "medium_rc4"
            fake.write_bytes(b"bukan binary asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
