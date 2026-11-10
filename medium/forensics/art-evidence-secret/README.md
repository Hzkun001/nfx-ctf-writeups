# Art Evidence Secret

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Forensics |
| Difficulty | Medium |
| Input yang dianalisis | [assets/original.png](assets/original.png), berkas PNG asli dari soal |
| Verifikasi | Lokal: dua tag AES-GCM terautentikasi, ekstraksi LSB direproduksi dua cara |

## Ringkasan

Sebuah berkas PNG tidak memuat flag secara langsung: tidak ada string `NFX`
di dalam chunk teks maupun setelah penanda akhir `IEND`. Jejaknya ada pada
**dua tempat**. Pertama, metadata `PhotoLocation` menyimpan password yang
disandikan Base64 di dalam Base64. Kedua, **bit paling tidak signifikan
(LSB)** kanal merah dan biru menyimpan dua payload terenkripsi berformat
`CTF1`. Payload merah dibuka dengan PBKDF2 dari password metadata dan
menghasilkan kunci hex; payload biru dibuka dengan kunci itu dan
menghasilkan flag.

Kunci soal ada pada komentar metadata: *"The smallest details matter."*

## Alur penyelesaian

### 1. Pemeriksaan awal

Berkas input adalah PNG RGB **1495 × 2424**, **774.601 byte**, SHA256
`1d349bbff6ba8f9bfd85fbf6980d098b5d810035395f3477d463526b11b2c4a1`.
Seluruh CRC chunk valid dan tidak ada data tambahan setelah `IEND`, jadi
flag tidak bisa diambil dengan `strings` atau `binwalk` biasa.

Metadata yang relevan:

| Kunci | Nilai mentah |
| --- | --- |
| `Comment` | `The smallest details matter.` |
| `PhotoLocation` | `SmFrYXJ0YSBTZWxhdGFuLCAxMzMwLCBSVyAyMCwgUlQgMTAsIFMzVnJkWEpwZFdzNU9RPT0=` |

`PhotoLocation` adalah Base64 dari teks yang di dalamnya masih ada Base64
lain:

```text
Jakarta Selatan, 1330, RW 20, RT 10, S3VrdXJpdWs5OQ==
```

Field terakhir adalah Base64 ganda yang mendekode ke password:

```text
Kukuriuk99
```

### 2. Ekstraksi LSB per kanal

Bit disusun **row-major** (baris demi baris, kiri ke kanan) dan setiap byte
diambil **MSB-first**. Kedua kanal memakai header yang sama: 4 byte `CTF1`
diikuti panjang payload 4 byte big-endian.

| Kanal | Panjang | Layout |
| --- | --- | --- |
| Merah (R, indeks 0) | 108 byte | `salt(16) + nonce(12) + ciphertext(64) + tag(16)` |
| Biru (B, indeks 2) | 53 byte | `nonce(12) + ciphertext(25) + tag(16)` |

Payload merah memakai **PBKDF2-HMAC-SHA256** dengan password metadata,
salt 16 byte dari awal payload, **200.000** iterasi, dan panjang kunci
turunan 32 byte. Hasil turunan menjadi kunci AES-GCM; plaintext-nya adalah
kunci hex 64 karakter:

```text
3cb7804019e6c5247aef85e1ca5362575097b9955ae8d1fdda34128fdf3d32bd
```

Payload biru dibuka dengan kunci hex tersebut (AES-GCM, nonce 12 byte),
sehingga tag-nya ikut terverifikasi.

### 3. Verifikasi hasil

Setiap tahap memakai `decrypt_and_verify`, jadi tag GCM yang cocok sudah
membuktikan kunci dan ciphertext benar tanpa menebak. Hasilnya diperiksa
ulang dengan dua ekstraksi independen (NumPy dan iterator piksel Pillow);
keduanya menghasilkan byte payload identik dan mengautentikasi kedua tag.

## Flag

```text
NFX{LSB_3ASY_OR_H4RD_IDK}
```

## Reproduksi

Dependensi: Python 3.10+, **Pillow**, dan **PyCryptodome**.

```bash
python3 solve.py            # memakai assets/original.png
python3 -m unittest -v      # tiga tes
```

[Solver](solve.py) memeriksa SHA256 input lebih dulu, lalu mengekstraksi
kanal merah dan biru. Tiga tes mencakup reproduksi flag, panjang payload
(108 dan 53 byte), serta penolakan tag yang dirusak. Berkas masukan tidak
diubah.

## Bukti

- [Berkas PNG asli](assets/original.png), SHA256 `1d349bbf…b2c4a1`.
- Metadata `Comment` dan `PhotoLocation` di atas.
- Payload merah dan biru dengan header `CTF1`, keduanya terautentikasi.

## Penggunaan AI

OpenAI Codex membantu penelusuran metadata, pengujian urutan bit LSB,
penyusunan rantai PBKDF2 → AES-GCM, dan penyuntingan writeup.
