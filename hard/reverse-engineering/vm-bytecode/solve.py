#!/usr/bin/env python3
"""Solver untuk challenge Hard VM Bytecode (Hard Reverse Engineering).

Binary menjalankan bytecode kustom pada VM kecil. Setiap karakter diproses
dengan urutan LOAD, XOR, ADD, ROL, lalu CMP. Bytecode dan tabel dispatch
tersimpan di .rodata.

Solver membaca tabel dispatch (untuk memetakan opcode ke handler), mem-parse
bytecode, lalu membalik tiap blok lima instruksi dengan urutan terbalik:
ROR (kebalikan ROL), SUB (kebalikan ADD), XOR.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default input: assets/hard_vm di direktori yang sama dengan skrip ini.
"""

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "hard_vm"
EXPECTED_SHA256 = "54cc69e2f8213ccb685818c3a371a08c87caf9d487d5a47b157ab3bcf7f93697"

# Lokasi di .rodata (dipetakan 1:1 pada segmen ini).
DISPATCH_ADDR = 0x2060     # 6 entri int32, offset relatif terhadap alamat ini
DISPATCH_LEN = 6
PROGRAM_ADDR = 0x2080      # bytecode 3-byte per instruksi
HALT = 0xFF

# Handler hasil resolve tabel dispatch (alamat absolut di .text).
HANDLERS = {
    0x11B6: "LOAD",
    0x11A8: "XOR",
    0x115C: "ADD",
    0x119D: "ROL",
    0x11AE: "CMP",
}


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def parse_dispatch(data: bytes) -> dict[int, str]:
    """Petakan opcode -> nama handler dari tabel dispatch.

    Interpreter melakukan `movsxd rax,[rdi+rax*4]; add rax,rdi; jmp rax`
    dengan rdi = DISPATCH_ADDR, sehingga tiap entri adalah offset relatif.
    """
    table = {}
    for op in range(DISPATCH_LEN):
        off = DISPATCH_ADDR + op * 4
        rel = struct.unpack_from("<i", data, off)[0]
        target = (DISPATCH_ADDR + rel) & 0xFFFFFFFFFFFFFFFF
        table[op] = HANDLERS.get(target, f"0x{target:x}")
    return table


def parse_program(data: bytes) -> list[tuple[int, int, int]]:
    """Baca instruksi 3-byte sampai opcode HALT."""
    ins = []
    pos = PROGRAM_ADDR
    while pos + 3 <= len(data):
        op, a, b = data[pos], data[pos + 1], data[pos + 2]
        ins.append((op, a, b))
        pos += 3
        if op == HALT:
            break
    return ins


def rotr8(b: int, s: int) -> int:
    s &= 7
    return b if s == 0 else ((b >> s) | (b << (8 - s))) & 0xFF


def solve(path: Path = TARGET_FILE) -> str:
    check_input(path)
    data = path.read_bytes()

    dispatch = parse_dispatch(data)
    program = parse_program(data)

    # Validasi struktur: blok 5 instruksi LOAD/XOR/ADD/ROL/CMP + HALT.
    if not program or program[-1][0] != HALT:
        raise ValueError("program tidak diakhiri HALT")

    body = program[:-1]
    if len(body) % 5 != 0:
        raise ValueError(f"jumlah instruksi {len(body)} bukan kelipatan 5")

    expected = ["LOAD", "XOR", "ADD", "ROL", "CMP"]
    plain = bytearray()

    for idx in range(0, len(body), 5):
        block = body[idx:idx + 5]
        names = [dispatch[op] for op, _, _ in block]
        if names != expected:
            raise ValueError(f"blok @{idx}: pola {names} != {expected}")

        (_, _, load_i), (_, _, k_xor), (_, _, k_add), (_, _, rot), (_, _, target) = block
        if load_i != idx // 5:
            raise ValueError(f"blok @{idx}: indeks LOAD {load_i} tidak sesuai")

        x = target
        x = rotr8(x, rot)          # kebalikan ROL
        x = (x - k_add) & 0xFF     # kebalikan ADD
        x ^= k_xor                 # kebalikan XOR
        plain.append(x)

    return plain.decode("ascii")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    print(solve(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
