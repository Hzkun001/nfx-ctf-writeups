#!/usr/bin/env python3
import os
import unittest
from solve import recover_subkeys, decrypt_ciphertext

class TestFeistelDifferential(unittest.TestCase):
    def test_solve(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, 'assets')
        pairs_file = os.path.join(assets_dir, 'pairs.txt')
        flag_file = os.path.join(assets_dir, 'flag.enc')

        subkeys = recover_subkeys(pairs_file)
        expected_subkeys = [0xa383, 0x3ab5, 0xd728, 0x7222, 0x9737, 0x7212, 0xfdec]
        self.assertEqual(subkeys, expected_subkeys)

        flag = decrypt_ciphertext(subkeys, flag_file)
        self.assertEqual(flag, "NFXCTF{d1ff3r3nt14l_crypt0_pwn5_f31st3l_45322835}")

if __name__ == '__main__':
    unittest.main()
