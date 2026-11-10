# Stay

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Miscellaneous & Logic |
| Difficulty | Medium |
| Input yang dianalisis | [lirik.txt](lirik.txt), salinan UTF-8 teks yang diterima |
| Verifikasi | Lokal: pengodean balik seluruh simbol dan byte input identik |

## Ringkasan

Teks lirik menyimpan karakter Unicode tak terlihat. Empat jenis karakter
membentuk alfabet dua bit yang menghasilkan string Base64. Setelah Base64
dibuka, repeating-key XOR dengan salah satu kata literal dari teks
menghasilkan flag. Analisis dilakukan pada byte dan code point, tanpa
penafsiran makna lirik.

## Alur penyelesaian

### 1. Periksa Unicode mentah

Input dibaca sebagai UTF-8 tanpa normalisasi dan tanpa penghapusan whitespace.
Salinan yang dianalisis memiliki **674 byte**, **318 code point**, dan
**176 karakter berkategori `Cf`** (format character).

| Code point | Nama Unicode | Jumlah | Byte UTF-8 |
| --- | --- | ---: | --- |
| U+200B | ZERO WIDTH SPACE | 32 | `E2 80 8B` |
| U+200C | ZERO WIDTH NON-JOINER | 39 | `E2 80 8C` |
| U+200D | ZERO WIDTH JOINER | 26 | `E2 80 8D` |
| U+2060 | WORD JOINER | 79 | `E2 81 A0` |

Tidak ditemukan U+FEFF, tab, CR, atau spasi/tab pada akhir baris. Tiga LF
memisahkan empat baris teks. Karakter `Cf` muncul pula di akhir tiga baris
pertama; karakter tersebut dipertahankan saat ekstraksi.

### 2. Ubah alfabet tersembunyi menjadi byte

Ekstrak karakter `Cf` sesuai urutan aslinya. Karena ada empat simbol,
solver mencoba **24 permutasi** pemetaan dua bit. Satu pemetaan menghasilkan
Base64 kanonis: valid secara alfabet/padding dan identik ketika dikodekan ulang.

| Simbol | Bit |
| --- | --- |
| U+200B | `10` |
| U+200C | `00` |
| U+200D | `11` |
| U+2060 | `01` |

Gabungan `176 × 2 = 352` bit dibaca delapan bit per byte, menghasilkan
44 karakter ASCII berikut:

```text
KDkvOC8VFBJVFTMeXxMOPgFfNl8JORUEXzYKUxQKEQ==
```

### 3. Dekode Base64

Hasil dekode Base64 adalah ciphertext **31 byte**:

```text
28 39 2f 38 2f 15 14 12 55 15 33 1e 5f 13 0e 3e
01 5f 36 5f 09 39 15 04 5f 36 0a 53 14 0a 11
```

Data memuat karakter kontrol dan belum menunjukkan flag secara langsung.
Pemeriksaan dilanjutkan ke lapisan XOR.

### 4. Pulihkan lapisan repeating-key XOR

Setelah karakter `Cf` dipisahkan, kata literal dari teks terlihat digunakan
sebagai kandidat kunci. Ada **26 kata berbeda** yang diperiksa. Ini merupakan
pencarian atas byte kata yang tersedia, tanpa analisis sastra.

Kunci yang menghasilkan plaintext utuh berbentuk flag adalah **`falling`**,
sepanjang tujuh byte. Operasi dekripsinya:

```text
plaintext[i] = ciphertext[i] XOR key[i mod 7]
```

Kunci dan jawaban tidak ditanam dalam logika solver. Kandidat dinilai dari
bentuk seluruh plaintext, dan kecocokan dengan prefiks yang diminta
dilaporkan terpisah. Pencarian yang dibatasi hanya ke `NFX{...}` akan
melewatkan hasil ini karena prefiks aktualnya `NXCTF`.

### 5. Verifikasi pengodean balik

Plaintext di-XOR kembali, dikodekan Base64, lalu dipetakan kembali ke empat
simbol Unicode. Seluruh **176 karakter tersembunyi** cocok dengan ekstraksi
awal. Ketika disisipkan kembali pada posisi semula, seluruh **674 byte
UTF-8** juga identik dengan input.

SHA256 salinan input:

```text
21eec7d5c0fae42acb13492e077a4c9e549a4580d6bdcb5e4f75ae36c3da5de7
```

## Flag

```text
NXCTF{st4y_w1th_m3_1n_th3_d4rk}
```

Prefiks **NXCTF** dipertahankan sesuai plaintext. Regex `NFX\{.*?\}` tidak
cocok dengan string ini. Bukti accepted pada platform belum tersedia.

## Reproduksi

Jalankan dari folder writeup ini dengan Python 3.10 atau lebih baru:

```bash
python3 periksa_unicode.py
python3 -m unittest -v
```

[Solver](periksa_unicode.py) hanya menggunakan pustaka standar. Outputnya
meliputi `hasil_dekripsi.txt`, `laporan.json`, `codepoints.tsv`, urutan
karakter escaped, representasi bit, dan hasil antara Base64. `lirik.txt`
tidak diubah. Tiga tes mencakup sampel ini, dukungan prefiks NFX, dan
penolakan kandidat kata kunci yang tidak menghasilkan flag.

Pemeriksaan byte merujuk pada salinan UTF-8 pesan chat yang diterima;
berkas byte asli sebelum pengiriman chat tidak tersedia. Metode kandidat
kata ini bersifat heuristik dan sesuai dengan input tantangan ini.

## Penggunaan AI

OpenAI Codex membantu inventarisasi code point, pengujian pemetaan bit,
pemeriksaan lapisan XOR, verifikasi pengodean balik, dan penyusunan writeup.
