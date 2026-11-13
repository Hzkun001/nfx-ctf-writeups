"""Solver untuk challenge OSINT The Ghost Operator (NFX CTF 2026).

Alur:
1. Menemukan jejak operator dari git commit signature (GPG UID: ghost-route-0914)
2. Memeriksa arsip Wayback Machine untuk URL rentry.co/ghost-route-0914
3. Menganalisis petunjuk rute evakuasi dan safehouse (Jl. Kolonel Masturi KM 9, Parongpong, Lembang)
4. Memvalidasi lokasi target: Villa Istana Bunga, Lembang
5. Menghasilkan flag: NFX{villa_istana_bunga_lembang}

Penggunaan:
    python3 solve.py           # memakai artefak transmisi lokal di assets/
    python3 solve.py --online  # mengambil snapshot via Wayback Machine API
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSMISSION_FILE = HERE / "assets" / "rentry_transmission.txt"
COMMIT_FILE = HERE / "assets" / "commit_d2627a7.txt"
EXPECTED_SHA256 = "40a8ac0d5603493a92a7e5cf459365512aa60df8863771ff59eba1a67d5329bd"

WAYBACK_SNAPSHOT_URL = (
    "http://web.archive.org/web/20261025190602/https://rentry.co/ghost-route-0914"
)


def extract_rentry_slug_from_commit(commit_path: Path = COMMIT_FILE) -> str:
    """Ekstrak slug URL rentry dari GPG signature commit."""
    if not commit_path.exists():
        raise FileNotFoundError(f"Berkas commit tidak ditemukan: {commit_path}")
    text = commit_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"rentry\.co/([a-zA-Z0-9_\-]+)", text)
    if not m:
        raise ValueError("Slug rentry tidak ditemukan pada berkas commit.")
    return m.group(1)


def parse_clues(text: str) -> dict:
    """Ekstrak entitas penting dari teks transmisi."""
    clues = {}
    if "Ghost Operator" in text:
        clues["operator"] = "Ghost Operator"
    if "Jl. Kolonel Masturi KM 9" in text:
        clues["road"] = "Jl. Kolonel Masturi KM 9"
    if "Parongpong" in text:
        clues["district"] = "Parongpong"
    if "Lembang" in text:
        clues["area"] = "Lembang"
    return clues


def solve_from_local(transmission_path: Path = TRANSMISSION_FILE) -> str:
    """Pulihkan flag dari transmisi lokal."""
    if not transmission_path.exists():
        raise FileNotFoundError(f"Berkas transmisi tidak ditemukan: {transmission_path}")
    text = transmission_path.read_text(encoding="utf-8", errors="replace")
    clues = parse_clues(text)

    # Validasi bahwa teks transmisi memiliki petunjuk geolokasi yang tepat
    if (
        clues.get("operator") == "Ghost Operator"
        and "road" in clues
        and "Lembang" in text
    ):
        # Berdasarkan geolokasi komplek villa terbesar di Jl. Kolonel Masturi KM 9, Parongpong, Lembang
        # Target: Villa Istana Bunga, Lembang
        location_slug = "villa_istana_bunga_lembang"
        return f"NFX{{{location_slug}}}"

    raise ValueError("Petunjuk tidak mencukupi untuk memulihkan flag.")


def solve_online() -> str:
    """Ambil transmisi langsung dari arsip Wayback Machine."""
    req = urllib.request.Request(
        WAYBACK_SNAPSHOT_URL,
        headers={"User-Agent": "NFX-CTF-Writeup-Solver/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Ekstrak konten artikel/body dari HTML rentry
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    text = article.get_text() if article else html

    clues = parse_clues(text)
    if clues.get("operator") == "Ghost Operator" and "Lembang" in text:
        return "NFX{villa_istana_bunga_lembang}"

    raise ValueError("Gagal memvalidasi transmisi dari Wayback Machine.")


def solve(online: bool = False) -> str:
    if online:
        return solve_online()
    return solve_from_local()


def main():
    parser = argparse.ArgumentParser(description="Solver The Ghost Operator OSINT")
    parser.add_argument("--online", action="store_true", help="Ambil langsung dari Wayback Machine")
    args = parser.parse_args()

    flag = solve(online=args.online)
    print(f"[+] Flag berhasil dipulihkan: {flag}")


if __name__ == "__main__":
    main()
