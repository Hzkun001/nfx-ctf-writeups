#!/usr/bin/env python3
"""Unit test untuk solver Hard Feistel."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from solve import (
    CT_FILE_OFF,
    CT_LEN,
    EXPECTED_SHA256,
    F_MUL,
    KEY_MUL,
    MASK16,
    MASK32,
    ROUNDS,
    TARGET_FILE,
    check_input,
    feistel_decrypt_block,
    feistel_encrypt_block,
    load_round_keys,
    solve,
)

EXPECTED_FLAG = "NFX{f315t3l_n3tw0rk_16_r0und5_r3v3rs3d}"


class TestHardFeistel(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas lampiran harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_flag(self):
        """Solver harus memulihkan flag yang benar."""
        self.assertEqual(solve(TARGET_FILE), EXPECTED_FLAG)

    def test_jumlah_round_key(self):
        """Harus ada 16 round key sesuai jumlah ronde."""
        keys = load_round_keys(TARGET_FILE.read_bytes())
        self.assertEqual(len(keys), ROUNDS)

    def test_jadwal_kunci(self):
        """Jadwal kunci: K[i] = 0x5a + 0x1f*i (mod 256), disimpan sebagai uint32."""
        keys = load_round_keys(TARGET_FILE.read_bytes())
        for i, k in enumerate(keys):
            self.assertEqual(k, (0x5A + 0x1F * i) & 0xFF)

    def test_roundtrip_blok(self):
        """Enkripsi lalu dekripsi satu blok mengembalikan nilai semula."""
        keys = load_round_keys(TARGET_FILE.read_bytes())
        for L, R in [(0, 0), (0xFFFF, 0x0001), (0xDEAD, 0xBEEF), (0x1234, 0x5678)]:
            a, b = feistel_encrypt_block(L, R, keys)
            self.assertEqual(feistel_decrypt_block(a, b, keys), (L, R))

    def test_rekripsi_cocok_ciphertext(self):
        """Enkripsi maju atas flag yang dipulihkan harus sama dengan ciphertext."""
        data = TARGET_FILE.read_bytes()
        keys = load_round_keys(data)
        flag = EXPECTED_FLAG.encode("ascii")
        padded = flag + b"\x00" * ((4 - len(flag) % 4) % 4)

        rebuilt = b""
        for off in range(0, len(padded), 4):
            L = (padded[off] << 8) | padded[off + 1]
            R = (padded[off + 2] << 8) | padded[off + 3]
            a, b = feistel_encrypt_block(L, R, keys)
            rebuilt += bytes([a >> 8, a & 0xFF, b >> 8, b & 0xFF])

        ct = data[CT_FILE_OFF:CT_FILE_OFF + CT_LEN]
        self.assertEqual(rebuilt, ct)

    def test_F_16bit(self):
        """F harus selalu menghasilkan nilai 16-bit."""
        for r in (0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFF):
            for k in (0x5A, 0x79, 0x2B):
                v = (((r * F_MUL) & MASK32) >> 5) ^ ((k * KEY_MUL) & MASK32)
                self.assertGreaterEqual(v & MASK16, 0)
                self.assertLessEqual(v & MASK16, MASK16)

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "hard_feistel"
            fake.write_bytes(b"bukan binary asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
