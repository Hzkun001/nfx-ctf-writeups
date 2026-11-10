#!/usr/bin/env python3
"""Inventaris byte/Unicode dan pemetaan dua bit tanpa normalisasi teks."""

import base64
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parent


def xor_bytes(data, key):
    return bytes(value ^ key[i % len(key)] for i, value in enumerate(data))


def try_word_keys(ciphertext, source):
    """Coba kata literal sebagai kunci, tanpa memaksakan prefiks NFX."""
    visible = "".join(char for char in source if unicodedata.category(char) != "Cf")
    words = dict.fromkeys(re.findall(r"[A-Za-z]+", visible))
    candidates = []
    for word in words:
        key = word.encode("ascii")
        plaintext = xor_bytes(ciphertext, key)
        if re.fullmatch(rb"[A-Z][A-Z0-9]{1,12}\{[ -~]{1,200}\}", plaintext):
            assert xor_bytes(plaintext, key) == ciphertext
            candidates.append({"key": word, "plaintext": plaintext.decode("ascii"),
                               "matches_NFX": bool(re.fullmatch(rb"NFX\{.*?\}", plaintext))})
    return len(words), candidates


def main():
    raw = (ROOT / "lirik.txt").read_bytes()
    text = raw.decode("utf-8")
    assert text.encode("utf-8") == raw
    hidden = "".join(char for char in text if unicodedata.category(char) == "Cf")
    symbols = sorted(set(hidden))
    inventory = [{"code_point": f"U+{ord(char):04X}",
                  "name": unicodedata.name(char),
                  "count": count, "utf8_hex": char.encode().hex(" ")}
                 for char, count in sorted(Counter(hidden).items())]
    trailing = []
    hidden_ends = []
    for number, line in enumerate(text.split("\n"), 1):
        whitespace = re.search(r"[ \t]+$", line)
        if whitespace:
            trailing.append({"line": number, "escaped": repr(whitespace.group())})
        suffix = ""
        for char in reversed(line):
            if unicodedata.category(char) != "Cf":
                break
            suffix = char + suffix
        if suffix:
            hidden_ends.append({"line": number, "count": len(suffix),
                                "code_points": [f"U+{ord(char):04X}" for char in suffix]})

    candidates = []
    if len(symbols) == 4 and len(hidden) % 4 == 0:
        for values in itertools.permutations(range(4)):
            mapping = dict(zip(symbols, values))
            bits = "".join(f"{mapping[char]:02b}" for char in hidden)
            encoded = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
            try:
                decoded = base64.b64decode(encoded, validate=True)
            except ValueError:
                continue
            if base64.b64encode(decoded) != encoded:
                continue
            inverse = {f"{value:02b}": char for char, value in mapping.items()}
            assert "".join(inverse[bits[i:i + 2]] for i in range(0, len(bits), 2)) == hidden
            word_count, xor_candidates = try_word_keys(decoded, text)
            for solution in xor_candidates:
                ciphertext = xor_bytes(solution["plaintext"].encode(), solution["key"].encode())
                rebuilt_bits = "".join(f"{value:08b}" for value in base64.b64encode(ciphertext))
                rebuilt_hidden = "".join(inverse[rebuilt_bits[i:i + 2]]
                                         for i in range(0, len(rebuilt_bits), 2))
                assert rebuilt_hidden == hidden
                characters = iter(rebuilt_hidden)
                rebuilt = "".join(next(characters) if unicodedata.category(char) == "Cf"
                                  else char for char in text)
                assert rebuilt.encode("utf-8") == raw
            candidates.append({"mapping": {f"U+{ord(char):04X}": f"{value:02b}"
                                            for char, value in mapping.items()},
                               "bits": bits, "ascii": encoded.decode("ascii"),
                               "base64_decoded_hex": decoded.hex(" "),
                               "base64_decoded_escaped": repr(decoded),
                               "base64_decoded_size": len(decoded),
                               "literal_words_checked": word_count,
                               "word_xor_candidates": xor_candidates,
                               "flags": [match.decode("ascii") for match in
                                         re.findall(rb"NFX\{.*?\}", encoded + b"\n" + decoded)]})
            if len(candidates) == 1:
                (ROOT / "hasil_ascii.txt").write_bytes(encoded)
                (ROOT / "hasil_base64.bin").write_bytes(decoded)
                (ROOT / "bits.txt").write_text(bits, encoding="ascii")

    solutions = [solution for candidate in candidates for solution in candidate["word_xor_candidates"]]
    if len(solutions) == 1:
        (ROOT / "hasil_dekripsi.txt").write_bytes(solutions[0]["plaintext"].encode("ascii"))
    report = {"byte_note": "UTF-8 dari teks chat yang diterima, bukan berkas byte asli sebelum chat.",
              "utf8_bytes": len(raw), "code_points": len(text),
              "sha256_utf8": hashlib.sha256(raw).hexdigest(),
              "lf_count": text.count("\n"), "cr_count": text.count("\r"),
              "tab_count": text.count("\t"), "bom_count": text.count("\ufeff"),
              "hidden_count": len(hidden), "inventory": inventory,
              "hidden_runs": [len(match.group()) for match in
                              re.finditer("[" + "".join(symbols) + "]+", text)] if hidden else [],
              "trailing_ascii_whitespace": trailing, "hidden_at_line_ends": hidden_ends,
              "hidden_sequence": hidden, "two_bit_base64_candidates": candidates,
              "other_nonascii": [{"code_point": f"U+{ord(char):04X}",
                                   "name": unicodedata.name(char), "count": count}
                                  for char, count in Counter(text).items()
                                  if ord(char) > 127 and unicodedata.category(char) != "Cf"]}
    (ROOT / "laporan.json").write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n")
    (ROOT / "urutan_tersembunyi.txt").write_bytes(hidden.encode("utf-8"))
    (ROOT / "urutan_escape.txt").write_bytes(hidden.encode("unicode_escape"))
    rows = ["unicode_index\tutf8_byte_offset\tcode_point\tutf8_hex\tcategory\tname\tescaped"]
    offset = 0
    for index, char in enumerate(text):
        encoded = char.encode()
        rows.append(f"{index}\t{offset}\tU+{ord(char):04X}\t{encoded.hex(' ')}\t"
                    f"{unicodedata.category(char)}\t{unicodedata.name(char, 'CONTROL')}\t"
                    f"{char.encode('unicode_escape').decode('ascii')}")
        offset += len(encoded)
    assert offset == len(raw)
    (ROOT / "codepoints.tsv").write_text("\n".join(rows) + "\n")
    print(f"UTF-8: {len(raw)} byte; Unicode: {len(text)} code point; Cf: {len(hidden)}.")
    for entry in inventory:
        print(entry)
    print("Trailing spaces/tabs:", trailing)
    print("Kandidat Base64 kanonis:", len(candidates))
    for candidate in candidates:
        print("Mapping:", candidate["mapping"])
        print("ASCII:", candidate["ascii"])
        print("Hasil Base64:", candidate["base64_decoded_hex"])
        print("Pola NFX sebelum XOR:", candidate["flags"])
        print("Kata literal sebagai kunci yang diperiksa:", candidate["literal_words_checked"])
        for solution in candidate["word_xor_candidates"]:
            print("Kunci XOR:", solution["key"])
            print("Hasil XOR:", solution["plaintext"])
            print("Sesuai pola NFX{...}:", solution["matches_NFX"])
            print("Verifikasi: seluruh simbol tersembunyi dan byte UTF-8 identik setelah pengodean balik.")


if __name__ == "__main__":
    main()
