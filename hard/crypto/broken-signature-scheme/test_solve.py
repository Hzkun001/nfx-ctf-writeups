"""Tests for the Broken Signature Scheme solver.

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


class BrokenSignatureSchemeTests(unittest.TestCase):
    def test_reproduces_flag(self):
        plaintext, indices, p, q = solve.solve(solve.DEFAULT_INPUT)
        self.assertEqual(indices, (0, 1, 2))
        self.assertEqual(p * q, int(__import__("json").loads(
            (solve.DEFAULT_INPUT).read_text())["N"], 16))
        self.assertEqual(plaintext, solve.EXPECTED_FLAG)

    def test_leaked_bits_match(self):
        data, modulus, _ = solve.load_output(solve.DEFAULT_INPUT)
        p, q = solve.factor_close_primes(modulus)
        leaked = (p >> data["leak_pos"]) & ((1 << data["leak_bits"]) - 1)
        self.assertEqual(leaked, int(data["leak"], 16))
        self.assertGreater(q - p, 1 << data["delta_bits"])

    def test_rejects_tampered_input(self):
        data = bytearray(solve.DEFAULT_INPUT.read_bytes())
        data[100] ^= 0x01
        tmp = HERE / "_tampered.json"
        tmp.write_bytes(bytes(data))
        try:
            with self.assertRaises(ValueError):
                solve.load_output(tmp)
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
