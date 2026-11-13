"""Reproduce the Bluebird Session forensic recovery from login.keyring.

Usage:
    python3 solve.py [path/to/login.keyring]

Requires PyCryptodome. The default input is assets/login.keyring.
"""

import hashlib
import struct
import sys
from pathlib import Path

from Crypto.Cipher import AES

DEFAULT_INPUT = Path(__file__).resolve().parent / "assets" / "login.keyring"
EXPECTED_SHA256 = "9aa5f380bb318e691f624beb2d20266cee09eb9b173af600e650a8dd623e1ee8"
PASSWORD = "Bluebirds1927!"


def derive_key_and_iv(password: str, salt: bytes, iterations: int):
    """Implement GNOME Keyring egg_symkey_generate_simple key derivation."""
    h = hashlib.sha256(password.encode("utf-8") + salt).digest()
    for _ in range(1, iterations):
        h = hashlib.sha256(h).digest()
    return h[:16], h[16:32]


def parse_and_decrypt_keyring(data: bytes, password: str = PASSWORD):
    """Parse GNOME Keyring v0 binary structure and decrypt item secrets."""
    if not data.startswith(b"GnomeKeyring\n\r\x00\n"):
        raise ValueError("Invalid GNOME Keyring magic header")

    offset = 16 + 4
    nlen = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4 + nlen

    ctime, mtime, flags, lock_timeout, iters = struct.unpack(">QQIII", data[offset:offset + 28])
    offset += 28
    salt = data[offset:offset + 8]
    offset += 8 + 16  # Skip reserved bytes

    num_items = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4

    for _ in range(num_items):
        offset += 8
        num_attrs = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        for _ in range(num_attrs):
            klen = struct.unpack(">I", data[offset:offset + 4])[0]
            offset += 4 + klen
            attr_type = struct.unpack(">I", data[offset:offset + 4])[0]
            offset += 4
            if attr_type == 0:
                vlen = struct.unpack(">I", data[offset:offset + 4])[0]
                offset += 4 + vlen
            else:
                offset += 4

    crypto_size = struct.unpack(">I", data[offset:offset + 4])[0]
    offset += 4
    enc_data = data[offset:offset + crypto_size]

    key, iv = derive_key_and_iv(password, salt, iters)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = cipher.decrypt(enc_data)

    checksum, payload = pt[:16], pt[16:]
    if hashlib.md5(payload).digest() != checksum:
        raise ValueError("MD5 integrity check failed: incorrect password")

    lbl_len = struct.unpack(">I", payload[:4])[0]
    label = payload[4:4 + lbl_len].decode("utf-8", errors="replace")
    p = 4 + lbl_len

    sec_len = struct.unpack(">I", payload[p:p + 4])[0]
    secret = payload[p + 4:p + 4 + sec_len].decode("utf-8", errors="replace")

    return label, secret


def extract_flag(keyring_path: Path = DEFAULT_INPUT, password: str = PASSWORD) -> str:
    data = Path(keyring_path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected input hash: {digest}")

    label, secret = parse_and_decrypt_keyring(data, password)
    
    # Extract the archive password line from the secret note
    archive_pw = None
    for line in secret.splitlines():
        if "for_nozomi.zip password:" in line:
            archive_pw = line.split(":", 1)[1].strip()
            break

    if not archive_pw:
        raise ValueError("Could not find archive password in decrypted secret note")

    return f"NFX{{{archive_pw}}}"


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    try:
        flag = extract_flag(target)
        print(f"[+] Flag: {flag}")
    except Exception as e:
        sys.exit(f"[-] Error: {e}")


if __name__ == "__main__":
    main()
