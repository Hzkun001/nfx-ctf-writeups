"""Tests for the Art Evidence Secret solver.

Run from this folder:
    python3 -m unittest -v
"""

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve)


class ArtEvidenceSecretTests(unittest.TestCase):
    def test_reproduces_flag(self):
        im, info = solve.load_image(solve.DEFAULT_INPUT)
        location = __import__("base64").b64decode(info["PhotoLocation"])
        password = __import__("base64").b64decode(location.split(b", ")[-1])
        red = solve.extract_channel(im, 0)
        blue = solve.extract_channel(im, 2)
        import hashlib
        from Crypto.Cipher import AES

        kek = hashlib.pbkdf2_hmac("sha256", password, red[:16], solve.PBKDF2_ROUNDS, 32)
        key = bytes.fromhex(
            AES.new(kek, AES.MODE_GCM, nonce=red[16:28])
            .decrypt_and_verify(red[28:-16], red[-16:])
            .decode("ascii")
        )
        flag = AES.new(key, AES.MODE_GCM, nonce=blue[:12]).decrypt_and_verify(
            blue[12:-16], blue[-16:]
        )
        self.assertEqual(flag, b"NFX{LSB_3ASY_OR_H4RD_IDK}")

    def test_payload_headers(self):
        im, _ = solve.load_image(solve.DEFAULT_INPUT)
        red = solve.extract_channel(im, 0)
        blue = solve.extract_channel(im, 2)
        self.assertEqual(len(red), 108)
        self.assertEqual(len(blue), 53)

    def test_rejects_tampered_tag(self):
        im, _ = solve.load_image(solve.DEFAULT_INPUT)
        red = bytearray(solve.extract_channel(im, 0))
        red[-1] ^= 0x01
        import hashlib
        from Crypto.Cipher import AES

        kek = hashlib.pbkdf2_hmac("sha256", b"Kukuriuk99", bytes(red[:16]), 200_000, 32)
        with self.assertRaises(ValueError):
            AES.new(kek, AES.MODE_GCM, nonce=bytes(red[16:28])).decrypt_and_verify(
                bytes(red[28:-16]), bytes(red[-16:])
            )


if __name__ == "__main__":
    unittest.main()
