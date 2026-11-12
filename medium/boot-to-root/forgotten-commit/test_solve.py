#!/usr/bin/env python3
import unittest
from solve import solve

class TestForgottenCommit(unittest.TestCase):
    def test_solve(self):
        res = solve()
        self.assertEqual(res['author_email'], 'k.vance@ops-shadow-nfx.internal')
        self.assertEqual(res['aws_key'], 'AKIA-NFX-99204811')
        self.assertEqual(res['pgp_fingerprint'], '4F9E-881C-B204-77A1')
        self.assertEqual(res['flag'], 'NFXCTF{g1t_d4ngl1ng_bl0b_h4v0c_5c8a19d4}')

if __name__ == '__main__':
    unittest.main()
