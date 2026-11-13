#!/usr/bin/env python3
"""
Challenge: Static IV Offline
Kategori : Crypto
Difficulty: Medium
Author   : rio
"""

import hashlib
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

MASTER = b"\x13\x37" * 16
PREFIX = b"user-input-goes-here:"


def get_key(counter: int) -> bytes:
    return hashlib.sha256(MASTER + counter.to_bytes(4, "little")).digest()[:32]


def solve(output_path: str = None) -> str:
    if output_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "assets", "output.txt")

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    counter = data["counter"]
    iv = bytes.fromhex(data["iv_hex"])
    ct = bytes.fromhex(data["ct_hex"])

    key = get_key(counter)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), 16)

    prefix_delim = PREFIX + b"|"
    if pt.startswith(prefix_delim):
        flag = pt[len(prefix_delim):].decode("utf-8")
    else:
        flag = pt.decode("utf-8")

    return flag


if __name__ == "__main__":
    flag = solve()
    print(f"[+] Recovered Flag: {flag}")
