#!/usr/bin/env python3
"""Pulihkan tinggi PNG dan dekripsi surat My Lovely Freya."""

import argparse
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import zipfile
import zlib


LIMIT = 16 * 1024 * 1024
# Ditranskripsikan dari tulisan yang muncul setelah tinggi gambar dipulihkan.
PASSWORD = b"<!HayamGoreng45@/>"


def restore_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Signature PNG tidak valid.")
    offset, chunks = 8, []
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        end = offset + size + 12
        if end > len(data):
            raise ValueError("Chunk PNG terpotong.")
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:end - 4]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("CRC chunk PNG tidak sesuai.")
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            break
    if offset != len(data) or not chunks or chunks[-1][0] != b"IEND":
        raise ValueError("Akhir PNG tidak valid.")
    if chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise ValueError("IHDR tidak valid.")
    width, old_height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1])
    if not width or (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError("Solver ini memerlukan RGB 8-bit non-interlaced.")
    compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, LIMIT + 1)
    if len(raw) > LIMIT or not decoder.eof or decoder.unused_data:
        raise ValueError("Data IDAT tidak lengkap atau melebihi batas.")
    stride = 1 + width * 3
    height, remainder = divmod(len(raw), stride)
    if not height or remainder or any(value > 4 for value in raw[::stride]):
        raise ValueError("Ukuran atau filter scanline tidak sesuai.")
    repaired = bytearray(data)
    repaired[20:24] = struct.pack(">I", height)
    repaired[29:33] = struct.pack(">I", zlib.crc32(repaired[12:29]) & 0xFFFFFFFF)
    if repaired[33:] != data[33:]:
        raise ValueError("Data gambar ikut berubah.")
    return bytes(repaired), old_height, height, len(raw)


def decrypt_letter(blob):
    if not blob.startswith(b"Salted__") or len(blob) < 32 or (len(blob) - 16) % 16:
        raise ValueError("Framing surat OpenSSL tidak sesuai.")
    derived = hashlib.pbkdf2_hmac("sha256", PASSWORD, blob[8:16], 100000, 48)
    command = ["openssl", "enc", "-aes-256-cbc", "-nosalt",
               "-K", derived[:32].hex(), "-iv", derived[32:].hex()]
    plaintext = subprocess.run(command + ["-d"], input=blob[16:],
                               capture_output=True, check=True, timeout=10).stdout
    encrypted = subprocess.run(command, input=plaintext, capture_output=True,
                               check=True, timeout=10).stdout
    if encrypted != blob[16:]:
        raise ValueError("Verifikasi enkripsi ulang gagal.")
    if not re.fullmatch(rb"[A-Z][A-Z0-9]{1,12}\{[ -~]+\}\r?\n?", plaintext):
        raise ValueError("Plaintext belum sesuai bentuk flag.")
    return plaintext


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        files = {}
        with zipfile.ZipFile(args.archive) as archive:
            for name in ("freya_sayangkuh.png", "surat_untuk_freya.enc"):
                entry = archive.getinfo(name)
                if entry.file_size > LIMIT:
                    raise ValueError("Anggota arsip terlalu besar.")
                with archive.open(entry) as source:
                    files[name] = source.read(LIMIT + 1)
                if len(files[name]) > LIMIT:
                    raise ValueError("Hasil ekstraksi terlalu besar.")
        png, old, new, size = restore_png(files["freya_sayangkuh.png"])
        letter = decrypt_letter(files["surat_untuk_freya.enc"])
        args.out.mkdir(parents=True, exist_ok=True)
        for name, data in {"freya-restored.png": png, "surat-terbaca.txt": letter}.items():
            path = args.out / name
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"Keluaran berbeda sudah ada: {path}")
            path.write_bytes(data)
        print(f"IDAT: {size} byte; tinggi: {old} -> {new}")
        print("Password dari gambar:", PASSWORD.decode())
        print("Verifikasi enkripsi ulang: identik")
        print("Flag:", letter.decode().rstrip("\r\n"))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, zlib.error,
            subprocess.SubprocessError) as error:
        parser.exit(1, f"Gagal: {error}\n")


if __name__ == "__main__":
    main()
