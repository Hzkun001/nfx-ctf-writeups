#!/usr/bin/env python3
"""Unit test untuk solver Castaway."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from solve import (
    ADD_ADDR,
    ADD_LEN,
    CT_ADDR,
    CT_LEN,
    EXPECTED_SHA256,
    INIT_STATE,
    SBOX_ADDR,
    SBOX_LEN,
    STATE_MUL,
    TARGET_FILE,
    XOR_MUL,
    build_states,
    check_input,
    rotl8,
    rotr8,
    solve,
)

EXPECTED_FLAG = "NFX{c4st4w4y_0n_4n_0p4qu3_st4t3_m4ch1n3}"


def forward_encrypt(flag: str, data: bytes) -> bytes:
    """Reimplementasi transformasi maju untuk memverifikasi hasil."""
    sbox = data[SBOX_ADDR:SBOX_ADDR + SBOX_LEN]
    addt = data[ADD_ADDR:ADD_ADDR + ADD_LEN]
    state = INIT_STATE
    out = bytearray()
    for i, ch in enumerate(flag.encode("ascii")):
        b = ch ^ state
        b = rotl8(b, (i % 7) + 1)
        b = (b + addt[i & 0x0F]) & 0xFF
        b = sbox[b]
        b ^= (i * XOR_MUL) & 0xFF
        out.append(b)
        state = (i + b - STATE_MUL * state) & 0xFF
    return bytes(out)


class TestCastaway(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas lampiran harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_flag(self):
        """Solver harus memulihkan flag yang benar."""
        self.assertEqual(solve(TARGET_FILE), EXPECTED_FLAG)

    def test_rekripsi_cocok_ciphertext(self):
        """Enkripsi maju atas flag yang dipulihkan harus sama dengan ciphertext."""
        data = TARGET_FILE.read_bytes()
        rebuilt = forward_encrypt(EXPECTED_FLAG, data)
        ct = data[CT_ADDR:CT_ADDR + CT_LEN]
        self.assertEqual(rebuilt, ct)

    def test_state_chain(self):
        """Rekonstruksi state harus konsisten dengan definisi berantai."""
        data = TARGET_FILE.read_bytes()
        ct = data[CT_ADDR:CT_ADDR + CT_LEN]
        states = build_states(ct)
        state = INIT_STATE
        for i, b in enumerate(ct):
            self.assertEqual(states[i], state)
            state = (i + b - STATE_MUL * state) & 0xFF

    def test_rotasi_saling_invers(self):
        """rotl8 dan rotr8 saling membalik untuk semua shift."""
        for s in range(8):
            for v in (0x00, 0x01, 0x7F, 0x80, 0xA5, 0xFF):
                self.assertEqual(rotr8(rotl8(v, s), s), v)

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "castaway"
            fake.write_bytes(b"bukan binary asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
