"""Pengujian solver tanpa mengeksekusi sumber tantangan."""

import ast
from pathlib import Path
import random
import unittest

import solve


class SolverTests(unittest.TestCase):
    def test_inverse_for_arbitrary_plaintexts(self):
        rng = random.Random(12345)
        for _ in range(25):
            plaintext = bytes(rng.randrange(256) for _ in range(42))
            self.assertEqual(solve.decrypt(solve.encrypt(plaintext)), plaintext)

    def test_source_state_roundtrip(self):
        state = solve.read_state(Path(__file__).with_name("chall.py"))
        flag = solve.decrypt(state)
        self.assertTrue(flag.startswith(b"NFX"))
        self.assertTrue(flag.endswith(b"}"))
        self.assertEqual(solve.encrypt(flag), state)

    def test_payload_character_and_ast_rules(self):
        payload = solve.make_payload()
        self.assertLessEqual(len(payload), 1024)
        self.assertFalse(set(payload) & set("0123456789\"'_"))
        banned = (ast.Import, ast.ImportFrom, ast.Lambda, ast.ListComp,
                  ast.SetComp, ast.DictComp, ast.GeneratorExp,
                  ast.FormattedValue, ast.JoinedStr)
        for node in ast.walk(ast.parse(payload, mode="eval")):
            self.assertNotIsInstance(node, banned)
            if isinstance(node, ast.Attribute):
                self.assertFalse(node.attr.startswith("_"))
            if isinstance(node, ast.Call):
                self.assertLessEqual(len(node.args), 2)
                self.assertFalse(node.keywords)

    def test_rotations(self):
        for value in (0, 1, 0x1234, 0xFFFF):
            for shift in range(1, 16):
                self.assertEqual(solve.ror16(solve.rol16(value, shift), shift), value)


if __name__ == "__main__":
    unittest.main()
