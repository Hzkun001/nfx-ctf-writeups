# Hard Feistel

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Hard |
| Author | cypera |
| Lampiran / sumber | [assets/hard_feistel](assets/hard_feistel) (ELF 64-bit LSB PIE, stripped, dari `NFCC-Com/qazwsx`, `rev/Hard_02_Feistel/hard_feistel`) |
| Verifikasi | Lokal: `./assets/hard_feistel '<flag>'` mencetak `Correct! Jaringan Feistel berhasil dibalik.` |

## Ringkasan

Flag dienkripsi dengan **jaringan Feistel 16 ronde** pada blok 32-bit, dengan
`L` dan `R` masing-masing 16-bit. Round key diturunkan dari jadwal sederhana dan
disimpan sebagai array `uint32` di `.rodata`, sedangkan ciphertext 40 byte
tersimpan di `.data`.

Karena struktur Feistel **invertibel secara struktural**, dekripsi tidak perlu
menginversi fungsi `F` — cukup menjalankan ronde dari belakang dengan urutan
kunci terbalik. Ini membuat soal jauh lebih ringan daripada yang terlihat.

Dua detail penting yang harus diperhatikan:

1. **Konstanta di `F` bukan TEA biasa.** `F` memakai `0x9e3779b1` (bukan
   `0x9e3779b9`) dikali `R` lalu digeser 5 bit, di-XOR dengan `K * 0x101`.
2. **Ciphertext ada di `.data`, yang offset filenya berbeda dari vaddr**
   (`0x4020` → file offset `0x3020`), tidak seperti `.rodata` yang 1:1.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file assets/hard_feistel        # ELF 64-bit LSB pie executable, stripped
strings -a assets/hard_feistel | grep -iE 'pemakaian|wrong|correct'
```

```text
Pemakaian: %s <flag>
Wrong!
Correct! Jaringan Feistel berhasil dibalik.
```

Panjang input divalidasi `strlen(argv[1]) == 0x27` (39 byte), lalu disalin ke
buffer 40 byte yang sudah dinolkan — jadi efektifnya ada padding satu NUL.

### 2. Memetakan round key dan ciphertext

```bash
objdump -s -j .rodata assets/hard_feistel
objdump -s -j .data   assets/hard_feistel
readelf -S assets/hard_feistel | grep -E '\.rodata|\.data'
```

| Section | Vaddr | File offset | Isi |
| --- | --- | --- | --- |
| `.rodata` | `0x2060` | `0x2060` | 16 × `uint32` round key |
| `.data` | `0x4020` | **`0x3020`** | 40 byte ciphertext |

Nilai round key:

```text
5a 79 98 b7 d6 f5 14 33 52 71 90 af ce ed 0c 2b
```

yang mengikuti jadwal trivial `K[i] = 0x5a + 0x1f*i (mod 256)`.

### 3. Mengurai fungsi ronde

Dari disassembly `0x1190`–`0x11b4`:

```text
imul eax, ebx, 0x9e3779b1   ; R * 0x9e3779b1  (32-bit)
shr  eax, 5                 ; >> 5
mov  edx, ebp
shl  edx, 8
add  edx, ebp               ; K * 0x101  (duplikasi byte)
xor  eax, edx
movzx eax, ax               ; potong ke 16 bit
xor  eax, esi               ; XOR dengan L
```

Sehingga:

```text
F(r, k) = ((((r * 0x9e3779b1) & 0xffffffff) >> 5) ^ ((k * 0x101) & 0xffffffff)) & 0xffff
```

Satu ronde: `L, R = R, L ^ F(R, k)`. Blok dibaca **big-endian**:
`L = b0<<8 | b1`, `R = b2<<8 | b3`.

### 4. Dekripsi

Feistel tidak perlu inversi `F`; cukup ronde terbalik:

```python
for k in reversed(keys):
    L, R = (R ^ F(L, k)) & 0xffff, L
```

Atau langsung jalankan solver:

```bash
python3 solve.py
```

### 5. Verifikasi hasil

```bash
./assets/hard_feistel 'NFX{f315t3l_n3tw0rk_16_r0und5_r3v3rs3d}'
# Correct! Jaringan Feistel berhasil dibalik.

./assets/hard_feistel 'NFX{aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}'
# Wrong!
```

## Flag

```text
NFX{f315t3l_n3tw0rk_16_r0und5_r3v3rs3d}
```

## Reproduksi

Hanya butuh Python 3 (pustaka standar, tanpa dependensi eksternal):

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 lampiran, memuat 16 round key dari
`.rodata`, membaca ciphertext dari `.data` (memakai **file offset** yang benar,
bukan vaddr), menjalankan 16 ronde Feistel terbalik per blok big-endian, membuang
padding nol, lalu mencetak flag. [test_solve.py](test_solve.py) menguji keutuhan
berkas input, kebenaran flag, jumlah dan jadwal round key, round-trip
enkripsi/dekripsi per blok, **rekripsi maju** yang menghasilkan ciphertext
identik, sifat 16-bit `F`, dan penolakan berkas yang dimodifikasi.

## Bukti

- Berkas tantangan terverifikasi: [assets/hard_feistel](assets/hard_feistel)
  (SHA256: `2db9a9e254792a497cc71e64be16b35b02665e4d9d553734dff3b9dfc7e21e51`).
- Round key di `.rodata:0x2060` (16 × uint32), ciphertext di `.data` vaddr `0x4020`
  / file offset `0x3020`.
- Output verifikasi: `./assets/hard_feistel '<flag>'` → `Correct! Jaringan Feistel berhasil dibalik.`
- Enkripsi ulang plaintext yang dipulihkan menghasilkan ciphertext identik
  (diuji otomatis).

## Penggunaan AI

Penyusunan solver (ronde Feistel terbalik dan penanganan offset `.data`) serta
penyuntingan naskah writeup dibantu oleh model AI; seluruh langkah analisis dan
verifikasi dijalankan ulang secara lokal.
