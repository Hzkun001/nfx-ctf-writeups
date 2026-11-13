#!/usr/bin/env python3
"""Unit test untuk solver Hard VM Bytecode."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from solve import (
    DISPATCH_ADDR,
    HALT,
    PROGRAM_ADDR,
    TARGET_FILE,
    EXPECTED_SHA256,
    check_input,
    parse_dispatch,
    parse_program,
    rotr8,
    solve,
)

EXPECTED_FLAG = "NFX{vm_byt3c0d3_1s_l1k3_4_puzzl3}"


def rotl8(b: int, s: int) -> int:
    s &= 7
    return b if s == 0 else ((b << s) | (b >> (8 - s))) & 0xFF


def run_vm(flag: str, data: bytes) -> bool:
    """Reimplementasi VM: jalankan bytecode terhadap flag, cek semua CMP."""
    program = parse_program(data)
    body = program[:-1]
    regs = [0] * 256
    ok = True
    for idx in range(0, len(body), 5):
        (_, r_load, i_load), (_, r_xor, k_xor), (_, r_add, k_add), (_, r_rol, rot), (_, r_cmp, target) = body[idx:idx + 5]
        regs[r_load] = ord(flag[i_load]) & 0xFF
        regs[r_xor] ^= k_xor
        regs[r_add] = (regs[r_add] + k_add) & 0xFF
        regs[r_rol] = rotl8(regs[r_rol], rot)
        if regs[r_cmp] != target:
            ok = False
    return ok


class TestVMBytecode(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas lampiran harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_flag(self):
        """Solver harus memulihkan flag yang benar."""
        self.assertEqual(solve(TARGET_FILE), EXPECTED_FLAG)

    def test_dispatch_table(self):
        """Tabel dispatch harus memetakan opcode 1..5 ke handler yang diharapkan.

        Entri 0 juga menunjuk LOAD, tetapi tidak pernah dipakai: interpreter
        menolak opcode 0 (`test al,al; je wrong`) sebelum melakukan lookup.
        """
        data = TARGET_FILE.read_bytes()
        table = parse_dispatch(data)
        self.assertEqual(
            {op: name for op, name in table.items() if op != 0},
            {1: "LOAD", 2: "XOR", 3: "ADD", 4: "ROL", 5: "CMP"},
        )
        self.assertEqual(table[0], "LOAD")  # entri duplikat / dead entry

    def test_vm_menerima_flag(self):
        """VM reimplementasi harus meloloskan flag yang dipulihkan."""
        data = TARGET_FILE.read_bytes()
        self.assertTrue(run_vm(EXPECTED_FLAG, data))

    def test_vm_menolak_flag_salah(self):
        """VM reimplementasi harus menolak flag yang salah."""
        data = TARGET_FILE.read_bytes()
        salah = "NFX{" + "a" * (len(EXPECTED_FLAG) - 5) + "}"
        self.assertFalse(run_vm(salah, data))

    def test_program_berakhir_halt(self):
        """Program harus diakhiri opcode HALT 0xff."""
        data = TARGET_FILE.read_bytes()
        program = parse_program(data)
        self.assertEqual(program[-1][0], HALT)

    def test_rotasi_saling_invers(self):
        """rotr8 membalik rotl8 untuk semua shift."""
        for s in range(8):
            for v in (0x00, 0x01, 0x7F, 0x80, 0xA5, 0xFF):
                self.assertEqual(rotr8(rotl8(v, s), s), v)

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "hard_vm"
            fake.write_bytes(b"bukan binary asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
