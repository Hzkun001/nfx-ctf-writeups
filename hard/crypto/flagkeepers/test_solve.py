"""Unit test untuk logika matematika GF(2^128) dan solver FlagKeepers."""

import hashlib
import unittest
from pathlib import Path

from solve import ONE, gf_inv, gf_mul, pdeg, pgcd, pmod

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
EXPECTED_SHA256 = "5a4aa4e5d0425fb479283507f049ca4f6a68c20bb6d62def758568dd868104ba"
EXPECTED_FLAG = "NFX{gcm_f0rb1dd3n_4tt4ck_du4l_t4g_c0ll1s10n_m4st3r}"


class TestFlagKeepers(unittest.TestCase):
    def test_asset_hash(self):
        target = ASSETS / "app.py"
        self.assertTrue(target.exists(), "Berkas assets/app.py harus ada.")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SHA256, "Hash SHA256 app.py tidak cocok.")

    def test_gf128_field_identity_and_inverse(self):
        test_val = 0x123456789ABCDEF0123456789ABCDEF0
        # Perkalian dengan identitas ONE harus mengembalikan elemen itu sendiri
        self.assertEqual(gf_mul(test_val, ONE), test_val)
        # Elemen dikali inversnya harus menghasilkan identitas ONE
        inv = gf_inv(test_val)
        self.assertEqual(gf_mul(test_val, inv), ONE)

    def test_polynomial_gcd(self):
        # Bangun dua polinomial yang berbagi akar H_root
        H_root = 0xCAFEBABE112233445566778899AABBCC
        # p_common = (x ^ H_root) -> [H_root, ONE]
        p_common = [H_root, ONE]

        # p1 = p_common * (x ^ R1)
        r1 = 0x11111111222222223333333344444444
        # (x ^ H)(x ^ r1) = x^2 ^ (H^r1)x ^ (H*r1)
        p1 = [gf_mul(H_root, r1), H_root ^ r1, ONE]

        # p2 = p_common * (x ^ R2)
        r2 = 0x55555555666666667777777788888888
        p2 = [gf_mul(H_root, r2), H_root ^ r2, ONE]

        g = pgcd(p1, p2)
        self.assertEqual(pdeg(g), 1)
        # Faktor yang dipulihkan harus cocok dengan H_root
        self.assertEqual(g[0], H_root)

    def test_expected_flag_format(self):
        self.assertTrue(EXPECTED_FLAG.startswith("NFX{"))
        self.assertTrue(EXPECTED_FLAG.endswith("}"))


if __name__ == "__main__":
    unittest.main()
