#!/usr/bin/env python3
"""Pulihkan PDF repeating-key XOR dan cari flag NFX, tanpa paket tambahan."""

import argparse
import base64
from collections import Counter
import math
from pathlib import Path
import re
import sys
from urllib.request import urlopen
import zlib


URL = ("https://raw.githubusercontent.com/NFCC-Com/qazwsx/refs/heads/main/"
       "crypto/Dokodemo_Door/rahasia.pdf")
MAX_FILE = 16 * 1024 * 1024
MAX_STREAM = 32 * 1024 * 1024
KEY_LENGTHS = range(4, 33)
FLAG_PATTERN = re.compile(rb"NFX\{.*?\}", re.DOTALL)


def read_input(path):
    """Baca input lokal, atau unduh lampiran soal bila belum tersedia."""
    if not path.exists():
        print(f"[Unduh] Menyimpan lampiran ke {str(path)!r}...")
        with urlopen(URL, timeout=30) as response:
            data = response.read(MAX_FILE + 1)
        if len(data) > MAX_FILE:
            raise ValueError("Lampiran melebihi batas 16 MiB.")
        with path.open("xb") as output:
            output.write(data)
    with path.open("rb") as source:
        data = source.read(MAX_FILE + 1)
    if not 64 <= len(data) <= MAX_FILE:
        raise ValueError("Ukuran input harus antara 64 byte dan 16 MiB.")
    return data


def xor_bytes(data, key):
    """XOR simetris: fungsi yang sama dapat mengenkripsi atau mendekripsi."""
    return bytes(value ^ key[i % len(key)] for i, value in enumerate(data))


