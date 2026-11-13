#!/usr/bin/env python3
"""Solver untuk challenge Castaway (Hard Reverse Engineering).

Binary membaca calon flag dari stdin, memvalidasinya lewat state machine kecil
dengan opaque predicate, lalu mentransformasi tiap byte memakai state berantai,
S-box 256 entri, tabel penambah, dan rotasi. Hasilnya dibandingkan dengan
ciphertext 40 byte di .rodata.

Karena transformasi bersifat berantai (state byte i bergantung pada ciphertext
byte i), state dapat direkonstruksi dari ciphertext saja, lalu tiap langkah
dibalik satu per satu. Tidak perlu menginversi rotasi "secara manual": cukup
rotasi ke arah berlawanan.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default input: assets/castaway di direktori yang sama dengan skrip ini.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "castaway"
EXPECTED_SHA256 = "6ca0a8f8e50b77f7dc666cf1b7a486f1a12df1008c478cbbe6615245bca776d1"

# Lokasi di .rodata (dipetakan 1:1 pada segmen ini).
SBOX_ADDR = 0x2020         # 256 byte, permutasi penuh
SBOX_LEN = 256
ADD_ADDR = 0x2120          # 16 byte tabel penambah
ADD_LEN = 16
CT_ADDR = 0x2140           # 40 byte ciphertext
CT_LEN = 40

INIT_STATE = 0xA5
STATE_MUL = 125            # disassembly: imul eax, 0xffffff83  (== -125)
XOR_MUL = 0x2F             # disassembly: imul eax, 0x2f


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def rotl8(b: int, s: int) -> int:
    s &= 7
    return b if s == 0 else ((b << s) | (b >> (8 - s))) & 0xFF


def rotr8(b: int, s: int) -> int:
    s &= 7
    return b if s == 0 else ((b >> s) | (b << (8 - s))) & 0xFF


def build_states(ct: bytes) -> list[int]:
    """Rekonstruksi state sebelum tiap byte dari ciphertext.

    state awal 0xa5; setelah memproses byte i:
        state = (i + ct[i] - 125 * state) & 0xff
    """
    states = []
    state = INIT_STATE
    for i, b in enumerate(ct):
        states.append(state)
        state = (i + b - STATE_MUL * state) & 0xFF
    return states


def solve(path: Path = TARGET_FILE) -> str:
    check_input(path)
    data = path.read_bytes()

    sbox = data[SBOX_ADDR:SBOX_ADDR + SBOX_LEN]
    addt = data[ADD_ADDR:ADD_ADDR + ADD_LEN]
    ct = data[CT_ADDR:CT_ADDR + CT_LEN]

    inv_sbox = [0] * 256
    for i, v in enumerate(sbox):
        inv_sbox[v] = i

    states = build_states(ct)

    plain = bytearray()
    for i, b in enumerate(ct):
        # balik transformasi: XOR indeks -> S-box -> tambah -> rotasi -> XOR state
        b ^= (i * XOR_MUL) & 0xFF
        b = inv_sbox[b]
        b = (b - addt[i & 0x0F]) & 0xFF
        b = rotr8(b, (i % 7) + 1)
        plain.append(b ^ states[i])

    return plain.decode("ascii")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    print(solve(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
