# My Lovely Freya

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Miscellaneous & Logic |
| Difficulty | Hard |
| Author | salep88 |
| Lampiran | [FreyaSayangkuh](https://drive.google.com/file/d/1gesizzk8iqP0812D-d4rrgycdP4vrW5l/view) |
| Verifikasi | Pemulihan lokal; dekripsi OpenSSL dan enkripsi ulang diperiksa |

## Ringkasan

Lampiran berisi sebuah PNG dan surat terenkripsi. Tinggi pada header PNG
diperkecil sehingga tulisan password di bagian bawah gambar tersembunyi.
Dengan menghitung tinggi dari data scanline, gambar dapat dipulihkan.
Password yang muncul kemudian membuka surat menggunakan AES-256-CBC
dengan PBKDF2-HMAC-SHA256 sebanyak 100.000 iterasi.

## Alur penyelesaian

### 1. Identifikasi lampiran

Walaupun tidak memiliki ekstensi, `FreyaSayangkuh` diawali signature ZIP
`50 4b 03 04`. Arsip memuat:

| Berkas | Ukuran |
| --- | ---: |
| `freya_sayangkuh.png` | 1.782.590 byte |
| `surat_untuk_freya.enc` | 48 byte |

PNG memiliki dimensi **1024 × 1200**, RGB 8-bit, dan tidak memakai interlace.
Metadata `Secret` berisi `QXlhbWdHb3Jlbmc0NQ==`, yang terdekode menjadi
`AyamgGoreng45`. Nilai ini tidak membuka surat dengan parameter dekripsi
yang akhirnya terverifikasi, sehingga pemeriksaan dilanjutkan ke struktur PNG.

### 2. Temukan tinggi gambar sebenarnya

Setelah seluruh payload `IDAT` digabung dan didekompresi dengan zlib,
diperoleh **4.720.128 byte**, tanpa data sisa setelah akhir stream.

Untuk PNG RGB 8-bit non-interlaced, satu scanline terdiri dari satu byte
filter dan tiga byte per piksel:

```text
byte per scanline = 1 + (1024 × 3) = 3073
tinggi sebenarnya = 4.720.128 / 3073 = 1536
baris tersembunyi = 1536 - 1200 = 336
```

Ubah field tinggi `IHDR` pada offset `0x14` menjadi `1536` (`00 00 06 00`),
lalu hitung ulang CRC `IHDR` pada offset `0x1D`. CRC mencakup jenis chunk
`IHDR` dan payload-nya. Payload `IDAT` dipertahankan utuh.

Bagian bawah [gambar yang dipulihkan](assets/freya-restored.png) menampilkan:

```text
<!HayamGoreng45@/>
```

Seluruh karakter tersebut, termasuk `<!` dan `/>`, merupakan password.

### 3. Dekripsi surat

Surat memiliki framing OpenSSL berikut:

```text
offset 0x00: Salted__             (8 byte)
offset 0x08: d4be860a4bb7cf3a     (salt 8 byte)
offset 0x10: ciphertext          (32 byte)
```

Petunjuk **100.000** dan **256** mengarahkan percobaan ke iterasi derivasi
kunci dan ukuran kunci AES. Parameter yang berhasil adalah:

| Parameter | Nilai |
| --- | --- |
| Password | `<!HayamGoreng45@/>` |
| KDF | PBKDF2-HMAC-SHA256 |
| Iterasi | 100000 |
| Panjang hasil KDF | 48 byte: key 32 byte, IV 16 byte |
| Cipher | AES-256-CBC |
| Padding | PKCS#7 |

Pada OpenSSL yang mendukung opsi `-saltlen`, dekripsi dapat diulang dengan:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -md sha256 \
  -saltlen 8 -in surat_untuk_freya.enc -pass 'pass:<!HayamGoreng45@/>'
```

### 4. Verifikasi

Dekripsi menghasilkan 24 byte, termasuk satu LF di akhir. Pemeriksaan
OpenSSL secara terpisah menghasilkan plaintext yang sama. Enkripsi ulang
dengan key, IV, dan padding yang sama juga menghasilkan ciphertext identik.

SHA256 lampiran asli:

```text
42547fc5fefd3b9fc555901b94827cd3131b9c8f082bdcb336bb688ada2721c1
```

## Flag

```text
NXCTF{FR3Y4_MY_L0V3LY!}
```

Prefiks yang diperoleh dari surat adalah **NXCTF**, berbeda dari contoh
format **NFX** pada deskripsi. String hasil dipertahankan apa adanya.
Writeup ini mencatat verifikasi lokal; bukti accepted pada platform belum tersedia.

## Reproduksi

[Solver](solve.py) membutuhkan Python 3 dan perintah `openssl`, tanpa paket
Python tambahan. Unduh lampiran ke folder writeup ini, kemudian jalankan:

```bash
python3 solve.py FreyaSayangkuh
```

Solver menghasilkan `output/freya-restored.png` dan
`output/surat-terbaca.txt`. Password pada solver ditranskripsikan dari baris
gambar yang dipulihkan; solver tidak menjalankan OCR. Dekripsinya memisahkan
header dan salt secara eksplisit sehingga tidak bergantung pada default
panjang salt OpenSSL. Lampiran asli tidak diubah.

## Penggunaan AI

OpenAI Codex membantu memeriksa struktur PNG, menghitung tinggi scanline,
menguji parameter dekripsi, serta menyusun solver dan dokumentasi.
