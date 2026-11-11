#!/usr/bin/env python3
"""Recover the supplied secp256k1 key and authenticate the AES-GCM flag."""
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fpylll import IntegerMatrix, LLL

ROOT = Path(__file__).resolve().parent / "assets"
EXPECTED_SHA256 = {
    "output.txt": "74f93d9a9c1399cfc2a1e756c273fe476992ad035cb910b5bf370a7823aa73e9",
    "pubkey.pem": "500c7aaa3253086496b618836c14c8bbefe5123c2f857563bdaaf84803360212",
    "challenge.py": "b2df03ad70dd772ef0ddefc44a4cc4bca6461d1f61103e1145b0ab8e64417063",
}


def check_inputs():
    for name, want in EXPECTED_SHA256.items():
        got = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if got != want:
            raise ValueError(f"Unexpected hash for {name}: {got}")

ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

BOUND = 1 << 248


def solve():
    check_inputs()
    data = json.loads((ROOT / "output.txt").read_text())
    if data["curve"] != "secp256k1" or int(data["n"], 0) != ORDER:
        raise ValueError("Unexpected curve or subgroup order")
    public = serialization.load_pem_public_key((ROOT / "pubkey.pem").read_bytes())
    if not isinstance(public, ec.EllipticCurvePublicKey) or public.curve.name != "secp256k1":
        raise ValueError("Unexpected public-key type")
    embedded = serialization.load_pem_public_key(data["pubkey_pem"].encode())
    if embedded.public_numbers() != public.public_numbers():
        raise ValueError("Public-key inputs disagree")
    signatures = []
    for item in data["signatures"]:
        r, s, h = (int(item[name], 0) for name in ("r", "s", "h"))
        if not (0 < r < ORDER and 0 < s < ORDER and 0 <= h < 2**256):
            raise ValueError("Invalid signature parameters")
        if item["K_BITS"] != 248 or item["top8_k"] != 0:
            raise ValueError("Unexpected nonce-bias metadata")
        digest = hashlib.sha256(bytes.fromhex(item["msg"])).digest()
        if int.from_bytes(digest, "big") != h:
            raise ValueError("Message hash mismatch")
        public.verify(utils.encode_dss_signature(r, s), digest,
                      ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        signatures.append((r, s, h))
    count = 48
    if len(signatures) < count:
        raise ValueError("This solver requires at least 48 biased signatures")
    scale = ORDER // BOUND
    basis = IntegerMatrix(count + 2, count + 2)
    for index, (r, s, h) in enumerate(signatures[:count]):
        inverse = pow(s, -1, ORDER)
        a, b = r * inverse % ORDER, h * inverse % ORDER
        basis[index, index] = ORDER * scale
        basis[count, index] = a * scale
        basis[count + 1, index] = (b - BOUND // 2) * scale
    basis[count, count] = 1
    basis[count + 1, count + 1] = ORDER // 2
    LLL.reduction(basis, delta=0.99)
    for row in range(count + 2):
        for private in (int(basis[row, count]) % ORDER, -int(basis[row, count]) % ORDER):
            if not 0 < private < ORDER:
                continue
            derived = ec.derive_private_key(private, ec.SECP256K1()).public_key()
            if derived.public_numbers() != public.public_numbers():
                continue
            nonces = [(h + r * private) * pow(s, -1, ORDER) % ORDER
                      for r, s, h in signatures]
            if not all(0 < nonce < BOUND for nonce in nonces):
                raise ValueError("Recovered key does not satisfy every nonce bound")
            cipher = data["flag_ciphertext"]
            key = hashlib.sha256(private.to_bytes(32, "big")).digest()
            plaintext = AESGCM(key).decrypt(
                bytes.fromhex(cipher["nonce_hex"]),
                bytes.fromhex(cipher["ct_hex"]) + bytes.fromhex(cipher["tag_hex"]), None)
            return private, plaintext, len(signatures)
    raise RuntimeError("LLL did not reveal a key matching the supplied public key")


if __name__ == "__main__":
    private, plaintext, checked = solve()
    print(f"Private key: {private:064x}")
    print(f"Verified: {checked} signatures, all nonce bounds, public key and AES-GCM tag")
    print(plaintext.decode("utf-8"))
