#!/usr/bin/env python3
"""Solver lokal Alchemist: balik 32 putaran dan buat formula PyJail."""

import argparse
import ast
from pathlib import Path
import struct
import sys


MASK = 0xFFFF
WORDS = 21
ROUNDS = 32


def read_state(path):
    """Ambil literal state melalui AST; chall.py tidak diimpor/dijalankan."""
    with path.open("rb") as source:
        content = source.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024:
        raise ValueError("Ukuran sumber melebihi 1 MiB.")
    tree = ast.parse(content)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_VAULT_STATE"
            for target in node.targets
        ):
            state = ast.literal_eval(node.value)
            if (isinstance(state, list) and len(state) == WORDS
                    and all(type(value) is int and 0 <= value <= MASK for value in state)):
                return state
            raise ValueError("State harus berupa 21 integer 16 bit.")
    raise ValueError("Literal _VAULT_STATE tidak ditemukan.")


def rol16(value, shift):
    return ((value << shift) | (value >> (16 - shift))) & MASK


def ror16(value, shift):
    return ((value >> shift) | (value << (16 - shift))) & MASK


def encrypt(plaintext):
    """Transformasi maju sebagai pemeriksaan independen hasil pembalikan."""
    if len(plaintext) != WORDS * 2:
        raise ValueError("Panjang plaintext harus 42 byte.")
    words = list(struct.unpack(">21H", plaintext))
    for round_number in range(ROUNDS):
        constant = (round_number * 0x9E37 + 0x7F4A) & MASK
        for index in range(WORDS):
            previous = words[(index - 1) % WORDS]
            shift = (round_number + index) % 15 + 1
            mix = rol16((previous * 257 + constant + index * 17) & MASK, shift)
            words[index] = rol16(((words[index] ^ mix) + constant) & MASK, 5)
        words = [words[(index * 4) % WORDS] for index in range(WORDS)]
    return words


def decrypt(state):
    """Batalkan permutasi, rotasi, penjumlahan, dan XOR dalam urutan terbalik."""
    words = list(state)
    for round_number in reversed(range(ROUNDS)):
        constant = (round_number * 0x9E37 + 0x7F4A) & MASK
        # 4 * 16 = 1 (mod 21), sehingga indeks 16 membatalkan permutasi 4.
        words = [words[(index * 16) % WORDS] for index in range(WORDS)]
        for index in reversed(range(WORDS)):
            # Saat index=0, word terakhir sudah kembali ke nilai awal putaran.
            previous = words[(index - 1) % WORDS]
            shift = (round_number + index) % 15 + 1
            mix = rol16((previous * 257 + constant + index * 17) & MASK, shift)
            words[index] = ((ror16(words[index], 5) - constant) & MASK) ^ mix
    return struct.pack(">21H", *words)


def make_payload():
    """Susun akses globals tanpa angka ASCII, kutip, atau underscore literal."""
    names = "abcdefg"  # Masing-masing bernilai 1, 2, 4, 8, 16, 32, 64.
    assignments = ["a:=True"]
    assignments.extend(f"{current}:={previous}+{previous}"
                       for previous, current in zip(names, names[1:]))
    assignments.append("u:=chr(g+f-a)")

    def number(value):
        return "+".join(name for bit, name in enumerate(names) if value & (1 << bit))

    def text(value):
        return "+".join("u" if char == "_" else f"chr({number(ord(char))})"
                        for char in value)

    lookup = f"getattr(als,{text('__globals__')}).get({text('_VAULT_STATE')})"
    payload = "(" + ",".join(assignments + [lookup]) + ")[-a]"
    if len(payload) > 1024 or any(char in payload for char in "0123456789\"'_"):
        raise ValueError("Payload tidak memenuhi batas karakter/panjang.")
    ast.parse(payload, mode="eval")
    return payload


def save_result(path, data):
    """Hindari menimpa keluaran yang berisi data berbeda."""
    try:
        with path.open("xb") as output:
            output.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError(f"Keluaran sudah berisi data berbeda: {path}")


def main(argv=None):
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=root / "chall.py")
    args = parser.parse_args(argv)
    try:
        state = read_state(args.source)
        plaintext = decrypt(state)
        if encrypt(plaintext) != state:
            raise ValueError("Verifikasi transformasi maju gagal.")
        flag = plaintext.decode("ascii")
        if not flag.startswith("NFX") or not flag.endswith("}"):
            raise ValueError("Plaintext hasil belum sesuai bentuk flag NFX.")
        payload = make_payload()
        save_result(root / "payload.txt", (payload + "\n").encode())
        save_result(root / "flag.txt", plaintext)
    except (OSError, ValueError, SyntaxError) as error:
        print(f"[Kendala] {error}", file=sys.stderr)
        return 1
    print(f"[Flag] {flag}")
    print("[Verifikasi] Transformasi maju 32 putaran identik dengan _VAULT_STATE.")
    print(f"[Payload] {len(payload)} karakter; bebas angka, kutip, dan underscore.")
    print(payload)
    print(f"[Berkas] {root / 'payload.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
