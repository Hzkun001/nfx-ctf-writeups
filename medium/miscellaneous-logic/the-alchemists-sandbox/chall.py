#!/usr/bin/env python3
import ast
import sys
import struct

_VAULT_STATE = [29406, 62193, 3550, 51604, 54474, 58556, 5807, 62536, 3004, 10962, 33499, 52037, 51010, 45605, 6009, 18571, 21884, 35367, 29761, 57118, 51549]

def _rol16(v: int, s: int) -> int:
    return ((v << s) & 0xFFFF) | (v >> (16 - s))

def _encrypt_vault(flag_bytes: bytes) -> list:
    assert len(flag_bytes) == 42
    w = list(struct.unpack(">21H", flag_bytes))
    for r in range(32):
        rc = ((r * 0x9E37) + 0x7F4A) & 0xFFFF
        for i in range(21):
            prev = w[(i - 1) % 21]
            mix = _rol16((prev * 257 + rc + i * 17) & 0xFFFF, (r + i) % 15 + 1)
            w[i] = (w[i] ^ mix) & 0xFFFF
            w[i] = _rol16((w[i] + rc) & 0xFFFF, 5)
        w = [w[(i * 4) % 21] for i in range(21)]
    return w

BANNED_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.FormattedValue,
    ast.JoinedStr,
)

def verify_ast(expr_str: str):
    if any(ch in expr_str for ch in "0123456789\"'"):
        raise ValueError("Digits and quotes are forbidden by the Alchemist!")
    if len(expr_str) > 1024:
        raise ValueError("Formula too long!")
    tree = ast.parse(expr_str, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, BANNED_NODES):
            raise ValueError(f"Forbidden AST node: {type(node).__name__}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("Private attributes are forbidden!")
        if isinstance(node, ast.Call) and (len(node.args) > 2 or node.keywords):
            raise ValueError("Calls may take at most 2 positional arguments and no keywords!")
    return compile(tree, "<alchemy>", "eval")

def run_sandbox(expr_str: str):
    code = verify_ast(expr_str)
    safe_env = {"__builtins__": {"getattr": getattr, "chr": chr}, "als": _encrypt_vault}
    return eval(code, safe_env, {})

if __name__ == "__main__":
    print("=== The Alchemist's Sandbox ===")
    try:
        line = input("formula> ").strip()
        res = run_sandbox(line)
        print("Result:", res)
    except Exception as exc:
        print("Transmutation failed:", exc)
