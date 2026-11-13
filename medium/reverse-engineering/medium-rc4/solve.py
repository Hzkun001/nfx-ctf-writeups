#!/usr/bin/env python3
"""Solver untuk challenge Medium RC4 (Medium Reverse Engineering).

Binary validator memakai RC4 dengan kunci yang tertanam di .rodata. Karena RC4
simetris, dekripsi memakai fungsi yang sama dengan enkripsi.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default input: assets/medium_rc4 di direktori yang sama dengan skrip ini.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "medium_rc4"
EXPECTED_SHA256 = "cc8b962d1501755603febfb884c5c49b42d9814aff165ed21d9cc81cda71d0f1"

# Offset di .rodata (berkas dipetakan 1:1 pada segmen ini).
KEY_ADDR = 0x2021          # "n0t_s3cur3_k3y_2026"
KEY_LEN = 19
CT_ADDR = 0x2060           # 42-byte ciphertext
CT_LEN = 0x2A              # 42


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def rc4(key: bytes, data: bytes) -> bytes:
    """RC4 standar: KSA lalu PRGA."""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(byte ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def solve(path: Path = TARGET_FILE) -> str:
    check_input(path)
    data = path.read_bytes()
    key = data[KEY_ADDR:KEY_ADDR + KEY_LEN]
    ct = data[CT_ADDR:CT_ADDR + CT_LEN]
    return rc4(key, ct).decode("ascii")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    print(solve(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
