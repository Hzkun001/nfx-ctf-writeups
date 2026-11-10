"""Decode the Black Box Protocol N4T0 workbook with the Python standard library.

Usage:
    python3 solve.py [path/to/flight_recovery_manifest.xlsx]

Never open the workbook in Excel/LibreOffice: read the ZIP/XML directly.
"""

import struct
import sys
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DEFAULT_INPUT = Path(__file__).resolve().parent / "assets" / "flight_recovery_manifest.xlsx"
EXPECTED_SHA256 = "afeb670e8f99e98968d8d1d14db12f267ac2b639ae47ce4602992bfe76518b3b"

NATO = {
    "November": "N", "Tango": "T", "Papa": "P", "Hotel": "H", "Charlie": "C",
    "Four": "4", "Zero": "0", "Three": "3", "One": "1",
}
EXPECTED_MASK = "XXX{X0X0_XX0X0X0X_0X0_X0xxX_X0X_xx0Xx_x0x0xx}"


def load_workbook(path):
    import hashlib

    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected input hash: {digest}")
    with zipfile.ZipFile(path) as z:
        strings = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = [
            "".join(t.text or "" for t in si.findall(".//m:t", NS))
            for si in strings.findall("m:si", NS)
        ]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    return shared, sheet


def read_columns(shared, sheet):
    cols = {"A": [], "B": [], "C": []}
    for row in sheet.findall("m:sheetData/m:row", NS):
        if row.attrib.get("r") == "1":
            continue
        for cell in row.findall("m:c", NS):
            raw = cell.findtext("m:v", namespaces=NS)
            if raw is None:
                continue
            value = shared[int(raw)] if cell.attrib.get("t") == "s" else raw
            if value == "null":
                continue
            col = cell.attrib["r"].rstrip("0123456789")
            cols[col].append((cell.attrib["r"], value, cell.attrib.get("t")))
    return cols


def decode(shared, sheet):
    cols = read_columns(shared, sheet)

    # Column A: NATO phonetic initials and English digit words.
    a = "".join(NATO[value] for _, value, _ in cols["A"])
    if len(a) != 15 or len(cols["A"]) != 15:
        raise ValueError("Column A does not have the expected 15 entries")

    # Column B: hexadecimal ASCII. Some cells store hex text, others store the
    # hex value as a number (e.g. "43.0"), so normalize through Decimal.
    b = "".join(
        chr(int(value if typ == "s" else str(int(Decimal(value))), 16))
        for _, value, typ in cols["B"]
    )

    # Column C: each number is an IEEE754 float32 whose big-endian bytes are
    # ASCII. Decimal truncation is below float32 half-ULP, so packing as
    # float32 restores all original 32 bits.
    chunks = []
    for address, value, _ in cols["C"]:
        packed = struct.pack(">f", float(value))
        restored = struct.unpack(">f", packed)[0]
        if abs(restored - float(value)) > abs(restored) * 1e-12:
            raise ValueError(f"{address}: float32 round-trip error too large")
        chunks.append(packed.decode("ascii"))
    c = "".join(chunks)

    flag = "NFX{" + "_".join([a[:4], a[4:12], a[12:]]) + "_" + b + c + "}"
    mask = "".join(
        "0" if ch.isdigit() else "X" if ch.isupper() else "x" if ch.islower() else ch
        for ch in flag
    )
    if mask != EXPECTED_MASK:
        raise ValueError(f"Flag does not match the supplied mask: {mask}")
    return flag, a, b, c


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_INPUT
    shared, sheet = load_workbook(path)
    flag, a, b, c = decode(shared, sheet)
    print("A:", a)
    print("B:", b)
    print("C:", c)
    print(flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
