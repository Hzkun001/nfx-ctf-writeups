# Medium RC4

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Medium |
| Author | cypera |
| Lampiran / sumber | [medium_rc4](medium_rc4) (ELF 64-bit, stripped) |
| Verifikasi | Lokal: menjalankan `./medium_rc4 '<flag>'` mencetak `Correct! RC4 memang simetris.` |

## Ringkasan

Binary validator menerima satu argumen (calon flag) dan membandingkannya dengan
ciphertext hasil RC4. Kunci RC4 tertanam sebagai string di `.rodata`, dan
ciphertext tersimpan sebagai array byte. Karena RC4 bersifat simetris, dekripsi
memakai fungsi yang sama dengan enkripsi sehingga cukup membalik alur yang sama.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file medium_rc4        # ELF 64-bit LSB pie executable, stripped
strings -a medium_rc4 | grep -iE 'key|wrong|correct'
```

Dari `strings` terlihat pesan dan kunci yang tertanam:

```text
Pemakaian: %s <flag>
Wrong!
n0t_s3cur3_k3y_2026
Correct! RC4 memang simetris.
```

### 2. Menemukan lokasi kunci dan ciphertext di .rodata

```bash
objdump -s -j .rodata medium_rc4
```

| Alamat | Isi | Arti |
| --- | --- | --- |
| `0x2021` | `n0t_s3cur3_k3y_2026` (19 byte) | kunci RC4 |
| `0x2060` | 42 byte ciphertext | target pembanding |

Disassembly di sekitar `main` (`0x1160`–`0x1240`) menunjukkan:

- `strlen(argv[1])` harus sama dengan `0x2a` (42).
- KSA standar: `j = (j + S[i] + key[i % 19]) & 0xff`, swap `S[i]`/`S[j]`,
  berjalan `i = 0..255`.
- PRGA standar: `i++`, `j += S[i]`, swap, lalu `xor` dengan `S[(S[i]+S[j]) & 0xff]`.
- Hasil 42 byte dibandingkan `memcmp` dengan array di `0x2060`.

### 3. Dekripsi

Karena RC4 simetris, cukup jalankan RC4 yang sama atas ciphertext dengan kunci
tersebut:

```python
ct = bytes.fromhex(
    "ada1e2de80fab7a465572a79e3ecf825"
    "690a5cca49dff6caa4c29c36d2485f17"
    "bb3e29d201f7009c9d31"
)
key = b"n0t_s3cur3_k3y_2026"
# ... KSA + PRGA standar, lalu xor dengan ct ...
```

Atau langsung pakai solver:

```bash
python3 solve.py
```

### 4. Verifikasi hasil

```bash
./medium_rc4 'NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}'
# Correct! RC4 memang simetris.

./medium_rc4 'NFX{wrong}'
# Wrong!
```

## Flag

```text
NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}
```

## Reproduksi

Hanya butuh Python 3 standar:

```bash
python3 solve.py              # membaca medium_rc4, mencetak flag
python3 -m unittest -v        # dua tes: flag & simetri RC4
```

[Solver](solve.py) membaca kunci dan ciphertext langsung dari `.rodata`
berdasarkan offset tetap, menjalankan RC4, lalu mencetak flag. Berkas input
tidak diubah. SHA256 `medium_rc4`:
`cc8b962d1501755603febfb884c5c49b42d9814aff165ed21d9cc81cda71d0f1`.

## Bukti

- [Binary asli](medium_rc4), SHA256 `cc8b962d…d0f1`.
- Output verifikasi `./medium_rc4 '<flag>'` → `Correct! RC4 memang simetris.`

## Penggunaan AI

OpenAI Codex membantu menulis struktur KSA/PRGA pada solver dan menyunting
naskah writeup.
