# Dokodemo Door

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Miscellaneous & Logic |
| Difficulty | Medium |
| Lampiran | [rahasia.pdf](https://raw.githubusercontent.com/NFCC-Com/qazwsx/refs/heads/main/crypto/Dokodemo_Door/rahasia.pdf) |
| Verifikasi | Lokal: struktur PDF, checksum stream, dan XOR balik |

## Ringkasan

File `rahasia.pdf` dienkripsi menggunakan repeating-key XOR. Header PDF
yang diketahui memberikan sebagian byte kunci. Statistik karakter per
kolom digunakan untuk melengkapi kunci, kemudian hasil diperiksa terhadap
struktur PDF. Flag ditemukan setelah stream teks ASCII85/Flate dibuka.

## Alur penyelesaian

### 1. Periksa ciphertext dan known plaintext

Lampiran berukuran **8.672 byte**. Delapan byte pertamanya adalah:

```text
4b 36 3c 19 46 02 5a 41
```

Byte tersebut belum sesuai signature PDF `%PDF-`. Karena XOR bersifat
simetris, hubungan ciphertext, plaintext, dan kunci adalah:

```text
C[i] = P[i] XOR K[i mod panjang_kunci]
K[i mod panjang_kunci] = C[i] XOR P[i]
```

`%PDF-` memberikan lima byte known plaintext. `%PDF-1.` panjangnya tujuh
byte; versi lengkap seperti `%PDF-1.4` memberikan delapan byte. Header ini
memberikan sebagian kunci, sehingga byte sisanya tetap perlu dipulihkan.

### 2. Pulihkan panjang dan isi kunci

[Solver](solve_rahasia.py) mencoba panjang kunci **4–32 byte**. Untuk setiap
panjang, ciphertext dibagi menjadi kolom berdasarkan posisi modulo panjang
kunci. Setiap kolom dienkripsi oleh byte kunci yang sama.

Seluruh 256 kandidat byte XOR dinilai berdasarkan karakter yang umum pada
PDF. Kandidat kemudian dibatasi oleh versi header dan variasi marker akhir
`%%EOF`. Penalti panjang digunakan untuk mengurangi kecocokan berlebihan
pada kunci panjang; pengulangan kunci yang sama juga dinormalisasi.

Kunci yang menghasilkan PDF valid adalah **16 byte**:

```text
nfx_k3tuk_p1ntu!
```

Nilai hexadecimal:

```text
6e 66 78 5f 6b 33 74 75 6b 5f 70 31 6e 74 75 21
```

### 3. Dekripsi dan validasi PDF

Seluruh ciphertext di-XOR dengan kunci berulang tersebut. Hasilnya dimulai
dengan `%PDF-1.4` dan diakhiri dengan:

```text
startxref
8239
%%EOF
```

Solver memeriksa offset tabel xref, offset seluruh sepuluh objek yang
dipakai, serta keberadaan objek Catalog. Pemeriksaan terpisah menggunakan
`pdfinfo` mengenali PDF 1.4, satu halaman A4, tanpa enkripsi PDF internal.

XOR balik dokumen menghasilkan ciphertext yang identik dengan lampiran.
Dokumen hasil tersedia sebagai [bukti pemulihan](assets/hasil-rahasia.pdf).

### 4. Buka stream teks dan cari flag

Pencarian regex pada byte PDF mentah belum menemukan flag. Stream teks
memiliki filter:

```text
/Filter [ /ASCII85Decode /FlateDecode ]
```

Filter dibuka berurutan: ASCII85 menggunakan `base64.a85decode`, lalu Flate
menggunakan zlib. Setelah checksum dan akhir stream diperiksa, pencarian
`NFX\{.*?\}` pada hasil dekompresi menemukan flag utuh.

## Flag

```text
NFX{k3tuk_p1ntu_bUk4_d0kum3n_x0r}
```

## Reproduksi

Jalankan dari folder writeup ini dengan Python 3.10 atau lebih baru:

```bash
python3 solve_rahasia.py
```

Jika `rahasia.pdf` belum tersedia, solver mengunduhnya dari URL lampiran.
Hasil disimpan sebagai `hasil_rahasia.pdf`; kunci dan flag dicetak ke terminal.
Untuk menentukan lokasi berkas secara eksplisit:

```bash
python3 solve_rahasia.py /lokasi/rahasia.pdf -o /lokasi/hasil_rahasia.pdf
```

Skrip memakai pustaka standar Python, tanpa `xortool` atau paket tambahan.
Input tidak diubah dan keluaran yang berbeda tidak ditimpa. Statistik
merupakan heuristik; validator ditujukan untuk xref klasik dan ekstraktor
mendukung stream ASCII85/Flate. OCR gambar tidak disertakan.

Pengujian offline:

```bash
python3 -m unittest -v
```

Lima tes mencakup panjang kunci 4/16/32 byte, kunci biner, variasi EOF,
stream terkompresi, batas ukuran, simulasi unduhan, dan perlindungan berkas.

SHA256 lampiran asli:

```text
44f43727b3de339f94ded1e67ef9cc6620e4d88f8fa707b4a738c35eba4a6df2
```

Verifikasi dalam writeup ini dilakukan secara lokal. Bukti accepted pada
platform belum tersedia.

## Penggunaan AI

OpenAI Codex membantu analisis repeating-key XOR, penyusunan dan pengujian
solver, pembacaan stream PDF, serta penulisan dokumentasi.