def shortest_key(key):
    """Kunci ABCDABCD dilaporkan sebagai ABCD."""
    for length in range(1, len(key) + 1):
        if len(key) % length == 0 and key == key[:length] * (len(key) // length):
            return key[:length]


def pdf_objects(data):
    """Validasi header, EOF, startxref, dan offset objek pada xref klasik."""
    if not re.match(rb"%PDF-(?:1\.[0-7]|2\.0)(?:\r\n|\r|\n)", data):
        raise ValueError("Header PDF tidak valid.")
    trailer = re.search(rb"startxref\s+(\d+)\s+%%EOF[ \t\r\n]*\Z", data)
    if trailer is None:
        raise ValueError("Marker startxref/%%EOF tidak valid.")
    xref = int(trailer.group(1))
    if not data.startswith(b"xref", xref):
        raise ValueError("Tabel xref klasik tidak ditemukan pada offset yang tercatat.")
    lines = data[xref:].splitlines()
    position = 1
    offsets = {}
    while position < len(lines) and lines[position].strip() != b"trailer":
        section = re.fullmatch(rb"(\d+)\s+(\d+)", lines[position].strip())
        if section is None:
            raise ValueError("Subbagian xref tidak valid.")
        first, count = map(int, section.groups())
        position += 1
        if count > len(lines) - position:
            raise ValueError("Jumlah entri xref tidak sesuai.")
        for number in range(first, first + count):
            entry = re.fullmatch(rb"(\d{10}) (\d{5}) ([nf])", lines[position].strip())
            position += 1
            if entry is None:
                raise ValueError("Entri xref tidak valid.")
            if entry.group(3) == b"f":
                continue
            offset, generation = map(int, entry.groups()[:2])
            expected = f"{number} {generation} obj".encode()
            if not 0 <= offset < xref or not data.startswith(expected, offset):
                raise ValueError("Offset objek PDF tidak sesuai tabel xref.")
            offsets[(number, generation)] = offset
    if not offsets or position >= len(lines):
        raise ValueError("Tabel xref kosong atau tidak lengkap.")
    ordered = sorted(offsets, key=offsets.get)
    ends = [offsets[key] for key in ordered[1:]] + [xref]
    objects = {key: data[offsets[key]:end] for key, end in zip(ordered, ends)}
    if not any(re.search(rb"/Type\s*/Catalog\b", obj) for obj in objects.values()):
        raise ValueError("Objek Catalog PDF tidak ditemukan.")
    return objects


def key_candidates(ciphertext):
    """Gabungkan statistik kolom, known plaintext header, dan variasi EOF."""
    weights = [-12.0] * 256
    for value in range(32, 127):
        weights[value] = 1.0
    for value in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        weights[value] = 2.0
    for value in b" ()/<>[]%":
        weights[value] = 2.5
    weights[32], weights[10], weights[13], weights[9] = 4.0, 4.0, 3.0, 1.0
    headers = [b"%PDF-1." + str(version).encode() for version in range(8)] + [b"%PDF-2.0"]
    endings = (b"%%EOF\n", b"%%EOF\r\n", b"%%EOF", b"%%EOF\r", b"")
    ranked = {}
    for length in KEY_LENGTHS:
        columns = [Counter(ciphertext[i::length]) for i in range(length)]
        scores = [[sum(count * weights[value ^ key] for value, count in column.items())
                   for key in range(256)] for column in columns]
        best = [max(range(256), key=column.__getitem__) for column in scores]
        for header in headers:
            for ending in endings:
                known = list(enumerate(header))
                known.extend(enumerate(ending, start=len(ciphertext) - len(ending)))
                fixed = {}
                for offset, plain_byte in known:
                    slot = offset % length
                    key_byte = ciphertext[offset] ^ plain_byte
                    if slot in fixed and fixed[slot] != key_byte:
                        break
                    fixed[slot] = key_byte
                else:
                    key = bytes(fixed.get(i, best[i]) for i in range(length))
                    score = sum(scores[i][key[i]] for i in range(length)) / len(ciphertext)
                    key = shortest_key(key)
                    # Penalti mencegah kunci panjang menang hanya karena cocok berlebihan.
                    score -= len(key) * math.log2(len(ciphertext)) / len(ciphertext)
                    ranked[key] = max(score, ranked.get(key, -math.inf))
    return sorted(ranked, key=ranked.get, reverse=True)


def recover_pdf(ciphertext):
    """Pilih kunci berdasarkan struktur PDF, bukan kecocokan header saja."""
    for key in key_candidates(ciphertext):
        plain = xor_bytes(ciphertext, key)
        try:
            objects = pdf_objects(plain)
        except ValueError:
            continue
        return key, plain, objects
    raise ValueError(
        "Belum ditemukan kunci yang menghasilkan PDF valid. "
        "Metode statistik ini memakai panjang kunci 4-32 byte dan PDF dengan xref klasik."
    )


def inflate(data):
    """Dekompresi Flate dengan pemeriksaan checksum dan batas hasil."""
    decoder = zlib.decompressobj()
    result = decoder.decompress(data, MAX_STREAM + 1)
    if len(result) > MAX_STREAM:
        raise ValueError("Hasil dekompresi stream melebihi batas 32 MiB.")
    if not decoder.eof or decoder.unused_data.strip(b"\r\n\t "):
        raise ValueError("Stream Flate tidak lengkap atau memiliki data tambahan.")
    return result


def find_flags(pdf, objects):
    """Cari pada PDF mentah dan setiap tahap stream ASCII85/Flate."""
    flags = set(FLAG_PATTERN.findall(pdf))
    for obj in objects.values():
        marker = re.search(rb"\bstream(?:\r\n|\r|\n)", obj)
        if marker is None:
            continue
        metadata = obj[:marker.start()]
        length = re.search(rb"/Length\s+(\d+)(?:\s+(\d+)\s+R)?", metadata)
        if length is None:
            continue
        size = int(length.group(1))
        if length.group(2) is not None:
            reference = objects.get((size, int(length.group(2))), b"")
            value = re.fullmatch(rb"\d+\s+\d+\s+obj\s+(\d+)\s+endobj\s*", reference)
            if value is None:
                raise ValueError("Referensi panjang stream tidak dapat dibaca.")
            size = int(value.group(1))
        begin = marker.end()
        if size > len(obj) - begin:
            raise ValueError("Panjang stream melampaui ukuran objek.")
        payload = obj[begin:begin + size]
        filters = re.search(rb"/Filter\s*(\[[^\]]*\]|/\w+)", metadata)
        names = re.findall(rb"/(\w+)", filters.group(1)) if filters else []
        flags.update(FLAG_PATTERN.findall(payload))
        for name in names:
            if name in (b"ASCII85Decode", b"A85"):
                payload = base64.a85decode(payload, adobe=payload.rstrip().endswith(b"~>"))
            elif name in (b"FlateDecode", b"Fl"):
                payload = inflate(payload)
            else:
                # shortcut: filter gambar tidak menjadi teks, gunakan OCR jika flag berupa gambar.
                break
            flags.update(FLAG_PATTERN.findall(payload))
    return sorted(flags)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=Path("rahasia.pdf"))
    parser.add_argument("-o", "--output", type=Path, default=Path("hasil_rahasia.pdf"))
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input dan hasil harus memakai nama berbeda.")
        ciphertext = read_input(args.input)
        print(f"[Analisis] Memeriksa {len(ciphertext):,} byte, panjang kunci 4-32...")
        key, pdf, objects = recover_pdf(ciphertext)
        print(f"[Kunci] Panjang: {len(key)} byte; nilai: {key!r}; hex: {key.hex()}")
        assert xor_bytes(pdf, key) == ciphertext
        try:
            with args.output.open("xb") as output:
                output.write(pdf)
        except FileExistsError:
            if args.output.read_bytes() != pdf:
                raise ValueError("Keluaran sudah berisi file lain. Pilih nama lain dengan -o.")
        print(f"[PDF] Header, EOF, dan offset objek valid. Disimpan: {str(args.output)!r}")
        flags = find_flags(pdf, objects)
        if not flags:
            print("[Informasi] PDF dipulihkan, tetapi pola NFX{...} belum ditemukan.")
            return 2
        for flag in flags:
            print(f"[Flag] {flag.decode('utf-8')}")
        return 0
    except (OSError, ValueError, zlib.error) as error:
        print(f"[Kendala] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
