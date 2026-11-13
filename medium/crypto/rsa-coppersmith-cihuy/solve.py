#!/usr/bin/env python3
"""
Challenge: RSA Coppersmith cihuy
Kategori : Crypto
Difficulty: Medium
Author   : Illal
"""

import math
import os
import sys

try:
    from flint import fmpz, fmpz_mat, fmpz_poly
except ImportError:
    fmpz = fmpz_mat = fmpz_poly = None


def solve(chall_path: str = None) -> str:
    if fmpz is None or fmpz_mat is None or fmpz_poly is None:
        raise ImportError(
            "Pustaka 'python-flint' diperlukan untuk menjalankan solver ini. "
            "Pasang via 'pip install python-flint' atau aktifkan venv yang sesuai."
        )

    if chall_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chall_path = os.path.join(base_dir, "assets", "chall.py")

    ns = {}
    with open(chall_path, "r", encoding="utf-8") as f:
        exec(f.read(), ns)

    n = ns["n"]
    e = ns["e"]
    c = ns["c"]
    p_msb = ns["p_msb"]
    unknown_bits = ns["unknown_bits"]

    a = p_msb << unknown_bits
    X = 1 << unknown_bits
    f = fmpz_poly([a, 1])  # f(x) = a + x mod p

    # Konstruksi kisi Coppersmith Howgrave-Graham untuk f(x) mod p
    for m, t in [(3, 3), (4, 4), (5, 5), (6, 6)]:
        d = m + t
        polys = []
        fp = [fmpz_poly([1])]
        for i in range(1, m + 1):
            fp.append(fp[-1] * f)
        for i in range(m):
            polys.append(fp[i] * fmpz(n) ** (m - i))
        for j in range(t):
            polys.append(fp[m] * fmpz_poly([0] * j + [1]))

        rows = []
        for p_ in polys:
            co = p_.coeffs() + [0] * (d - len(p_.coeffs()))
            rows.append([int(co[k]) * (X**k) for k in range(d)])

        M = fmpz_mat(rows).lll()

        for r in range(d):
            co = [int(M[r, k]) // (X**k) for k in range(d)]
            g = fmpz_poly(co)
            try:
                roots = g.roots() if hasattr(g, "roots") else []
            except Exception:
                roots = []

            for rt in roots:
                try:
                    x0 = int(rt[0]) if isinstance(rt, tuple) else int(rt)
                except Exception:
                    continue

                if 0 <= x0 < X:
                    candidate_p = a + x0
                    g_val = math.gcd(candidate_p, n)
                    if g_val not in (1, n):
                        p = g_val
                        q = n // p
                        phi = (p - 1) * (q - 1)
                        d_key = pow(e, -1, phi)
                        m_val = pow(c, d_key, n)
                        pt_bytes = m_val.to_bytes((m_val.bit_length() + 7) // 8, "big")
                        return pt_bytes.decode("utf-8")

    raise ValueError("Akar Coppersmith tidak menghasilkan faktorisasi n")


if __name__ == "__main__":
    try:
        flag = solve()
        print(f"[+] Recovered Flag: {flag}")
    except ImportError as err:
        print(f"[-] {err}", file=sys.stderr)
        sys.exit(1)
