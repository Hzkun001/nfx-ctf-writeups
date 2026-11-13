#!/usr/bin/env python3
"""Unit test untuk solver Medium TEA."""

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from solve import (
    CT_ADDR,
    CT_LEN,
    EXPECTED_SHA256,
    TARGET_FILE,
    check_input,
    solve,
    tea_decrypt_block,
    tea_encrypt_block,
)

EXPECTED_FLAG = "NFX{t1ny_3ncrypt10n_4lg0r1thm_32_r0und5}"


class TestMediumTEA(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas lampiran harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_flag(self):
        """Solver harus memulihkan flag yang benar."""
        self.assertEqual(solve(TARGET_FILE), EXPECTED_FLAG)

    def test_roundtrip(self):
        """Enkripsi lalu dekripsi satu blok mengembalikan nilai semula."""
        for v0, v1 in [(0, 0), (0xDEADBEEF, 0xCAFEBABE), (0xFFFFFFFF, 1)]:
            a, b = tea_encrypt_block(v0, v1)
            self.assertEqual(tea_decrypt_block(a, b), (v0, v1))

    def test_rekripsi_cocok_ciphertext(self):
        """Enkripsi ulang plaintext yang dipulihkan harus sama dengan ciphertext."""
        flag = solve(TARGET_FILE).encode("ascii")
        padded = flag + b"\x00" * ((8 - len(flag) % 8) % 8)
        rebuilt = b""
        for off in range(0, len(padded), 8):
            v0, v1 = struct.unpack("<II", padded[off:off + 8])
            a, b = tea_encrypt_block(v0, v1)
            rebuilt += struct.pack("<II", a, b)
        ct = TARGET_FILE.read_bytes()[CT_ADDR:CT_ADDR + CT_LEN]
        self.assertEqual(rebuilt, ct)

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "medium_tea"
            fake.write_bytes(b"bukan binary asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
