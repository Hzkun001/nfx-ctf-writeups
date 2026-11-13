#!/usr/bin/env python3
"""Solver untuk challenge Medium RC4 (NFX CTF).

Binary validator memakai RC4 dengan kunci 128-bit yang tertanam di .rodata.
Karena RC4 simetris, dekripsi memakai fungsi yang sama dengan enkripsi.

Pemakaian:
    python3 solve.py [path-ke-binary]

Default path: medium_rc4 di direktori yang sama dengan skrip ini.
"""
import sys
from pathlib import Path

DEFAULT_BIN = Path(__file__).with_name("medium_rc4")

# Lokasi di .rodata (file offset == virtual address karena .rodata dipetakan 1:1
# pada offset yang sama di segmen ini).
RODATA_OFF = 0x2000
KEY_ADDR = 0x2021          # "n0t_s3cur3_k3y_2026"
CT_ADDR = 0x2060           # 42-byte ciphertext
CT_LEN = 0x2A              # 42


def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def solve(bin_path: Path) -> str:
    data = bin_path.read_bytes()
    key = data[KEY_ADDR:KEY_ADDR + 19]
    ct = data[CT_ADDR:CT_ADDR + CT_LEN]
    pt = rc4(key, ct)
    return pt.decode("ascii")


def main() -> int:
    bin_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BIN
    flag = solve(bin_path)
    print(flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
