#!/usr/bin/env python3
"""Solver untuk challenge FlagKeepers (Crypto - NFX CTF).

Alur:
1. Layanan mempertahankan dua konteks AES-GCM (key_a dan key_b) yang berbagi satu nonce.
2. Setiap kali menu Option 2 (Recovery Log) dipanggil, pesan dienkripsi dengan key_b dan nonce sesi yang sama.
3. Karena nonce digunakan berulang kali pada key_b:
   - Keystream E_K(J_i) dapat dipulihkan dengan XOR: PT XOR CT.
   - Tag autentikasi AES-GCM dihitung sebagai: Tag = GHASH(H, CT || len) XOR E_K(J_0).
   - Selisih dua tag: Delta_Tag = GHASH(H, CT_1) XOR GHASH(H, CT_2).
   - Persamaan polinomial di GF(2^128) dapat disusun.
4. Dengan mengumpulkan 3 pasang (CT, Tag) dari Option 2, kita membentuk dua polinomial selisih.
5. Menghitung GCD polinomial di GF(2^128) menghasilkan faktor derajat 1: (x XOR H_b).
6. Dari H_b, kita memulihkan term masking S_b = E_K(J_0).
7. Nilai idx disesuaikan ke 240 dengan memanggil Option 1 (Audit Log) dua kali (208 + 16 + 16 = 240).
8. Kita memalsukan ciphertext untuk b"admin = True" dan menghitung tag GHASH valid.
9. Mengirim payload ke Option 4 untuk mengekstrak flag.
"""

from __future__ import annotations

import argparse
import re
import socket
import struct
import subprocess
import sys
import time

# ==================== GF(2^128) Arithmetic ====================
R_CONST = 0xE1000000000000000000000000000000
ONE = 1 << 127  # Multiplicative identity dalam bit representation GCM


def gf_mul(x: int, y: int) -> int:
    z = 0
    v = y
    for i in range(128):
        if x & (1 << (127 - i)):
            z ^= v
        carry = v & 1
        v >>= 1
        if carry:
            v ^= R_CONST
    return z


def gf_inv(a: int) -> int:
    r = ONE
    b = a
    e = (1 << 128) - 2
    while e:
        if e & 1:
            r = gf_mul(r, b)
        b = gf_mul(b, b)
        e >>= 1
    return r


def b2g(b: bytes) -> int:
    return int.from_bytes(b, "big")


def g2b(n: int) -> bytes:
    return n.to_bytes(16, "big")


def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def pad16(d: bytes) -> bytes:
    return d if len(d) % 16 == 0 else d + b"\x00" * (16 - len(d) % 16)


def ghash(H: int, data: bytes) -> int:
    y = 0
    for i in range(0, len(data), 16):
        y = gf_mul(y ^ b2g(data[i : i + 16]), H)
    return y


def build_gi(ct: bytes) -> bytes:
    return pad16(ct) + struct.pack(">QQ", 0, len(ct) * 8)


# ==================== Polinomial di GF(2^128) ====================
def pdeg(p: list[int]) -> int:
    d = len(p) - 1
    while d >= 0 and p[d] == 0:
        d -= 1
    return d


def ptrim(p: list[int]) -> list[int]:
    d = pdeg(p)
    return p[: d + 1] if d >= 0 else [0]


def pmod(a: list[int], b: list[int]) -> list[int]:
    a = list(a)
    db = pdeg(b)
    if db < 0:
        raise ZeroDivisionError
    lci = gf_inv(b[db])
    da = pdeg(a)
    while da >= db:
        c = gf_mul(a[da], lci)
        for i in range(db + 1):
            a[da - db + i] ^= gf_mul(c, b[i])
        da = pdeg(a)
    return ptrim(a)


def pgcd(a: list[int], b: list[int]) -> list[int]:
    a = ptrim(a)
    b = ptrim(b)
    while pdeg(b) > 0:
        a, b = b, pmod(a, b)
    if pdeg(b) == 0 and b[0] != 0:
        return [ONE]
    if pdeg(a) >= 0 and a[pdeg(a)] != 0:
        lci = gf_inv(a[pdeg(a)])
        a = [gf_mul(c, lci) for c in a]
    return ptrim(a)


def diff_poly(ct1: bytes, tag1: bytes, ct2: bytes, tag2: bytes) -> list[int]:
    gi1 = build_gi(ct1)
    gi2 = build_gi(ct2)
    n1 = len(gi1) // 16
    n2 = len(gi2) // 16
    mx = max(n1, n2)
    p = [0] * (mx + 1)
    p[0] = b2g(tag1) ^ b2g(tag2)
    for i in range(n1):
        p[n1 - i] ^= b2g(gi1[i * 16 : (i + 1) * 16])
    for i in range(n2):
        p[n2 - i] ^= b2g(gi2[i * 16 : (i + 1) * 16])
    return ptrim(p)


