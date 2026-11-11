"""Tests for the ECDSA Nonce Bias solver.

Run from this folder:
    python3 -m unittest -v

The lattice recovery test requires fpylll and cryptography (see
requirements.txt) and is skipped when they are unavailable. The input
hash and metadata tests always run.
"""

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(solve)
    HAVE_DEPS = True
except ModuleNotFoundError:
    HAVE_DEPS = False

EXPECTED_FLAG = "NXCTF{ecds4_hnp_n0nc3_b14s_8b1t_l4tt1c3_a3d2ae498097}"
EXPECTED_HASHES = {
    "output.txt": "74f93d9a9c1399cfc2a1e756c273fe476992ad035cb910b5bf370a7823aa73e9",
    "pubkey.pem": "500c7aaa3253086496b618836c14c8bbefe5123c2f857563bdaaf84803360212",
    "challenge.py": "b2df03ad70dd772ef0ddefc44a4cc4bca6461d1f61103e1145b0ab8e64417063",
}


class InputTests(unittest.TestCase):
    def test_asset_hashes(self):
        for name, want in EXPECTED_HASHES.items():
            got = hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()
            self.assertEqual(got, want, name)

    def test_signature_count_and_bias_metadata(self):
        data = json.loads((ASSETS / "output.txt").read_text())
        self.assertEqual(data["curve"], "secp256k1")
        self.assertEqual(len(data["signatures"]), 200)
        for item in data["signatures"]:
            self.assertEqual(item["K_BITS"], 248)
            self.assertEqual(item["top8_k"], 0)

    def test_message_hashes_match(self):
        data = json.loads((ASSETS / "output.txt").read_text())
        for item in data["signatures"][:10]:
            digest = hashlib.sha256(bytes.fromhex(item["msg"])).digest()
            self.assertEqual(int.from_bytes(digest, "big"), int(item["h"], 0))


@unittest.skipUnless(HAVE_DEPS, "fpylll/cryptography not installed")
class LatticeRecoveryTests(unittest.TestCase):
    def test_reproduces_flag(self):
        private, plaintext, checked = solve.solve()
        self.assertEqual(checked, 200)
        self.assertEqual(plaintext.decode(), EXPECTED_FLAG)

    def test_rejects_tampered_input(self):
        target = ASSETS / "output.txt"
        original = target.read_bytes()
        tampered = bytearray(original)
        tampered[200] ^= 0x01
        try:
            target.write_bytes(bytes(tampered))
            with self.assertRaises(ValueError):
                solve.check_inputs()
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
