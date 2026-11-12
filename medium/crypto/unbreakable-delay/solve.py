#!/usr/bin/env python3
"""Solver untuk challenge Unbreakable Delay (Crypto - NFX CTF).

Alur:
1. Layanan mengimplementasikan Wesolowski Verifiable Delay Function (VDF):
   y = g^(2^(2^256)) mod n
   di mana delay T = 2^256 normalnya memerlukan waktu eksponensial untuk dihitung.
2. Server membocorkan nilai:
   - Modulus RSA 2048-bit n = p * q
   - Petunjuk bitwise XOR hint = p ^ q (1022-bit)
   - Nilai komputasi target y
   - Bilangan prima penantang l (challenge)
3. Faktorisasi modulus n menggunakan algoritma branch-and-bound bit-by-bit modulo 2^(i+1):
   - Karena p_0 = q_0 = 1, kita menelusuri kandidat (p_i, q_i) yang memenuhi p_i ^ q_i == hint_i
     dan p_test * q_test == n mod 2^(i+1).
   - Ruang cabang sangat sempit dan stabil, memulihkan p dan q dalam ~20 detik.
4. Setelah p dan q ditemukan, fungsi totient Euler dihitung:
   phi(n) = (p - 1) * (q - 1)
5. Bypass Wesolowski VDF:
   - Persamaan verifikasi: pi^l * g^r == y (mod n), di mana r = 2^T mod l.
   - Pembagian euclid pada eksponen: 2^T = q_div * l + r
   - Karena gcd(l, phi(n)) == 1, nilai q_div mod phi(n) dapat dihitung instan:
     q_div = ((2^T - r) * pow(l, -1, phi(n))) % phi(n)
   - Bukti pi = g^(q_div) mod n.
6. Mengirimkan pi ke server dan memperoleh flag.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE_PARAMS = HERE / "assets" / "sample_parameters.json"


def factor_rsa_with_xor(n: int, hint: int, bit_len: int = 1025) -> tuple[int, int]:
    """Memfaktorkan n = p * q jika diketahui hint = p ^ q."""
    candidates = [(1, 1)]
    for i in range(1, bit_len):
        next_candidates = []
        bit_t = (hint >> i) & 1
        mod = 1 << (i + 1)
        target = n % mod
        for cp, cq in candidates:
            for p_i in (0, 1):
                q_i = p_i ^ bit_t
                np = cp | (p_i << i)
                nq = cq | (q_i << i)
                if (np * nq) % mod == target:
                    next_candidates.append((np, nq))
        candidates = next_candidates
        for cp, cq in candidates:
            if cp * cq == n:
                return cp, cq
    for cp, cq in candidates:
        if cp * cq == n:
            return cp, cq
    raise ValueError("Gagal memfaktorkan modulus dengan petunjuk XOR.")


def compute_wesolowski_proof(n: int, p: int, q: int, l: int, g: int = 3) -> tuple[int, int]:
    """Menghitung bukti pi dan sisa r untuk Wesolowski VDF."""
    phi = (p - 1) * (q - 1)
    # T = 2**256
    # r = 2^T mod l
    r = pow(2, 2**256, l)
    two_t_mod_phi = pow(2, 2**256, phi)
    q_div = ((two_t_mod_phi - r) * pow(l, -1, phi)) % phi
    pi = pow(g, q_div, n)
    return pi, r


def solve_remote(host: str, port: int) -> str:
    print(f"[*] Menghubungi target {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    buf = ""
    while "Give me the proof (pi):" not in buf:
        chunk = s.recv(4096).decode("utf-8", errors="ignore")
        if not chunk:
            break
        buf += chunk

    m_n = re.search(r"modulus is (\d+)", buf)
    m_hint = re.search(r"hint \(p \^ q\) is (\d+)", buf)
    m_y = re.search(r"in Z_n, g\^\(2\^\(2\^256\)\) == (\d+)", buf)
    m_l = re.search(r"my challenge is (\d+)", buf)

    if not (m_n and m_hint and m_y and m_l):
        s.close()
        raise ValueError(f"Gagal mengekstrak parameter dari server:\n{buf[:300]}")

    n = int(m_n.group(1))
    hint = int(m_hint.group(1))
    y = int(m_y.group(1))
    l = int(m_l.group(1))

    print("[*] Memfaktorkan modulus n...")
    t0 = time.time()
    p, q = factor_rsa_with_xor(n, hint)
    print(f"[+] Faktorisasi selesai dalam {time.time() - t0:.2f} detik.")

    phi = (p - 1) * (q - 1)
    two_t_mod_phi = pow(2, 2**256, phi)

    # Identifikasi basis g (biasanya g = 3)
    g = None
    for cand_g in range(2, 100):
        if pow(cand_g, two_t_mod_phi, n) == y:
            g = cand_g
            break
    if g is None:
        s.close()
        raise ValueError("Basis generator g tidak ditemukan.")
    print(f"[+] Generator g = {g}")

    pi, r = compute_wesolowski_proof(n, p, q, l, g)
    assert (pow(pi, l, n) * pow(g, r, n)) % n == y, "Verifikasi lokal bukti pi gagal."
    print("[+] Bukti pi terverifikasi secara lokal!")

    s.sendall(f"{pi}\n".encode())
    resp = ""
    while True:
        chunk = s.recv(4096).decode("utf-8", errors="ignore")
        if not chunk:
            break
        resp += chunk

    s.close()
    return resp.strip()


def solve_offline() -> str:
    print("[*] Menjalankan verifikasi offline dengan parameter arsip...")
    params = json.loads(SAMPLE_PARAMS.read_text())
    n = int(params["modulus_n"])
    hint = int(params["hint_p_xor_q"])
    y = int(params["y"])
    l = int(params["challenge_l"])
    g = int(params["generator_g"])

    t0 = time.time()
    p, q = factor_rsa_with_xor(n, hint)
    print(f"[+] Modulus berhasil difaktorkan dalam {time.time() - t0:.2f}s.")
    assert p * q == n, "p * q != n"

    pi, r = compute_wesolowski_proof(n, p, q, l, g)
    check = (pow(pi, l, n) * pow(g, r, n)) % n
    assert check == y, f"Verifikasi gagal: {check} != {y}"
    print("[+] Verifikasi persamaan Wesolowski pi^l * g^r == y (mod n) BERHASIL!")
    return params["flag"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Solver Unbreakable Delay")
    parser.add_argument("--remote", action="store_true", help="Jalankan ke server live")
    parser.add_argument("--host", default="s1.nfx.my.id", help="Host remote")
    parser.add_argument("--port", type=int, default=43118, help="Port remote")
    args = parser.parse_args()

    if args.remote:
        try:
            res = solve_remote(args.host, args.port)
            print(f"[+] Respon:\n{res}")
        except Exception as e:
            print(f"[-] Gagal terhubung ke remote: {e}")
            print("[*] Menjalankan verifikasi offline sebagai fallback...")
            flag = solve_offline()
            print(f"[+] Flag arsip: {flag}")
    else:
        flag = solve_offline()
        print(f"[+] Flag arsip: {flag}")


if __name__ == "__main__":
    main()
