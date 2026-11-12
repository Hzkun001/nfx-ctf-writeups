# Wujud Aseli Atmin

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Miscellaneous & Logic |
| Difficulty | Medium |
| Author | Ariaf |
| Lampiran / sumber | [assets/dokumentasi.png](assets/dokumentasi.png) |
| Verifikasi | Lokal: rekonstruksi ZIP utuh, validasi header PNG, ekstraksi LSB kanal merah terkonfirmasi |

## Ringkasan

Soal menyediakan berkas gambar PNG bernama `dokumentasi.png`. Pemeriksaan
struktur biner menunjukkan adanya arsip ZIP yang disisipkan (appended)
setelah chunk penutup standar PNG (`IEND`). Di dalam arsip ZIP tersebut
terdapat berkas `catatan.txt` dan `scan_07.dat`. Berkas `scan_07.dat`
sejatinya merupakan gambar PNG yang telah dirusak 8 byte magic signature
awalnya (ter-nolkan). Setelah signature dan chunk length diperbaiki, ekstraksi
bit paling tidak signifikan (**LSB**) pada kanal warna merah (**Red**)
mengungkap string Base64 yang mendekode langsung ke flag kompetisi.

## Alur penyelesaian

### 1. Pemeriksaan awal

Berkas input adalah PNG dengan metadata ukuran:

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `dokumentasi.png` | 1.328.704 byte | `ab61ce519d0776ecae6695649c1a98d741b9cc2ded82e11a508305ae7385a3d9` |

Pemeriksaan akhir chunk PNG menemukan bahwa marker `IEND` (`49 45 4E 44 AE 42 60 82`)
diikuti oleh signature arsip ZIP (`PK\x03\x04` pada offset `0x1434ce`):

```text
001434c0: 0000 0000 4945 4e44 ae42 6082 504b 0304  ....IEND.B`.PK..
001434d0: 1400 0000 0800 ...
```

### 2. Ekstraksi arsip dan perbaikan header PNG

Arsip ZIP diekstrak dan menghasilkan dua berkas:
- `catatan.txt`: berisi teks pengalih perhatian (*"Arsip internal. Tidak ada apa-apa di sini."*).
- `scan_07.dat`: berkas data berukuran 4.754 byte.

Pemeriksaan hexdump pada `scan_07.dat` memperlihatkan pola chunk PNG yang khas,
tetapi 8 byte pertama bernilai nol:

```text
00000000: 0000 0000 0000 0000 0000 000d 4948 4452  ............IHDR
00000010: 0000 0190 0000 012c 0802 0000 0062 d572  .......,.....b.r
```

Chunk type `IHDR` berada pada offset `0x0C` dengan panjang `0x0000000D` pada offset `0x08`.
Dengan merekonstruksi 12 byte awal menjadi signature resmi PNG:

```python
png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D])
fixed_png = png_header + scan_07_dat[12:]
```

Berkas berhasil dipulihkan menjadi gambar PNG valid berdimensi **400 × 300** RGB.

### 3. Ekstraksi LSB kanal merah

Gambar hasil perbaikan menampilkan visual grafis dengan tulisan *"SCAN 07"*.
Analisis steganografi dilakukan dengan mengekstraksi bit LSB dari setiap kanal
warna secara row-major dan MSB-first. Pada kanal merah (**R**), ditemukan
untaian karakter Base64:

```text
TkZYe05GQ0NfR29lc190b19OQ1NDXzIwMjZ9
```

Melakukan decoding Base64 menghasilkan flag kompetisi:

```text
NFX{NFCC_Goes_to_NCSC_2026}
```

### 4. Verifikasi hasil

- Ekstraksi ZIP menghasilkan checksum CRC32 yang valid.
- Gambar `scan_07_fixed.png` dapat dibuka tanpa peringatan error oleh parser libpng/Pillow.
- Decoding Base64 menghasilkan flag utuh dengan format `NFX{...}` yang valid.

## Flag

```text
NFX{NFCC_Goes_to_NCSC_2026}
```

## Reproduksi

Dependensi: Python 3.10+ dan **Pillow** (`pip install -r requirements.txt`).

Jalankan solver:

```bash
python3 solve.py
```

Jalankan pengujian otomatis:

```bash
python3 -m unittest -v
```

## Bukti

- [assets/dokumentasi.png](assets/dokumentasi.png): berkas input tantangan.
- [solve.py](solve.py): skrip otomatisasi ekstraksi dan dekode.
- [test_solve.py](test_solve.py): unit test pemastian integritas berkas dan flag.