def clean_ansi(t: str) -> str:
    return re.sub(r"\033\[[0-9;]*[a-zA-Z]", "", t)


class SocketClient:
    def __init__(self, host: str, port: int):
        self.s = socket.socket()
        self.s.settimeout(10)
        self.s.connect((host, port))
        self.buf = b""

    def recv_until(self, marker: bytes, timeout: float = 10.0) -> bytes:
        end = time.time() + timeout
        while marker not in self.buf:
            if time.time() > end:
                break
            try:
                data = self.s.recv(4096)
                if not data:
                    break
                self.buf += data
            except socket.timeout:
                break
        idx = self.buf.find(marker)
        if idx >= 0:
            res = self.buf[: idx + len(marker)]
            self.buf = self.buf[idx + len(marker) :]
            return res
        res = self.buf
        self.buf = b""
        return res

    def sendline(self, line: str | bytes) -> None:
        if isinstance(line, str):
            line = line.encode()
        self.s.sendall(line + b"\n")

    def close(self) -> None:
        self.s.close()


def get_pair(client: SocketClient, option: bytes = b"2") -> tuple[bytes, bytes, bytes]:
    client.recv_until(b"> ")
    client.sendline(option)
    raw = client.recv_until(b"\n\n", timeout=5)
    if b"Tag:" not in raw:
        raw += client.recv_until(b"\n", timeout=5)
    txt = clean_ansi(raw.decode(errors="ignore"))
    lm = re.search(r"Log \[(.+?)\]", txt)
    cm = re.search(r"CT: ([0-9a-f]+)", txt)
    tm = re.search(r"Tag: ([0-9a-f]+)", txt)
    if not (lm and cm and tm):
        raise ValueError(f"Gagal mem-parsing respons: {txt[:200]}")
    pt = lm.group(1).encode()
    ct = bytes.fromhex(cm.group(1))
    tag = bytes.fromhex(tm.group(1))
    return pt, ct, tag


def solve_remote(host: str, port: int) -> str:
    client = SocketClient(host, port)
    client.recv_until(b"[5] Exit")

    # Ambil 3 pasang log pemulihan (key_b, session nonce)
    pairs = [get_pair(client, b"2") for _ in range(3)]

    # Sesuaikan idx ke 240 dengan memanggil Option 1 dua kali
    get_pair(client, b"1")
    get_pair(client, b"1")

    pt1, ct1, tag1 = pairs[0]
    pt2, ct2, tag2 = pairs[1]
    pt3, ct3, tag3 = pairs[2]

    keystream_b = xor_bytes(pt1, ct1)
    p12 = diff_poly(ct1, tag1, ct2, tag2)
    p13 = diff_poly(ct1, tag1, ct3, tag3)

    g = pgcd(p12, p13)
    if pdeg(g) != 1:
        client.close()
        raise ValueError(f"Derajat GCD adalah {pdeg(g)}, diharapkan 1.")

    H_b = g[0]
    gi1 = build_gi(ct1)
    S_b = b2g(tag1) ^ ghash(H_b, gi1)

    # Validasi dengan pasangan ke-2
    gi2 = build_gi(ct2)
    if (ghash(H_b, gi2) ^ S_b) != b2g(tag2):
        client.close()
        raise ValueError("Validasi H_b gagal pada pasangan ke-2.")

    # Palsukan ciphertext dan tag untuk b"admin = True"
    target_pt = b"admin = True"
    forged_ct = xor_bytes(target_pt, keystream_b[: len(target_pt)])
    forged_gi = build_gi(forged_ct)
    forged_tag = g2b(ghash(H_b, forged_gi) ^ S_b)

    # Kirim ke Option 4
    client.recv_until(b"> ")
    client.sendline(b"4")
    client.recv_until(b"CT: ")
    client.sendline(forged_ct.hex())
    client.recv_until(b"Tag: ")
    client.sendline(forged_tag.hex())

    time.sleep(0.5)
    resp = client.recv_until(b"\n", timeout=5)
    clean_resp = clean_ansi(resp.decode(errors="ignore")).strip()
    client.close()
    return clean_resp


def main() -> None:
    parser = argparse.ArgumentParser(description="Solver FlagKeepers")
    parser.add_argument("--host", default="s1.nfx.my.id", help="Host remote")
    parser.add_argument("--port", type=int, default=44421, help="Port remote")
    args = parser.parse_args()

    print(f"[*] Menghubungi target {args.host}:{args.port}...")
    try:
        flag = solve_remote(args.host, args.port)
        print(f"[+] Flag berhasil didapatkan:\n{flag}")
    except Exception as e:
        print(f"[-] Terjadi kesalahan / koneksi gagal: {e}")
        print("[*] (Layanan remote mungkin sudah selesai saat pasca-kompetisi)")


if __name__ == "__main__":
    main()
