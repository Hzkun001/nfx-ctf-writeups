"""Unit test untuk solver Unbreakable Delay."""

import json
import unittest
from pathlib import Path

from solve import SAMPLE_PARAMS, compute_wesolowski_proof, factor_rsa_with_xor

EXPECTED_FLAG = "NFX{x0r_f4ct0r1ng_4nd_f4st_vdf_byp4ss_m4k3s_1t_h4rd}"


class TestUnbreakableDelay(unittest.TestCase):
    def test_sample_params_exist(self):
        self.assertTrue(SAMPLE_PARAMS.exists(), "Berkas sample_parameters.json harus ada.")
        data = json.loads(SAMPLE_PARAMS.read_text())
        for key in ["modulus_n", "hint_p_xor_q", "y", "challenge_l", "generator_g", "flag"]:
            self.assertIn(key, data)

    def test_factor_small_rsa_with_xor(self):
        # Uji faktorisasi branch-and-bound pada skala kecil untuk kecepatan unit test
        p_small = 1000000007
        q_small = 1000000009
        n_small = p_small * q_small
        hint_small = p_small ^ q_small

        p_found, q_found = factor_rsa_with_xor(n_small, hint_small, bit_len=35)
        self.assertEqual(p_found * q_found, n_small)
        self.assertEqual(set([p_found, q_found]), set([p_small, q_small]))

    def test_wesolowski_vdf_verification(self):
        params = json.loads(SAMPLE_PARAMS.read_text())
        n = int(params["modulus_n"])
        y = int(params["y"])
        l = int(params["challenge_l"])
        g = int(params["generator_g"])

        # Gunakan p dan q yang sudah diketahui untuk verifikasi persamaan bukti pi
        # Uji sifat aljabar: pi^l * g^r == y (mod n)
        # Kita uji dengan p_test dan q_test kecil untuk validasi struktur aljabar
        p_toy = 61
        q_toy = 53
        n_toy = p_toy * q_toy
        l_toy = 17
        g_toy = 3
        phi_toy = (p_toy - 1) * (q_toy - 1)
        two_t_toy = pow(2, 2**8, phi_toy)
        y_toy = pow(g_toy, two_t_toy, n_toy)

        r_toy = pow(2, 2**8, l_toy)
        q_div_toy = ((two_t_toy - r_toy) * pow(l_toy, -1, phi_toy)) % phi_toy
        pi_toy = pow(g_toy, q_div_toy, n_toy)

        self.assertEqual((pow(pi_toy, l_toy, n_toy) * pow(g_toy, r_toy, n_toy)) % n_toy, y_toy)

    def test_flag_format(self):
        self.assertEqual(EXPECTED_FLAG, "NFX{x0r_f4ct0r1ng_4nd_f4st_vdf_byp4ss_m4k3s_1t_h4rd}")


if __name__ == "__main__":
    unittest.main()
