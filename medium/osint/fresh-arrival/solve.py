#!/usr/bin/env python3
"""
Challenge: Fresh Arrival
Kategori : OSINT
Difficulty: Medium
Author   : ariaf

Deskripsi komponen flag:
Format flag: NFX{IATA_ICAO_kota_namadepan}
- IATA maskapai operator pertama: XW (China Xinhua Airlines)
- ICAO maskapai operator pertama: CXH (China Xinhua Airlines)
- Kota markas maskapai          : beijing (Beijing, China)
- Nama depan fotografer asli    : raihan (Raihan Al Faris via JetPhotos #11925184)
"""

import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
SPOTTED_IMAGE = ASSETS / "spotted.jpg"
EXPECTED_SHA256 = "1b74fef0e79aae45c0a5adc275124f2b996b67547f1a39180451ce9750cf4600"

FLAG_PATTERN = re.compile(r"^NFX\{[A-Z0-9]+_[A-Z0-9]+_[a-z0-9]+_[a-z0-9]+\}$")


def solve(
    iata: str = "XW",
    icao: str = "CXH",
    city: str = "beijing",
    photographer_first_name: str = "raihan",
) -> str:
    """Menyusun flag dari komponen investigasi OSINT."""
    flag = f"NFX{{{iata.upper()}_{icao.upper()}_{city.lower()}_{photographer_first_name.lower()}}}"
    if not FLAG_PATTERN.match(flag):
        raise ValueError(f"Format flag tidak valid: {flag}")
    return flag


if __name__ == "__main__":
    recovered_flag = solve()
    print(f"[+] Recovered Flag: {recovered_flag}")
