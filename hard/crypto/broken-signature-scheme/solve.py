"""Solve the multi-layer broken RSA signature instance (offline).

Usage:
    python3 solve.py [path/to/output.txt]

Requires pycryptodome. Default input is assets/output.txt.
"""

import hashlib
import json
import sys
from itertools import combinations
from math import isqrt, prod
from pathlib import Path

from Crypto.Cipher import AES

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "assets" / "output.txt"
EXPECTED_SHA256 = "a89d84089e4e67617d57a223474dab7ced37eda40d5b2df31f4b8454c28d4eb7"
EXPECTED_FLAG = b"NXCTF{mult1_l4y3r_l4tt1c3_r54_s1gn4tur3_hnp_8c211ad6b5a6}"


def load_output(path):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected input hash: {digest}")
    data = json.loads(Path(path).read_text())
    modulus = int(data["N"], 16)
    exponent = int(data["e"])
    if modulus <= 1 or not 1 < exponent < modulus:
        raise ValueError("Invalid RSA parameters")
    return data, modulus, exponent


def forge_signature(pairs, target, modulus, exponent):
    """Multiplicative RSA: prod(sig(m_i)) == sig(prod m_i) mod N."""
    for size in range(1, len(pairs) + 1):
        for indices in combinations(range(len(pairs)), size):
            if prod(pairs[i][0] for i in indices) % modulus != target % modulus:
                continue
            forged = prod(pairs[i][1] for i in indices) % modulus
            if pow(forged, exponent, modulus) != target % modulus:
                raise ValueError("Multiplicative forgery did not verify")
            return forged, indices
    raise ValueError("No subset of supplied messages multiplies to the target")


def factor_close_primes(modulus):
    """Fermat factorization; works here because q-p is only ~2^300."""
    a = isqrt(modulus - 1) + 1
    b2 = a * a - modulus
    b = isqrt(b2)
    if b * b != b2:
        raise ValueError("This instance does not factor at Fermat's first candidate")
    p, q = a - b, a + b
    if not (1 < p < q) or p * q != modulus:
        raise ValueError("Invalid factorization")
    return p, q


def solve(path=DEFAULT_INPUT):
    data, modulus, exponent = load_output(path)

    pairs = []
    for item in data["valid_sigs"]:
        message = int.from_bytes(bytes.fromhex(item["msg"]), "big")
        signature = int(item["sig"], 16)
        if not 0 <= signature < modulus or pow(signature, exponent, modulus) != message % modulus:
            raise ValueError("Invalid supplied RSA signature")
        pairs.append((message, signature))
    if not 1 <= len(pairs) <= 16:
        raise ValueError("Subset search expects between 1 and 16 supplied signatures")

    target = int.from_bytes(bytes.fromhex(data["target_msg_hex"]), "big")
    forged, indices = forge_signature(pairs, target, modulus, exponent)

    p, q = factor_close_primes(modulus)
    leaked = (p >> data["leak_pos"]) & ((1 << data["leak_bits"]) - 1)
    if leaked != int(data["leak"], 16) or q - p <= 1 << data["delta_bits"]:
        raise ValueError("Recovered factors do not match the supplied leaks")

    # Cross-check the forgery against the recovered private exponent.
    private = pow(exponent, -1, (p - 1) * (q - 1))
    if pow(target, private, modulus) != forged:
        raise ValueError("Forgery disagrees with the recovered RSA private key")

    # Layer 3: key = SHA256(p_bytes || q_bytes), smaller factor first.
    p_bytes = p.to_bytes((p.bit_length() + 7) // 8, "big")
    q_bytes = q.to_bytes((q.bit_length() + 7) // 8, "big")
    key = hashlib.sha256(p_bytes + q_bytes).digest()
    cipher = data["flag_cipher"]
    aes = AES.new(key, AES.MODE_GCM, nonce=bytes.fromhex(cipher["nonce_hex"]))
    plaintext = aes.decrypt_and_verify(
        bytes.fromhex(cipher["ct_hex"]), bytes.fromhex(cipher["tag_hex"])
    )
    return plaintext, indices, p, q


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_INPUT
    plaintext, indices, p, q = solve(path)
    print(f"Forged signature uses entries: {', '.join(str(i + 1) for i in indices)}")
    print(f"q - p bit length: {(q - p).bit_length()} (delta_bits={q.bit_length() and 300})")
    print("Verified: signatures, RSA factorization, leaked bits and AES-GCM tag")
    print(plaintext.decode("utf-8"))
    if plaintext != EXPECTED_FLAG:
        raise ValueError("Unexpected plaintext")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
