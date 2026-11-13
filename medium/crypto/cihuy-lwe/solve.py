#!/usr/bin/env python3
"""Solver untuk tantangan Cihuy LWE (Medium Crypto).

Memulihkan rahasia LWE berukuran kecil (ternary) menggunakan reduksi kisi
(Kannan's embedding / CVP via LLL dan BKZ), lalu mendekripsi ciphertext
berbasis PRF counter SHA-256.
"""

import ast
import hashlib
import json
import sys
from pathlib import Path

from fpylll import BKZ, FPLLL, IntegerMatrix, LLL

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "lwe.py"
EXPECTED_SHA256 = "6a996ad10f8ee04aed2f3befe3f1268b2b4bff8c9d6c6740b2cd88db0a623e1c"


def check_inputs(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}")


def load_data(path: Path = TARGET_FILE) -> dict:
    data = {}
    for node in ast.parse(path.read_text()).body:
        if (
            not isinstance(node, ast.Assign)
            or len(node.targets) != 1
            or not isinstance(node.targets[0], ast.Name)
        ):
            raise ValueError("Hanya penetapan variabel literal yang didukung")
        name = node.targets[0].id
        if name in data:
            raise ValueError(f"Variabel duplikat terdeteksi: {name}")
        data[name] = ast.literal_eval(node.value)

    assert set(data) == {"q", "n", "m", "A", "b", "ct"}, "Kunci data LWE tidak lengkap"
    q, n, m = (data[k] for k in ("q", "n", "m"))
    assert (q, n, m) == (257, 40, 64), f"Parameter tidak terduga: q={q}, n={n}, m={m}"
    assert len(data["A"]) == m and all(len(row) == n for row in data["A"])
    assert len(data["b"]) == m
    assert all(type(x) is int and 0 <= x < q for row in data["A"] + [data["b"]] for x in row)
    assert len(bytes.fromhex(data["ct"])) == 41
    return data


def recover(data: dict) -> tuple[list[int], list[int], list[int]]:
    q, n, m = data["q"], data["n"], data["m"]
    embedding = 4

    # Bentuk basis baris dimensi 105:
    # Baris 0..m-1:   [ q * I_m,   0,       0 ]
    # Baris m..m+n-1: [ A^T,       I_n,     0 ]
    # Baris m+n:      [ b^T,       0,       embedding ]
    rows = [[q * (i == j) for j in range(m)] + [0] * (n + 1) for i in range(m)]
    rows += [
        [data["A"][i][j] for i in range(m)] + [int(j == k) for k in range(n)] + [0]
        for j in range(n)
    ]
    rows += [data["b"] + [0] * n + [embedding]]

    basis = IntegerMatrix.from_matrix(rows)
    FPLLL.set_random_seed(0)
    LLL.reduction(basis, delta=0.99)
    BKZ.reduction(basis, BKZ.Param(block_size=20, max_loops=4))

    for i in range(basis.nrows):
        row = [int(basis[i, j]) for j in range(basis.ncols)]
        if abs(row[-1]) != embedding:
            continue
        sign = row[-1] // embedding
        error = [sign * x for x in row[:m]]
        secret = [-sign * x for x in row[m:-1]]
        if max(map(abs, secret)) > 1 or max(map(abs, error)) > 2:
            continue
        predicted = [
            (sum(a * s for a, s in zip(arow, secret)) + e) % q
            for arow, e in zip(data["A"], error)
        ]
        assert predicted == data["b"], "Vektor rahasia gagal memverifikasi persamaan b"
        assert sum(x * x for x in secret) == 25, "Norm kuadrat rahasia s tidak sesuai"
        assert sum(x * x for x in error) == 103, "Norm kuadrat galat e tidak sesuai"
        return secret, error, predicted

    raise RuntimeError("Vektor rahasia ternary dengan batas noise <= 2 tidak ditemukan")


def decrypt(secret: list[int], ciphertext: bytes) -> tuple[str, bytes, bytes]:
    # Serialisasi rahasia bertanda (di mana -1 modulo 256 menjadi 0xff)
    seed = bytes(x % 256 for x in secret)
    stream = b"".join(
        hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for counter in range((len(ciphertext) + 31) // 32)
    )
    stream = stream[: len(ciphertext)]
    plaintext = bytes(x ^ y for x, y in zip(ciphertext, stream))
    flag = plaintext.decode("ascii")
    assert flag.startswith("NFXCTF{") and flag.endswith("}"), f"Format flag tidak valid: {flag}"
    assert bytes(x ^ y for x, y in zip(plaintext, stream)) == ciphertext
    return flag, seed, stream


def solve(path: Path = TARGET_FILE) -> tuple[list[int], str]:
    check_inputs(path)
    data = load_data(path)
    secret, error, predicted = recover(data)
    ciphertext = bytes.fromhex(data["ct"])
    flag, seed, stream = decrypt(secret, ciphertext)
    return secret, flag


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    secret, flag = solve(target)
    print(f"Flag: {flag}")
    print(f"Secret s: {secret}")


if __name__ == "__main__":
    main()
