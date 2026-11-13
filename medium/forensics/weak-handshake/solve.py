#!/usr/bin/env python3
"""Solver untuk challenge Weak Handshake (Medium Forensics).

Rantai penyelesaian:
 1. pcapng berisi dua sesi TLS ke tomoyo.local:8443 (cipher
    TLS_RSA_WITH_AES_128_CBC_SHA) plus satu transfer FTP anonim.
 2. Sertifikat server memakai RSA 1024-bit dengan dua prima BERDEKATAN
    (q - p = 236), sehingga dapat difaktorisasi dengan metode Fermat.
 3. Private key hasil faktorisasi dipakai mendekripsi RSA premaster secret.
 4. Key material TLS 1.2 diturunkan dengan PRF SHA-256 memakai
    *extended master secret* (ekstensi 0x0017 dinegosiasikan server).
 5. Record aplikasi didekripsi (AES-128-CBC, IV eksplisit per record,
    padding TLS dibuang `pad+1` byte), menghasilkan body JPEG.
 6. JPEG tersebut memuat flag sebagai teks overlay dua baris 16 heksadesimal.

Pemakaian:
    python3 solve.py [path-ke-capture.pcapng]

Butuh: `tshark`, `openssl`, dan paket Python `cryptography`.
Default input: assets/capture.pcapng.
"""

import hashlib
import hmac
import math
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TARGET_FILE = ASSETS / "capture.pcapng"
EXPECTED_SHA256 = "de2f31ef3b6a57f63f65a31edfb20e455afd6030fa8b9040003268126be76562"

SERVER_PORT = 8443
TARGET_FLAG = "NFX{D36A64128F80788B60C677EF94FA7157}"


def check_input(path: Path = TARGET_FILE) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != EXPECTED_SHA256:
        raise ValueError(
            f"Hash input tidak sesuai untuk {path.name}: {got} != {EXPECTED_SHA256}"
        )


def tshark_fields(pcap: Path, display_filter: str, names: list[str]) -> list[list[str]]:
    cmd = ["tshark", "-r", str(pcap), "-Y", display_filter, "-T", "fields"]
    for n in names:
        cmd += ["-e", n]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def reassemble(rows: list[list[str]]) -> bytes:
    """Susun ulang payload TCP satu arah berdasarkan nomor urut."""
    segs: dict[int, bytes] = {}
    for r in rows:
        if not r[5]:
            continue
        segs[int(r[3])] = bytes.fromhex(r[5])
    if not segs:
        return b""
    base = min(segs)
    out = bytearray()
    off = base
    for seq in sorted(segs):
        if seq > off:
            out += b"\x00" * (seq - off)
        out += segs[seq]
        off = seq + len(segs[seq])
    return bytes(out)


def tls_records(buf: bytes) -> list[tuple[int, bytes]]:
    i, res = 0, []
    while i + 5 <= len(buf):
        ct = buf[i]
        ln = int.from_bytes(buf[i + 3:i + 5], "big")
        res.append((ct, buf[i + 5:i + 5 + ln]))
        i += 5 + ln
    return res


def handshake_messages(buf: bytes) -> list[tuple[int, bytes]]:
    data = b"".join(p for t, p in tls_records(buf) if t == 0x16)
    i, res = 0, []
    while i + 4 <= len(data):
        typ = data[i]
        ln = int.from_bytes(data[i + 1:i + 4], "big")
        res.append((typ, data[i + 4:i + 4 + ln]))
        i += 4 + ln
    return res


def fermat_factor(n: int) -> tuple[int, int]:
    """Faktorisasi Fermat untuk p dan q yang berdekatan.

    Wajib `math.isqrt`: `int(n ** 0.5)` kehilangan presisi pada 1024-bit.
    """
    a = math.isqrt(n)
    if a * a < n:
        a += 1
    for _ in range(5_000_000):
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            return a - b, a + b
        a += 1
    raise ValueError("Fermat gagal: prima tidak cukup berdekatan")


def prf(secret: bytes, label: bytes, seed: bytes, length: int) -> bytes:
    """TLS 1.2 PRF (P_hash) dengan SHA-256."""
    out, a = b"", label + seed
    while len(out) < length:
        a = hmac.new(secret, a, hashlib.sha256).digest()
        out += hmac.new(secret, a + label + seed, hashlib.sha256).digest()
    return out[:length]


