"""Solver untuk challenge OSINT Tragedi 9/11 (NFX CTF 2026).

Alur:
1. Menemukan pengunggah video r/PublicFreakout: u/PigParkerPt2
2. Menemukan profil GitHub: https://github.com/PigParkerPt2
3. Memeriksa riwayat commit repositori xor-operation
4. Mengekstrak flag dari commit df34505b8a8ce9a97bac2bf57fec359097a0d815 (.env)

Penggunaan:
    python3 solve.py           # memakai patch lokal di assets/commit_df34505.patch
    python3 solve.py --online  # mengambil langsung dari GitHub commit API
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCH_FILE = HERE / "assets" / "commit_df34505.patch"
EXPECTED_SHA256 = "5f3fd8b3fc5aa9cb0545f5d947d0af543a5e16c0df6fd73e43558af400c43f39"
FLAG_PATTERN = re.compile(r"NFX\{[A-Za-z0-9_!@#$%^&*]+\}")

COMMIT_API_URL = "https://api.github.com/repos/PigParkerPt2/xor-operation/commits/df34505b8a8ce9a97bac2bf57fec359097a0d815"
RAW_PATCH_URL = "https://github.com/PigParkerPt2/xor-operation/commit/df34505.patch"


def solve_from_patch(patch_path: Path = PATCH_FILE) -> str:
    """Ekstrak flag dari berkas patch git commit df34505."""
    if not patch_path.exists():
        raise FileNotFoundError(f"Berkas patch tidak ditemukan: {patch_path}")
    content = patch_path.read_text(encoding="utf-8", errors="replace")
    matches = FLAG_PATTERN.findall(content)
    if not matches:
        raise ValueError("Flag tidak ditemukan di dalam berkas patch.")
    return matches[0]


def solve_online() -> str:
    """Ambil langsung data commit dari GitHub API publik."""
    req = urllib.request.Request(
        COMMIT_API_URL,
        headers={"User-Agent": "NFX-CTF-Writeup-Solver/1.0", "Accept": "application/vnd.github.v3+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for file_info in data.get("files", []):
                patch_text = file_info.get("patch", "")
                m = FLAG_PATTERN.search(patch_text)
                if m:
                    return m.group(0)
    except Exception as e:
        sys.stderr.write(f"[!] Gagal mengambil via GitHub API ({e}), mencoba raw patch...\n")
        raw_req = urllib.request.Request(
            RAW_PATCH_URL,
            headers={"User-Agent": "NFX-CTF-Writeup-Solver/1.0"},
        )
        with urllib.request.urlopen(raw_req, timeout=15) as resp:
            raw_text = resp.read().decode("utf-8", errors="replace")
            m = FLAG_PATTERN.search(raw_text)
            if m:
                return m.group(0)

    raise ValueError("Gagal mengambil flag dari GitHub secara online.")


def solve(online: bool = False) -> str:
    if online:
        return solve_online()
    return solve_from_patch()


def main():
    parser = argparse.ArgumentParser(description="Solver Tragedi 9/11 OSINT")
    parser.add_argument("--online", action="store_true", help="Ambil langsung dari remote GitHub")
    args = parser.parse_args()

    flag = solve(online=args.online)
    print(f"[+] Flag berhasil dipulihkan: {flag}")


if __name__ == "__main__":
    main()
