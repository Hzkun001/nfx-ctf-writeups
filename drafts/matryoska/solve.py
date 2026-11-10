#!/usr/bin/env python3
"""Dekode lapisan capsule.dat dan periksa rekonstruksi berkas asli."""

import argparse
import base64
from pathlib import Path
import sys
import zlib


KEY = b"NFX!"  # Diperoleh dari dugaan awalan NFXCTF{ dan pola kunci empat byte.
LIMIT = 1024 * 1024


def swap_pairs(data):
    if len(data) % 2:
        raise ValueError("Jumlah karakter harus genap untuk pertukaran pasangan.")
    result = bytearray(data)
    result[::2], result[1::2] = data[1::2], data[::2]
    return bytes(result)


def xor_bytes(data):
    return bytes(value ^ KEY[index % len(KEY)] for index, value in enumerate(data))


def decrypt(data):
    compressed = base64.b64decode(swap_pairs(data), validate=True)
    decoder = zlib.decompressobj()
    encoded = decoder.decompress(compressed, LIMIT + 1)
    if len(encoded) > LIMIT or not decoder.eof or decoder.unused_data:
        raise ValueError("Stream ZLIB tidak lengkap atau melampaui batas.")
    return xor_bytes(base64.b85decode(encoded))


def encrypt(plaintext):
    encoded = base64.b85encode(xor_bytes(plaintext))
    return swap_pairs(base64.b64encode(zlib.compress(encoded, 9)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path,
                        default=Path(__file__).with_name("capsule.dat"))
    args = parser.parse_args()
    try:
        with args.input.open("rb") as source:
            data = source.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError("Input melebihi 1 MiB.")
        plaintext = decrypt(data)
        if encrypt(plaintext) != data:
            raise ValueError("Rekonstruksi tidak identik dengan input.")
        print(plaintext.decode("ascii"))
        print("Verifikasi: pengodean balik identik dengan capsule.dat.")
    except (OSError, ValueError, zlib.error) as error:
        print(f"Gagal: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