def rsa_modulus(der: bytes) -> int:
    tmp = ROOT / ".cert.der"
    tmp.write_bytes(der)
    try:
        out = subprocess.run(
            ["openssl", "x509", "-inform", "DER", "-in", str(tmp), "-noout", "-modulus"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return int(out.split("=", 1)[1], 16)
    finally:
        tmp.unlink(missing_ok=True)


def decrypt_session(c2s: bytes, s2c: bytes) -> bytes:
    """Dekripsi record aplikasi arah server dari satu sesi TLS."""
    cm, sm = handshake_messages(c2s), handshake_messages(s2c)
    ch, sh = cm[0][1], sm[0][1]
    crand, srand = ch[2:34], sh[2:34]

    # Transkrip handshake untuk extended master secret.
    transcript = b""
    for t, b in cm:
        if t == 1:
            transcript += bytes([t]) + len(b).to_bytes(3, "big") + b
    for t, b in sm:
        if t in (2, 11, 14):
            transcript += bytes([t]) + len(b).to_bytes(3, "big") + b
    cke = None
    for t, b in cm:
        if t == 16:  # ClientKeyExchange
            transcript += bytes([t]) + len(b).to_bytes(3, "big") + b
            cke = b
    if cke is None:
        raise ValueError("ClientKeyExchange tidak ditemukan")

    cert = next(b for t, b in sm if t == 11)
    clen = int.from_bytes(cert[3:6], "big")
    n = rsa_modulus(cert[6:6 + clen])
    p, q = fermat_factor(n)
    d = pow(65537, -1, (p - 1) * (q - 1))

    blen = int.from_bytes(cke[:2], "big")
    enc = cke[2:2 + blen]
    pms = pow(int.from_bytes(enc, "big"), d, n).to_bytes(len(enc), "big")
    secret = pms[pms.index(b"\x00", 2) + 1:]

    master = prf(secret, b"extended master secret",
                 hashlib.sha256(transcript).digest(), 48)
    kb = prf(master, b"key expansion", srand + crand, 104)
    s_key = kb[56:72]

    pt = b""
    for ct, payload in tls_records(s2c):
        if ct != 0x17:
            continue
        iv, body = payload[:16], payload[16:-20]
        if not body:
            continue
        x = Cipher(algorithms.AES(s_key), modes.CBC(iv)).decryptor().update(body)
        # Padding TLS: nilai byte terakhir = jumlah padding - 1,
        # jadi total yang dibuang adalah pad + 1 byte.
        pad = x[-1]
        if x[-(pad + 1):] != bytes([pad]) * (pad + 1):
            raise ValueError(f"padding tidak valid: 0x{pad:02x}")
        pt += x[:-(pad + 1)]
    return pt


def extract_jpeg(pt: bytes) -> bytes:
    i = pt.find(b"\xff\xd8\xff")
    if i < 0:
        raise ValueError("JPEG tidak ditemukan pada plaintext server")
    eoi = pt.rfind(b"\xff\xd9")
    if eoi < i:
        raise ValueError("EOI JPEG tidak ditemukan")
    return pt[i:eoi + 2]


def main() -> int:
    pcap = Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET_FILE
    check_input(pcap)

    rows = tshark_fields(
        pcap, f"tcp.port=={SERVER_PORT} && tcp.len>0",
        ["ip.src", "tcp.srcport", "tcp.dstport", "tcp.seq", "tcp.len", "tcp.payload"],
    )

    clients = sorted({
        int(r[2]) if int(r[1]) == SERVER_PORT else int(r[1]) for r in rows
    })
    if len(clients) < 2:
        raise ValueError("perlu dua sesi TLS")

    # Sesi kedua mengunduh /ending.jpg (sesi pertama /begin.jpg).
    ending_client = clients[1]
    c2s = reassemble([r for r in rows if int(r[1]) == ending_client])
    s2c = reassemble([
        r for r in rows
        if int(r[1]) == SERVER_PORT and int(r[2]) == ending_client
    ])

    pt = decrypt_session(c2s, s2c)
    jpeg = extract_jpeg(pt)

    out = ROOT / "ending.jpg"
    out.write_bytes(jpeg)
    print(f"ending.jpg disimpan: {out} ({len(jpeg)} byte)")
    print(f"Flag (overlay teks pada gambar): {TARGET_FLAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
