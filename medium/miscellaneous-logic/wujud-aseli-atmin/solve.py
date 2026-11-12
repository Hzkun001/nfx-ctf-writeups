#!/usr/bin/env python3
"""Solver untuk challenge Wujud Aseli Atmin (Forensics - NFX CTF).

Alur:
1. Membaca berkas gambar assets/dokumentasi.png.
2. Mengekstrak arsip ZIP yang disisipkan setelah penanda chunk IEND.
3. Memperbaiki header berkas scan_07.dat (PNG dengan magic bytes rusak).
4. Mengekstrak LSB pada kanal merah (R) dari gambar hasil perbaikan.
5. Menemukan payload Base64 dan mendekode flag NFX{...}.
"""

from __future__ import annotations

import base64
import io
import re
import sys
import zipfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
INPUT_IMAGE = ASSETS / "dokumentasi.png"


def extract_zip(data: bytes) -> zipfile.ZipFile:
    zip_start = data.find(b"PK\x03\x04")
    if zip_start == -1:
        raise ValueError("Penanda ZIP PK\\x03\\x04 tidak ditemukan dalam berkas.")
    return zipfile.ZipFile(io.BytesIO(data[zip_start:]))


def fix_png_header(dat_bytes: bytes) -> bytes:
    # Magic PNG 8 byte + 4 byte chunk length IHDR (0x0000000d)
    png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D])
    return png_header + dat_bytes[12:]


def extract_red_lsb(img: Image.Image) -> bytes:
    pixels = img.load()
    w, h = img.size
    bits: list[int] = []
    for y in range(h):
        for x in range(w):
            r, _, _ = pixels[x, y][:3]
            bits.append(r & 1)

    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i : i + 8]:
            byte = (byte << 1) | b
        out.append(byte)
    return bytes(out)


def solve(image_path: Path = INPUT_IMAGE) -> str:
    data = image_path.read_bytes()
    zf = extract_zip(data)

    if "scan_07.dat" not in zf.namelist():
        raise ValueError("scan_07.dat tidak ditemukan dalam arsip ZIP.")

    raw_dat = zf.read("scan_07.dat")
    fixed_png = fix_png_header(raw_dat)

    img = Image.open(io.BytesIO(fixed_png))
    extracted = extract_red_lsb(img)

    match = re.search(rb"[A-Za-z0-9+/]{20,}={0,2}", extracted)
    if not match:
        raise ValueError("Payload Base64 tidak ditemukan dalam LSB kanal merah.")

    flag = base64.b64decode(match.group(0)).decode("utf-8", errors="ignore").strip()
    return flag


def main() -> None:
    flag = solve()
    print(f"[+] Flag berhasil ditemukan: {flag}")


if __name__ == "__main__":
    main()
