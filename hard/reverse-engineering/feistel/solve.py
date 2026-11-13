#!/usr/bin/env python3
"""Solver untuk challenge Hard Feistel (Hard Reverse Engineering).

Binary mengenkripsi flag dengan jaringan Feistel 16 ronde pada blok 32-bit
(L dan R masing-masing 16-bit). Round key diturunkan dari jadwal sederhana dan
tertanam di .rodata; ciphertext 40 byte tersimpan di .data.

Karena Feistel invertible secara struktural, dekripsi cukup menjalankan ronde
dari belakang tanpa menginversi fungsi F.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default input: assets/hard_feistel di direktori yang sama dengan skrip ini.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "hard_feistel"
EXPECTED_SHA256 = "2db9a9e254792a497cc71e64be16b35b02665e4d9d553734dff3b9dfc7e21e51"

# .rodata: vaddr 0x2000 == file offset 0x2000 (dipetakan 1:1).
KEYS_VADDR = 0x2060        # 16 x uint32 little-endian
KEYS_FILE_OFF = 0x2060
# .data: vaddr 0x4000 == file offset 0x3000 (offset file BERBEDA dari vaddr).
CT_VADDR = 0x4020          # 40 byte ciphertext
CT_FILE_OFF = 0x3020

CT_LEN = 40
FLAG_LEN = 0x27            # 39, sesuai strlen yang diminta binary
ROUNDS = 16
MASK32 = 0xFFFFFFFF
MASK16 = 0xFFFF

# Konstanta dari disassembly:
#   imul eax, ebx, 0x9e3779b1 ; shr eax, 5 ; movzx eax, ax
#   k*0x101  (compiler menulis: shl edx,8 ; add edx,ebp)
F_MUL = 0x9E3779B1
KEY_MUL = 0x101


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def load_round_keys(data: bytes) -> list[int]:
    keys = []
    for i in range(ROUNDS):
        off = KEYS_FILE_OFF + i * 4
        keys.append(int.from_bytes(data[off:off + 4], "little"))
    return keys


def F(r: int, k: int) -> int:
    """Fungsi ronde 16-bit.

    `imul` 32-bit lalu `shr 5` mengambil bit 5..20, kemudian `movzx ax`
    memotongnya ke 16 bit; `k * 0x101` adalah trik kompilator untuk
    menduplikasi byte kunci (k<<8 | k).
    """
    return ((((r * F_MUL) & MASK32) >> 5) ^ ((k * KEY_MUL) & MASK32)) & MASK16


def feistel_encrypt_block(L: int, R: int, keys: list[int]) -> tuple[int, int]:
    for k in keys:
        L, R = R, (L ^ F(R, k)) & MASK16
    return L, R


def feistel_decrypt_block(L: int, R: int, keys: list[int]) -> tuple[int, int]:
    for k in reversed(keys):
        L, R = (R ^ F(L, k)) & MASK16, L
    return L, R


def solve(path: Path = TARGET_FILE) -> str:
    check_input(path)
    data = path.read_bytes()

    keys = load_round_keys(data)
    ct = data[CT_FILE_OFF:CT_FILE_OFF + CT_LEN]

    plain = bytearray()
    for off in range(0, CT_LEN, 4):
        # Blok dibaca big-endian: L = b0<<8|b1, R = b2<<8|b3
        L = (ct[off] << 8) | ct[off + 1]
        R = (ct[off + 2] << 8) | ct[off + 3]
        L, R = feistel_decrypt_block(L, R, keys)
        plain += bytes([L >> 8, L & 0xFF, R >> 8, R & 0xFF])

    # Padding nol: buang NUL di akhir.
    return plain.rstrip(b"\x00").decode("ascii")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    print(solve(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
