"""Pengujian offline: python3 -m unittest -v."""

import base64
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

import solve_rahasia as app


def make_pdf(flag=b"NFX{uji_otomatis}", compressed=False, ending=b"\n"):
    content = (b"BT (Dokumen administrasi dengan angka 1234567890 dan catatan arsip) Tj ET\n" * 70
               + b"BT (" + flag + b") Tj ET\n")
    filters = b""
    if compressed:
        content = base64.a85encode(zlib.compress(content), adobe=True)
        filters = b"/Filter [/ASCII85Decode /FlateDecode] "
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>",
               b"<< " + filters + b"/Length " + str(len(content)).encode()
               + b" >>\nstream\n" + content + b"\nendstream"]
    pdf = b"%PDF-1.4\n%\x93\x8c\x8b\x9e\n"
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    startxref = len(pdf)
    pdf += b"xref\n0 5\n0000000000 65535 f \n"
    pdf += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    pdf += (b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n"
            + str(startxref).encode() + b"\n%%EOF" + ending)
    return pdf


class SolverTests(unittest.TestCase):
    def test_download_missing_file_and_size_limit(self):
        scratch = Path.home() / "tmp" / "rahasia-xor" / "dokodemo-door"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            source = Path(directory) / "rahasia.pdf"
            payload = b"X" * 128
            with patch.object(app, "urlopen", return_value=io.BytesIO(payload)) as request:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(app.read_input(source), payload)
                    self.assertEqual(app.read_input(source), payload)
                request.assert_called_once_with(app.URL, timeout=30)
            missing = Path(directory) / "terlalu_besar.pdf"
            with (patch.object(app, "MAX_FILE", 64),
                  patch.object(app, "urlopen", return_value=io.BytesIO(payload)),
                  redirect_stdout(io.StringIO()), self.assertRaises(ValueError)):
                app.read_input(missing)
            self.assertFalse(missing.exists())

    def test_key_recovery_and_eof_variations(self):
        for key, ending in ((b"A\x00B\xff", b"\n"),
                            (b"1234567890abcdef", b"\r\n"),
                            (bytes(range(32)), b"")):
            with self.subTest(length=len(key)):
                original = make_pdf(ending=ending)
                ciphertext = app.xor_bytes(original, key)
                found, restored, _ = app.recover_pdf(ciphertext)
                self.assertEqual(found, key)
                self.assertEqual(restored, original)

    def test_compressed_stream_flag(self):
        pdf = make_pdf(compressed=True)
        self.assertNotIn(b"NFX{uji_otomatis}", pdf)
        self.assertEqual(app.find_flags(pdf, app.pdf_objects(pdf)), [b"NFX{uji_otomatis}"])

    def test_invalid_pdf_and_bounded_decompression(self):
        with self.assertRaises(ValueError):
            app.pdf_objects(b"%PDF-1.4\nstartxref\n0\n%%EOF\n")
        pdf = make_pdf()
        with self.assertRaises(ValueError):
            app.pdf_objects(pdf.replace(b"0000000015", b"0000000016"))
        with patch.object(app, "MAX_STREAM", 128), self.assertRaises(ValueError):
            app.inflate(zlib.compress(b"x" * 129))
        with self.assertRaises(ValueError):
            app.inflate(zlib.compress(b"uji")[:-2])

    def test_cli_preserves_input_and_existing_output(self):
        scratch = Path.home() / "tmp" / "rahasia-xor" / "dokodemo-door"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            source = Path(directory) / "rahasia.pdf"
            output = Path(directory) / "hasil.pdf"
            original = make_pdf(compressed=True)
            ciphertext = app.xor_bytes(original, b"ABCD")
            source.write_bytes(ciphertext)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(app.main([str(source), "-o", str(output)]), 0)
                self.assertEqual(app.main([str(source), "-o", str(output)]), 0)
                self.assertEqual(app.main([str(source), "-o", str(source)]), 1)
                output.write_bytes(b"Jangan ditimpa")
                self.assertEqual(app.main([str(source), "-o", str(output)]), 1)
            self.assertEqual(source.read_bytes(), ciphertext)
            self.assertEqual(output.read_bytes(), b"Jangan ditimpa")


if __name__ == "__main__":
    unittest.main()
