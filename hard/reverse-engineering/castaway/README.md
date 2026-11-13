# Castaway

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Hard |
| Author | Kesatria Baja Ringan |
| Lampiran / sumber | [assets/castaway](assets/castaway) (ELF 64-bit LSB PIE, stripped, dari `NFCC-Com/qazwsx`, `rev/Hard_03_Castaway/castaway`) |
| Verifikasi | Lokal: `echo '<flag>' \| ./assets/castaway` mencetak `Access granted.` |

## Ringkasan

Binary membaca calon flag dari **stdin**, lalu memvalidasinya melalui tiga lapis
pertahanan:

1. **Anti-debug `ptrace`** — memanggil `ptrace(PTRACE_TRACEME, ...)` dan
   menandai apakah proses sedang di-trace. Flag hasil deteksi ini dipakai sebagai
   kunci XOR tambahan pada byte pertama input.
2. **State machine kecil dengan opaque predicate** — variabel state mengalir
   melalui nilai `0, 1, 2, 0x32, 0x63`, dan transisi `2 → 0x32` dijaga oleh
   predicate `(i * i) & 3 == 2` yang tampak rumit tetapi deterministik.
3. **Transformasi per-byte berantai** — setiap byte di-XOR dengan state, dirotasi,
   ditambah entri tabel, dipetakan lewat **S-box 256 entri**, lalu di-XOR dengan
   `i * 0x2f`. State kemudian diperbarui dari ciphertext byte tersebut.

Kunci penyelesaian: karena **state bergantung pada ciphertext** (bukan pada
plaintext), seluruh rantai state dapat direkonstruksi hanya dari ciphertext,
sehingga transformasi tiap byte bisa dibalik satu per satu tanpa brute force.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file assets/castaway        # ELF 64-bit LSB pie executable, stripped
strings -a assets/castaway | grep -iE 'flag>|nope|access'
```

```text
flag> 
Nope.
Access granted.
```

### 2. Pemetaan tabel di `.rodata`

```bash
objdump -s -j .rodata assets/castaway
```

| Alamat | Ukuran | Peran |
| --- | --- | --- |
| `0x2020` | 256 byte | S-box (permutasi penuh, semua nilai unik) |
| `0x2120` | 16 byte | tabel penambah `dc5ac5d41cd2bb6b825c9af1d19676bd` |
| `0x2140` | 40 byte | ciphertext target |

### 3. Memahami transformasi

Dari disassembly fungsi transformasi (`0x1282`–`0x142d`), untuk tiap byte `i`
dengan state `st`:

```text
b = input[i] ^ st
b = rotl8(b, (i % 7) + 1)
b = b + addt[i & 0xf]
b = sbox[b]
b = b ^ (i * 0x2f)
out[i] = b
st = (i + b - 125 * st) & 0xff        # state baru dari CIPHERTEXT b
```

State awal `st = 0xa5`. Perhatikan `imul eax, 0xffffff83` = `-125` dan
`imul eax, 0x2f` untuk faktor XOR.

Predicate opaque `(i*i) & 3 == 2` hanya menentukan apakah state machine lanjut ke
`0x32` atau `1`; karena deterministik terhadap `i`, ia tidak menghalangi
pembalikan — cukup diabaikan saat membalik.

### 4. Membalik transformasi

Karena `st` hanya bergantung pada ciphertext, hitung dulu semua state:

```python
state = 0xA5
states = []
for i, b in enumerate(ct):
    states.append(state)
    state = (i + b - 125 * state) & 0xFF
```

Lalu balik tiap langkah dengan urutan terbalik (XOR → S-box → tambah → rotasi → XOR state):

```python
b ^= (i * 0x2f) & 0xff
b = inv_sbox[b]
b = (b - addt[i & 0xf]) & 0xff
b = rotr8(b, (i % 7) + 1)      # rotasi ke arah berlawanan
plain[i] = b ^ states[i]
```

Atau langsung jalankan solver:

```bash
python3 solve.py
```

### 5. Verifikasi hasil

```bash
echo 'NFX{c4st4w4y_0n_4n_0p4qu3_st4t3_m4ch1n3}' | ./assets/castaway
# flag> Access granted.

echo 'NFX{wrong_wrong_wrong_wrong_wrong_wrong}' | ./assets/castaway
# flag> Nope.
```

## Flag

```text
NFX{c4st4w4y_0n_4n_0p4qu3_st4t3_m4ch1n3}
```

## Reproduksi

Hanya butuh Python 3 (pustaka standar, tanpa dependensi eksternal):

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 lampiran, membaca S-box, tabel
penambah, dan ciphertext dari `.rodata`, merekonstruksi rantai state dari
ciphertext, membalik transformasi per byte, lalu mencetak flag.
[test_solve.py](test_solve.py) menguji keutuhan berkas input, kebenaran flag,
**rekripsi maju** yang menghasilkan ciphertext identik, konsistensi rantai state,
sifat saling-invers rotasi, dan penolakan berkas yang dimodifikasi. Berkas
masukan tidak diubah.

## Bukti

- Berkas tantangan terverifikasi: [assets/castaway](assets/castaway)
  (SHA256: `6ca0a8f8e50b77f7dc666cf1b7a486f1a12df1008c478cbbe6615245bca776d1`).
- S-box permutasi penuh di `0x2020`; tabel penambah di `0x2120`; ciphertext di `0x2140`.
- Output verifikasi: `echo '<flag>' | ./assets/castaway` → `Access granted.`
- Reimplementasi transformasi maju menghasilkan ciphertext identik (diuji otomatis).

## Penggunaan AI

Penyusunan solver (rekonstruksi state berantai dan pembalikan transformasi) serta
penyuntingan naskah writeup dibantu oleh model AI; seluruh langkah analisis dan
verifikasi dijalankan ulang secara lokal.
