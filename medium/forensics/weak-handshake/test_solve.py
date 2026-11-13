#!/usr/bin/env python3
"""Unit test untuk solver Weak Handshake."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from solve import (
    EXPECTED_SHA256,
    SERVER_PORT,
    TARGET_FILE,
    TARGET_FLAG,
    check_input,
    extract_jpeg,
    fermat_factor,
    handshake_messages,
    prf,
    reassemble,
    rsa_modulus,
    tls_records,
    tshark_fields,
)

ENDING_SHA256 = "6af3547729d20261bd77d7b9196afab088f7ee0d5e3e272871e94281d36d2575"


def load_session(client_port: int):
    rows = tshark_fields(
        TARGET_FILE, f"tcp.port=={SERVER_PORT} && tcp.len>0",
        ["ip.src", "tcp.srcport", "tcp.dstport", "tcp.seq", "tcp.len", "tcp.payload"],
    )
    c2s = reassemble([r for r in rows if int(r[1]) == client_port])
    s2c = reassemble([
        r for r in rows
        if int(r[1]) == SERVER_PORT and int(r[2]) == client_port
    ])
    return c2s, s2c


class TestWeakHandshake(unittest.TestCase):
    def test_input_sha256(self):
        """Berkas pcap harus utuh sesuai hash yang dicatat."""
        got = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()
        self.assertEqual(got, EXPECTED_SHA256)

    def test_dua_sesi_tls(self):
        """Harus ada dua port klien berbeda (sesi begin & ending)."""
        rows = tshark_fields(
            TARGET_FILE, f"tcp.port=={SERVER_PORT} && tcp.len>0",
            ["ip.src", "tcp.srcport", "tcp.dstport", "tcp.seq", "tcp.len", "tcp.payload"],
        )
        clients = sorted({
            int(r[2]) if int(r[1]) == SERVER_PORT else int(r[1]) for r in rows
        })
        self.assertEqual(len(clients), 2)

    def test_sertifikat_rsa_1024_prima_berdekatan(self):
        """Sertifikat memakai RSA 1024-bit dengan q - p = 236 (lemah)."""
        _, s2c = load_session(56422)
        cert = next(b for t, b in handshake_messages(s2c) if t == 11)
        clen = int.from_bytes(cert[3:6], "big")
        n = rsa_modulus(cert[6:6 + clen])
        self.assertEqual(n.bit_length(), 1024)

        p, q = fermat_factor(n)
        self.assertEqual(p * q, n)
        self.assertEqual(q - p, 236)
        self.assertEqual(p.bit_length(), 512)

    def test_cipher_suite_dan_ems(self):
        """ServerHello: cipher 0x002f dan ekstensi 0x0017 (extended master secret)."""
        _, s2c = load_session(56422)
        sh = handshake_messages(s2c)[0][1]
        off = 35 + sh[34]
        self.assertEqual(int.from_bytes(sh[off:off + 2], "big"), 0x002F)

        ext_len = int.from_bytes(sh[off + 3:off + 5], "big")
        ext = sh[off + 5:off + 5 + ext_len]
        types, i = [], 0
        while i + 4 <= len(ext):
            types.append(int.from_bytes(ext[i:i + 2], "big"))
            i += 4 + int.from_bytes(ext[i + 2:i + 4], "big")
        self.assertIn(0x0017, types)

    def test_prf_sha256(self):
        """PRF TLS 1.2 SHA-256 harus deterministik dan berlabel."""
        a = prf(b"secret", b"label", b"seed", 48)
        b = prf(b"secret", b"label", b"seed", 48)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 48)
        self.assertNotEqual(a, prf(b"secret", b"other", b"seed", 48))

    def test_reproduksi_gambar_identik(self):
        """Dekripsi harus menghasilkan JPEG yang identik byte-per-byte."""
        from solve import decrypt_session, extract_jpeg

        c2s, s2c = load_session(56422)
        jpeg = extract_jpeg(decrypt_session(c2s, s2c))
        self.assertEqual(len(jpeg), 323692)
        self.assertEqual(hashlib.sha256(jpeg).hexdigest(), ENDING_SHA256)
        self.assertTrue(jpeg.startswith(b"\xff\xd8\xff"))
        self.assertTrue(jpeg.endswith(b"\xff\xd9"))

    def test_flag_konstan(self):
        self.assertEqual(TARGET_FLAG, "NFX{D36A64128F80788B60C677EF94FA7157}")

    def test_tolak_input_berubah(self):
        """Input yang dimodifikasi harus ditolak oleh pemeriksaan hash."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "capture.pcapng"
            fake.write_bytes(b"bukan pcap asli")
            with self.assertRaises(ValueError):
                check_input(fake)


if __name__ == "__main__":
    unittest.main()
