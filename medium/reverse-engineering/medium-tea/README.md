# Medium TEA

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Medium |
| Author | cypera |
| Lampiran / sumber | [assets/medium_tea](assets/medium_tea) (ELF 64-bit LSB PIE, stripped, dari `NFCC-Com/qazwsx`, `rev/Medium_02_TEA/medium_tea`) |
| Verifikasi | Lokal: `./assets/medium_tea '<flag>'` mencetak `Correct! TEA terpecahkan.` |

## Ringkasan

Binary validator memakai **TEA (Tiny Encryption Algorithm) 32 ronde** dengan kunci
128-bit yang tertanam. Input dibaca dari `argv[1]`, panjangnya harus tepat
`0x28` (40 byte), lalu di-pad nol ke kelipatan 8 byte. Setiap blok 64-bit
dienkripsi dan hasilnya dibandingkan dengan ciphertext 40 byte di `.rodata`.

Dua hal membuat soal ini mudah dibalik:

1. **Konstanta kunci diobfuskasi sebagai pengurangan.** Disassembly tidak memuat
   `0xcafebabe`/`0xdeadc0de` secara literal, melainkan `sub 0x35014542` dan
   `sub 0x21523f22`. Karena keduanya operasi 32-bit, hasilnya adalah nilai
   dua's-complement dari konstanta aslinya.
2. **TEA bersifat invertible.** Struktur Feistel-nya memungkinkan dekripsi
   dengan menjalankan ronde terbalik tanpa perlu menginversi fungsi F.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file assets/medium_tea      # ELF 64-bit LSB pie executable, stripped
strings -a assets/medium_tea | grep -iE 'pemakaian|wrong|correct'
```

```text
Pemakaian: %s <flag>
Wrong!
Correct! TEA terpecahkan.
```

### 2. Ciphertext di `.rodata`

```bash
objdump -s -j .rodata assets/medium_tea
```

Ciphertext berada di `0x2040` sepanjang 40 byte (5 blok 64-bit):

```text
d08b910e 9e3d818e eadab483 cfc8fd8a 083b4483
6a130476 724d7205 905af697 db1395e7 c74c5385
```

### 3. Mengurai loop enkripsi dan kunci

Disassembly `0x1156`–`0x11bc` memperlihatkan inti TEA:

```text
1168: sub  esi, 0x61c88647        ; sum += 0x9e3779b9  (negasi dari -delta)
117a: sub  r9d, 0x35014542        ; k1 = -0x35014542 = 0xcafebabe
1181: add  eax, 0x1337beef        ; k0 = 0x1337beef
119e: add  r9d, 0x0badf00d        ; k3 = 0x0badf00d
11a5: sub  eax, 0x21523f22        ; k2 = -0x21523f22 = 0xdeadc0de
11b6: cmp  esi, 0xc6ef3720        ; berhenti saat sum == delta*32
```

Konstanta hasil decode:

| Konstanta | Nilai |
| --- | --- |
| delta | `0x9e3779b9` |
| ronde | 32 |
| k0 | `0x1337beef` |
| k1 | `0xcafebabe` |
| k2 | `0xdeadc0de` |
| k3 | `0x0badf00d` |

Rumus per ronde (sesuai TEA standar):

```text
sum += delta
v0 += ((v1 << 4) + k0) ^ (v1 + sum) ^ ((v1 >> 5) + k1)
v1 += ((v0 << 4) + k2) ^ (v0 + sum) ^ ((v0 >> 5) + k3)
```

Setiap blok dibaca **little-endian** sebagai `(v0, v1)`, lalu dibandingkan
`memcmp` per 8 byte dengan array di `0x2040`.

### 4. Dekripsi

Dekripsi TEA menjalankan ronde dari belakang dengan `sum` dimulai dari
`delta * 32`:

```python
sum = (delta * 32) & 0xFFFFFFFF
for _ in range(32):
    v1 -= (((v0 << 4) + k2) ^ ((v0 >> 5) + k3) ^ (v0 + sum))
    v0 -= (((v1 << 4) + k0) ^ ((v1 >> 5) + k1) ^ (v1 + sum))
    sum = (sum - delta) & 0xFFFFFFFF
```

Atau langsung jalankan solver:

```bash
python3 solve.py
```

### 5. Verifikasi hasil

```bash
./assets/medium_tea 'NFX{t1ny_3ncrypt10n_4lg0r1thm_32_r0und5}'
# Correct! TEA terpecahkan.

./assets/medium_tea 'NFX{wrong}'
# Wrong!
```

## Flag

```text
NFX{t1ny_3ncrypt10n_4lg0r1thm_32_r0und5}
```

## Reproduksi

Hanya butuh Python 3 (pustaka standar, tanpa dependensi eksternal):

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 lampiran, membaca ciphertext dari
`.rodata` di offset `0x2040`, menjalankan 32 ronde TEA terbalik per blok
little-endian, membuang padding nol, lalu mencetak flag.
[test_solve.py](test_solve.py) menguji keutuhan berkas input, kebenaran flag,
round-trip enkripsi/dekripsi per blok, kecocokan enkripsi ulang dengan
ciphertext asli, dan penolakan berkas yang dimodifikasi. Berkas masukan tidak
diubah.

## Bukti

- Berkas tantangan terverifikasi: [assets/medium_tea](assets/medium_tea)
  (SHA256: `a2b45f299304e0cc64582e0bdc704100b9cb2f4fc4c0f164a8cfd322b01b255a`).
- Ciphertext 40 byte di `0x2040`, kunci hasil decode konstanta `sub`/`add`.
- Output verifikasi: `./assets/medium_tea '<flag>'` → `Correct! TEA terpecahkan.`
- Enkripsi ulang plaintext yang dipulihkan menghasilkan ciphertext identik
  dengan yang tersimpan di binary (diuji otomatis).

## Penggunaan AI

Penyusunan solver (ronde TEA terbalik) dan penyuntingan naskah writeup dibantu
oleh model AI; seluruh langkah analisis dan verifikasi dijalankan ulang secara lokal.
