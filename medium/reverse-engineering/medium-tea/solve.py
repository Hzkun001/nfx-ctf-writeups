#!/usr/bin/env python3
"""Solver untuk challenge Medium TEA (Medium Reverse Engineering).

Binary validator memakai TEA 32 ronde dengan kunci 128-bit yang tertanam.
Flag dipad nol ke kelipatan 8 byte, tiap blok 64-bit dienkripsi, lalu
dibandingkan dengan ciphertext. TEA invertible, jadi dekripsi cukup menjalankan
ronde terbalik tanpa menginversi fungsi F.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default input: assets/medium_tea di direktori yang sama dengan skrip ini.
"""

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "medium_tea"
EXPECTED_SHA256 = "a2b45f299304e0cc64582e0bdc704100b9cb2f4fc4c0f164a8cfd322b01b255a"

# Lokasi di .rodata (dipetakan 1:1 pada segmen ini).
CT_ADDR = 0x2040           # 40 byte ciphertext (5 blok)
CT_LEN = 40
FLAG_LEN = 0x28            # 40, sesuai strlen yang diminta binary

# Kunci 128-bit hasil decode konstanta di disassembly.
# 0xcafebabe muncul sebagai sub 0x35014542, 0xdeadc0de sebagai sub 0x21523f22.
KEY = (0x1337BEEF, 0xCAFEBABE, 0xDEADC0DE, 0x0BADF00D)
DELTA = 0x9E3779B9
ROUNDS = 32
MASK = 0xFFFFFFFF


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def tea_encrypt_block(v0: int, v1: int) -> tuple[int, int]:
    k0, k1, k2, k3 = KEY
    s = 0
    for _ in range(ROUNDS):
        s = (s + DELTA) & MASK
        v0 = (v0 + ((((v1 << 4) & MASK) + k0) ^ ((v1 >> 5) + k1) ^ ((v1 + s) & MASK))) & MASK
        v1 = (v1 + ((((v0 << 4) & MASK) + k2) ^ ((v0 >> 5) + k3) ^ ((v0 + s) & MASK))) & MASK
    return v0, v1


def tea_decrypt_block(v0: int, v1: int) -> tuple[int, int]:
    k0, k1, k2, k3 = KEY
    s = (DELTA * ROUNDS) & MASK
    for _ in range(ROUNDS):
        v1 = (v1 - ((((v0 << 4) & MASK) + k2) ^ ((v0 >> 5) + k3) ^ ((v0 + s) & MASK))) & MASK
        v0 = (v0 - ((((v1 << 4) & MASK) + k0) ^ ((v1 >> 5) + k1) ^ ((v1 + s) & MASK))) & MASK
        s = (s - DELTA) & MASK
    return v0, v1


def solve(path: Path = TARGET_FILE) -> str:
    check_input(path)
    data = path.read_bytes()
    ct = data[CT_ADDR:CT_ADDR + CT_LEN]

    plain = bytearray()
    for off in range(0, CT_LEN, 8):
        v0, v1 = struct.unpack("<II", ct[off:off + 8])
        a, b = tea_decrypt_block(v0, v1)
        plain += struct.pack("<II", a, b)

    # Padding nol: buang NUL di akhir.
    return plain.rstrip(b"\x00").decode("ascii")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    print(solve(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
