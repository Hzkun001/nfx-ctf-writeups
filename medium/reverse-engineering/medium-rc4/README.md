# Medium RC4

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Medium |
| Author | cypera |
| Lampiran / sumber | [assets/medium_rc4](assets/medium_rc4) (ELF 64-bit LSB PIE, stripped, dari `NFCC-Com/qazwsx`, `rev/Medium_01_RC4/medium_rc4`) |
| Verifikasi | Lokal: `./assets/medium_rc4 '<flag>'` mencetak `Correct! RC4 memang simetris.` |

## Ringkasan

Binary validator menerima satu argumen berupa calon flag, lalu mengenkripsinya
dengan **RC4** dan membandingkan hasilnya dengan ciphertext 42 byte yang
tersimpan di `.rodata`. Kunci RC4 juga tertanam di `.rodata` sebagai string
literal, sehingga tidak ada kerahasiaan yang tersisa: kunci dan ciphertext sama-sama
dapat dibaca langsung dari berkas.

Karena RC4 bersifat **simetris** (algoritma enkripsi dan dekripsi identik), tidak
diperlukan inversi apa pun. Cukup jalankan KSA + PRGA yang sama atas ciphertext
dengan kunci tersebut untuk memperoleh plaintext.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file assets/medium_rc4      # ELF 64-bit LSB pie executable, stripped
strings -a assets/medium_rc4 | grep -iE 'key|wrong|correct|pemakaian'
```

`strings` langsung membocorkan kunci dan pesan validasi:

```text
Pemakaian: %s <flag>
Wrong!
n0t_s3cur3_k3y_2026
Correct! RC4 memang simetris.
```

### 2. Memetakan kunci dan ciphertext di `.rodata`

```bash
objdump -s -j .rodata assets/medium_rc4
```

| Alamat | Isi | Peran |
| --- | --- | --- |
| `0x2021` | `n0t_s3cur3_k3y_2026` (19 byte) | kunci RC4 |
| `0x2060` | 42 byte ciphertext | target pembanding `memcmp` |

Disassembly `main` (`0x10e0`–`0x1240`) mengonfirmasi alur standar RC4:

- `strlen(argv[1])` harus tepat `0x2a` (42 byte).
- **KSA**: `j = (j + S[i] + key[i % 19]) & 0xff`, lalu swap `S[i]`/`S[j]`,
  untuk `i = 0..255`.
- **PRGA**: `i++`, `j += S[i]`, swap, lalu XOR byte dengan
  `S[(S[i] + S[j]) & 0xff]`.
- Hasil 42 byte dibandingkan `memcmp` dengan array di `0x2060`.

### 3. Dekripsi (RC4 simetris)

```python
key = b"n0t_s3cur3_k3y_2026"
ct = bytes.fromhex(
    "ada1e2de80fab7a465572a79e3ecf825"
    "690a5cca49dff6caa4c29c36d2485f17"
    "bb3e29d201f7009c9d31"
)
# jalankan KSA + PRGA standar dengan `key`, lalu XOR terhadap `ct`
```

Atau langsung jalankan solver:

```bash
python3 solve.py
```

### 4. Verifikasi hasil

```bash
./assets/medium_rc4 'NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}'
# Correct! RC4 memang simetris.

./assets/medium_rc4 'NFX{wrong}'
# Wrong!
```

## Flag

```text
NFX{rc4_1s_s1mpl3_but_d34dly_1n_r3v3rs1ng}
```

## Reproduksi

Hanya butuh Python 3 (pustaka standar, tanpa dependensi eksternal):

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 lampiran, membaca kunci dan ciphertext
dari `.rodata` berdasarkan offset tetap, menjalankan KSA + PRGA RC4, lalu
mencetak flag. [test_solve.py](test_solve.py) menguji keutuhan berkas input,
kebenaran flag, sifat simetris RC4, dan penolakan berkas yang dimodifikasi.
Berkas masukan tidak diubah.

## Bukti

- Berkas tantangan terverifikasi: [assets/medium_rc4](assets/medium_rc4)
  (SHA256: `cc8b962d1501755603febfb884c5c49b42d9814aff165ed21d9cc81cda71d0f1`).
- Tabel lokasi kunci (`0x2021`) dan ciphertext (`0x2060`) di `.rodata`.
- Output verifikasi: `./assets/medium_rc4 '<flag>'` → `Correct! RC4 memang simetris.`

## Penggunaan AI

Penyusunan solver (KSA/PRGA) dan penyuntingan naskah writeup dibantu oleh model AI;
seluruh langkah analisis dan verifikasi dijalankan ulang secara lokal.
