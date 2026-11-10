"""Tes regresi lapisan XOR dan prefiks flag tanpa menebak isi plaintext."""

import base64
from pathlib import Path
import unittest

import periksa_unicode as app


class WordXorTests(unittest.TestCase):
    def test_supplied_payload_and_actual_prefix(self):
        ciphertext = base64.b64decode(
            b"KDkvOC8VFBJVFTMeXxMOPgFfNl8JORUEXzYKUxQKEQ==", validate=True)
        source = Path(__file__).with_name("lirik.txt").read_text()
        count, candidates = app.try_word_keys(ciphertext, source)
        self.assertEqual(count, 26)
        self.assertEqual(candidates, [{
            "key": "falling",
            "plaintext": "NXCTF{st4y_w1th_m3_1n_th3_d4rk}",
            "matches_NFX": False,
        }])

    def test_requested_prefix_remains_supported(self):
        plaintext = b"NFX{uji_byte}"
        key = b"arsip"
        ciphertext = bytes(c ^ key[i % len(key)] for i, c in enumerate(plaintext))
        _, candidates = app.try_word_keys(ciphertext, "Data arsip kantor")
        self.assertEqual(candidates, [{"key": "arsip", "plaintext": plaintext.decode(),
                                       "matches_NFX": True}])

    def test_wrong_literal_keys_do_not_produce_a_flag(self):
        ciphertext = base64.b64decode(b"KDkvOC8VFBJVFTMeXxMOPgFfNl8JORUEXzYKUxQKEQ==")
        _, candidates = app.try_word_keys(ciphertext, "alpha beta gamma")
        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
