"""Uji sampel, invers lapisan, dan penolakan input rusak."""

from pathlib import Path
import unittest
import zlib

import solve


class CapsuleTests(unittest.TestCase):
    def test_supplied_capsule(self):
        data = Path(__file__).with_name("capsule.dat").read_bytes()
        plaintext = solve.decrypt(data)
        self.assertEqual(plaintext, b"NFXCTF{m4try0shk4_0n10n_p33l3d_c309b71e}")
        self.assertEqual(solve.encrypt(plaintext), data)

    def test_roundtrip_arbitrary_bytes(self):
        for data in (b"", bytes(range(256)), b"NFX{contoh}"):
            with self.subTest(size=len(data)):
                self.assertEqual(solve.decrypt(solve.encrypt(data)), data)

    def test_invalid_input(self):
        for data in (b"x", b"not-an-archive!!", b"QUJD"):
            with self.subTest(data=data), self.assertRaises((ValueError, zlib.error)):
                solve.decrypt(data)


if __name__ == "__main__":
    unittest.main()
