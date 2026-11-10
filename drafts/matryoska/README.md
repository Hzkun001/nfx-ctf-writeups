# Matryoska

> **Draf:** kategori dan difficulty menunggu konfirmasi. WU ini belum
> dimasukkan ke indeks pengumpulan Medium, Hard, atau Insane.

[Indeks repositori](../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Menunggu konfirmasi |
| Difficulty | Menunggu konfirmasi |
| Input yang dianalisis | [capsule.dat](capsule.dat) |
| Verifikasi | Lokal: seluruh lapisan dikodekan balik dan identik dengan input |

## Ringkasan

`capsule.dat` menyimpan flag dalam beberapa lapisan konversi. Pasangan
karakter pada lapisan terluar tertukar. Setelah urutannya dikembalikan,
data dapat dibuka melalui Base64, ZLIB, Base85, dan repeating-key XOR.

## Alur penyelesaian

### 1. Periksa byte input

Input berukuran **80 byte** dan tampak menyerupai Base64:

```text
NezoDMwALdIETDoQPTzHcqJlbzWHkyx7oLwy6Sx2DVwbgNosU81vHTQNATK19NIZQMM6gKAIXgPAAZ==
```

Dekode langsung memang diterima decoder Base64, tetapi menghasilkan byte
yang belum menunjukkan struktur arsip. Pengodean ulang hasilnya juga
mengubah akhiran `Z==` menjadi `Q==`, menunjukkan pad bits yang tidak kanonis.
Karena itu, lapisan terluar diperiksa sebelum melanjutkan dekompresi.

### 2. Kembalikan urutan setiap pasangan karakter

Tukar posisi pada pasangan `(0,1)`, `(2,3)`, dan seterusnya. Awalan berubah:

```text
NezoDMwA → eNozMDAw
```

Hasil tersebut merupakan Base64 kanonis. Setelah didekode, diperoleh
stream dengan signature **`78 DA`** yang dapat dibaca sebagai ZLIB.

### 3. Dekompresi ZLIB dan dekode Base85

Stream ZLIB dibuka sampai EOF, dengan pemeriksaan checksum dan tanpa sisa
data setelah stream. Hasilnya **50 karakter**:

```text
0001D8UQ0qdNL|lel;*kdKqX>e|9#0K6PtNeIf@!eRg3(d3QZr
```

String tersebut didekode memakai `base64.b85decode` menjadi **40 byte**.
Awal hasilnya adalah:

```text
00 00 00 62 1A 00 23 4C
```

### 4. Pulihkan lapisan repeating-key XOR

Uji dugaan awalan `NFXCTF{` terhadap byte awal hasil Base85. Hubungan XOR
memberikan byte kunci berikut:

```text
ciphertext: 00 00 00 62 1A 00 23
plaintext:  4E 46 58 43 54 46 7B    NFXCTF{
key:        4E 46 58 21 4E 46 58    NFX!NFX
```

Pola tersebut memberi kandidat kunci berulang empat byte **`NFX!`**.
Terapkan pada seluruh 40 byte:

```text
plaintext[i] = ciphertext[i] XOR key[i mod 4]
```

Hasilnya menjadi string flag utuh. Dugaan awalan ini diperiksa terhadap
seluruh hasil dan rekonstruksi berkas, bukan diterima dari awalan saja.

### 5. Verifikasi rekonstruksi

Terapkan urutan maju dari flag:

```text
XOR NFX! → Base85 → ZLIB level 9 → Base64 → tukar pasangan karakter
```

Hasilnya identik dengan seluruh **80 byte** `capsule.dat`. Input tidak
diubah. SHA256 sampel:

```text
e2f6db112e31db622142afaebc11b00e15588227f1e51e6e100f9c8c113064aa
```

## Flag

```text
NFXCTF{m4try0shk4_0n10n_p33l3d_c309b71e}
```

Prefiks asli `NFXCTF` dipertahankan. Bukti accepted pada platform belum
tersedia; hasil di atas diverifikasi secara lokal dari sampel yang diberikan.

## Reproduksi

Python 3.8 atau lebih baru, tanpa dependensi tambahan:

```bash
python3 solve.py
python3 -m unittest -v
```

[Solver](solve.py) mengikuti urutan lapisan yang sudah ditemukan. Kunci
`NFX!` dicantumkan sebagai parameter hasil analisis, bukan dicari ulang oleh
solver. Rekonstruksi lengkap diperiksa sebelum flag ditampilkan. Pengujian
mencakup sampel asli, invers untuk data lain, dan input rusak.

## Penggunaan AI

OpenAI Codex membantu pemeriksaan lapisan encoding, identifikasi pertukaran
pasangan karakter, analisis XOR, pengujian solver, dan penyusunan writeup.
