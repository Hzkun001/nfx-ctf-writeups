# The Alchemist's Sandbox

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Miscellaneous & Logic |
| Difficulty | Medium |
| Lampiran | [chall.py di Google Drive](https://drive.google.com/file/d/1CGh-1qN056hfi5NPE6yjGDpW4BccOewB/view) |
| Sumber lokal | [chall.py](chall.py) |
| Verifikasi | Lokal: payload diterima sandbox asli dan enkripsi ulang sesuai vault |

## Ringkasan

Tantangan menggabungkan PyJail berbasis filter karakter/AST dan algoritma
transformasi 32 putaran. `getattr` serta `chr` memungkinkan nama atribut
dibentuk pada runtime untuk mengambil state vault. Transformasi kemudian
dibalik dengan urutan putaran dan indeks word yang tepat hingga flag pulih.

## Alur penyelesaian

### 1. Periksa batas sandbox

Sumber melarang digit ASCII dan tanda kutip pada input. Pemeriksaan AST
memblokir import, lambda, comprehension, generator expression, f-string,
serta akses atribut yang namanya dimulai `_`. Panjang input dibatasi 1024
karakter; panggilan hanya boleh memakai maksimal dua argumen posisi dan
tanpa keyword argument.

Environment evaluasi menyediakan:

```python
{"__builtins__": {"getattr": getattr, "chr": chr}, "als": _encrypt_vault}
```

`ast.NamedExpr`, tuple, aritmetika, dan subscript tetap diizinkan. Pemeriksaan
atribut privat dilakukan terhadap `ast.Attribute`; string yang dibentuk
untuk argumen `getattr` tidak terkena pemeriksaan nama atribut tersebut.

### 2. Bentuk payload tanpa digit, kutip, atau underscore literal

Boolean `True` dapat dipakai sebagai nilai satu. Payload membentuk variabel
dengan walrus dan penjumlahan:

```text
a=True, b=a+a, c=b+b, d=c+c, e=d+d, f=e+e, g=f+f
```

Nilainya adalah 1, 2, 4, 8, 16, 32, dan 64. Maka `chr(g+f-a)` membentuk
underscore pada runtime. Kombinasi nilai lain membentuk karakter untuk
string `__globals__` dan `_VAULT_STATE`.

Operasi yang dicapai payload setara dengan:

```python
getattr(als, "__globals__").get("_VAULT_STATE")
```

Potongan di atas menjelaskan operasi; formula yang benar-benar memenuhi
filter tersedia di [payload.txt](payload.txt). Formula menempatkan assignment
dan lookup dalam tuple, lalu memakai `[-a]` untuk mengambil hasil terakhir.

Payload memiliki **306 karakter**, tanpa digit ASCII, kutip, atau underscore
literal. Setiap panggilan memenuhi batas argumen. Pengujian pada sandbox
asli mengembalikan seluruh 21 word `_VAULT_STATE`.

Karena state juga tersedia sebagai literal pada source, solver offline
membacanya melalui AST dan `ast.literal_eval`. Solver tidak mengimpor atau
menjalankan `chall.py` untuk mendapatkan state tersebut.

### 3. Balik transformasi 32 putaran

Flag terdiri dari **42 byte**, dikemas menjadi 21 word big-endian 16-bit.
Pada putaran `r`, konstanta yang dipakai adalah:

```text
rc = (r × 0x9E37 + 0x7F4A) mod 65536
```

Setiap word di-XOR dengan `mix`, ditambah `rc` modulo 65536, kemudian
dirotasi kiri lima bit. Setelah semua word diproses, indeks dipermutasi
menggunakan `4*i mod 21`.

Untuk membaliknya:

1. Proses putaran **31 turun ke 0**.
2. Batalkan permutasi memakai `16*i mod 21`, karena `4*16 mod 21 = 1`.
3. Pulihkan word dari indeks **20 turun ke 0**.
4. Lakukan rotasi kanan lima bit, kurangi konstanta modulo 65536, lalu XOR
   kembali dengan `mix` yang dihitung dari word sebelumnya.

Rumus invers per word:

```text
original = ((ROR16(current, 5) - rc) & 0xFFFF) XOR mix
```

Urutan indeks penting karena algoritma memperbarui array secara in-place.
Untuk indeks di atas nol, word sebelumnya masih berisi hasil transformasi
putaran itu. Ketika indeks nol dipulihkan, word terakhir sudah kembali ke
nilai awal putaran, sesuai nilai yang dipakai saat mengenkripsi indeks nol.

Terakhir, kemas hasil dengan `struct.pack(">21H", ...)` untuk mendapatkan
kembali 42 byte flag.

### 4. Verifikasi hasil

Empat tes memeriksa invers pada 25 plaintext acak yang deterministik,
roundtrip state sumber, rotasi, serta batas karakter dan AST payload.

Sumber asli juga diuji dalam `bwrap` dengan jaringan terputus dan sumber
read-only. Payload diterima dan menghasilkan state vault yang tepat.
Fungsi asli `_encrypt_vault(flag)` mengembalikan seluruh 21 word yang sama
dengan `_VAULT_STATE`.

SHA256 sumber asli:

```text
46c34f32dd4e0ad5c83176c204e19698c580a60c97c324147bf1e0db8af058bc
```

## Flag

```text
NFXCTF{pyj41l_4st_4lch3my_vm_pwn_d84f216a}
```

Awalan hasil sebenarnya adalah **NFXCTF**, berbeda dari contoh format NFX.
String hasil dipertahankan. Belum tersedia bukti accepted atau pengujian
pada server remote; verifikasi di atas dilakukan terhadap sumber lokal.

## Reproduksi

Dari folder writeup ini, jalankan dengan Python 3.8 atau lebih baru:

```bash
python3 solve.py
python3 -m unittest -v
```

[Solver](solve.py) memakai pustaka standar Python, memulihkan flag, dan
menghasilkan `flag.txt` serta `payload.txt` di folder solver. Enkripsi ulang
32 putaran diperiksa sebelum hasil ditampilkan. File keluaran dengan isi
berbeda tidak ditimpa. Payload dapat ditempel sebagai satu baris pada
prompt `formula>` layanan tantangan yang menjalankan filter serupa.

## Penggunaan AI

OpenAI Codex membantu membaca filter AST, menyusun payload bebas karakter
terlarang, membalik transformasi, menguji solver, dan menulis dokumentasi.
