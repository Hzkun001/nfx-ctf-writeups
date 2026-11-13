"""Tests for the Cihuy LWE solver.

Run from this folder:
    python3 -m unittest -v

The lattice recovery test requires fpylll (see requirements.txt) and is skipped
when it is unavailable. The input hash and metadata tests always run.
"""

import ast
import hashlib
import importlib.util
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

EXPECTED_FLAG = "NFXCTF{l4tt1c3_sm4ll_s3cr3t_LWE_7e2a0195}"
EXPECTED_HASHES = {
    "lwe.py": "6a996ad10f8ee04aed2f3befe3f1268b2b4bff8c9d6c6740b2cd88db0a623e1c",
}


class InputTests(unittest.TestCase):
    def test_asset_hashes(self):
        for name, want in EXPECTED_HASHES.items():
            got = hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()
            self.assertEqual(got, want, name)

    def test_challenge_parameters(self):
        target = ASSETS / "lwe.py"
        data = {}
        for node in ast.parse(target.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                data[node.targets[0].id] = ast.literal_eval(node.value)

        self.assertEqual(data["q"], 257)
        self.assertEqual(data["n"], 40)
        self.assertEqual(data["m"], 64)
        self.assertEqual(len(data["A"]), 64)
        self.assertTrue(all(len(row) == 40 for row in data["A"]))
        self.assertEqual(len(data["b"]), 64)
        self.assertEqual(len(bytes.fromhex(data["ct"])), 41)


@unittest.skipUnless(HAVE_DEPS, "fpylll not installed")
class LatticeRecoveryTests(unittest.TestCase):
    def test_reproduces_flag(self):
        secret, flag = solve.solve()
        self.assertEqual(flag, EXPECTED_FLAG)
        self.assertEqual(len(secret), 40)
        self.assertTrue(all(x in (-1, 0, 1) for x in secret))
        self.assertEqual(sum(x * x for x in secret), 25)

    def test_rejects_tampered_input(self):
        target = ASSETS / "lwe.py"
        original = target.read_bytes()
        tampered = bytearray(original)
        tampered[100] ^= 0x01
        try:
            target.write_bytes(bytes(tampered))
            with self.assertRaises(ValueError):
                solve.check_inputs()
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
