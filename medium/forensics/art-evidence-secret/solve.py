"""Reproduce the Art Evidence Secret solve from the original PNG.

Usage:
    python3 solve.py [path/to/original.png]

Requires Pillow and PyCryptodome. The default input is assets/original.png.
"""

import base64
import hashlib
import re
import sys
from pathlib import Path

from PIL import Image
from Crypto.Cipher import AES

DEFAULT_INPUT = Path(__file__).resolve().parent / "assets" / "original.png"
EXPECTED_SHA256 = "1d349bbff6ba8f9bfd85fbf6980d098b5d810035395f3477d463526b11b2c4a1"
PBKDF2_ROUNDS = 200_000


def load_image(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected input hash: {digest}")
    with Image.open(path) as im:
        if im.mode != "RGB":
            raise ValueError("Expected the original RGB image")
        # Copy pixel data so the file handle can be closed.
        return im.copy(), dict(im.info)


def extract_channel(im, channel):
    """Read one LSB bitstream, MSB-first, in row-major pixel order."""
    width, height = im.size
    pixels = im.load()
    cursor = 0

    def read(count):
        nonlocal cursor
        out = bytearray()
        for _ in range(count):
            value = 0
            for _ in range(8):
                if cursor >= width * height:
                    raise ValueError("Payload exceeds image capacity")
                value = (value << 1) | (pixels[cursor % width, cursor // width][channel] & 1)
                cursor += 1
            out.append(value)
        return bytes(out)

    header = read(8)
    if header[:4] != b"CTF1":
        raise ValueError(f"Unexpected payload header: {header[:4]!r}")
    size = int.from_bytes(header[4:], "big")
    if 8 * (size + 8) > width * height:
        raise ValueError("Declared payload length exceeds image capacity")
    return read(size)


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_INPUT
    im, info = load_image(path)

    # The metadata password is a Base64 field inside the PhotoLocation string.
    location = base64.b64decode(info["PhotoLocation"], validate=True)
    password = base64.b64decode(location.split(b", ")[-1], validate=True)

    red = extract_channel(im, 0)
    blue = extract_channel(im, 2)

    # red: salt(16) + nonce(12) + ciphertext(64) + tag(16)
    kek = hashlib.pbkdf2_hmac("sha256", password, red[:16], PBKDF2_ROUNDS, 32)
    key_hex = AES.new(kek, AES.MODE_GCM, nonce=red[16:28]).decrypt_and_verify(
        red[28:-16], red[-16:]
    )

    # blue: nonce(12) + ciphertext(25) + tag(16)
    key = bytes.fromhex(key_hex.decode("ascii"))
    flag = AES.new(key, AES.MODE_GCM, nonce=blue[:12]).decrypt_and_verify(
        blue[12:-16], blue[-16:]
    )

    if not re.fullmatch(rb"NFX\{[ -~]+\}", flag):
        raise ValueError(f"Unexpected flag format: {flag!r}")
    print(flag.decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
