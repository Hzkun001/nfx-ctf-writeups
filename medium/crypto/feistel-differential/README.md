# Feistel Differential

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Author | Illal |
| Lampiran / sumber | [assets/cipher.py](assets/cipher.py), [assets/flag.enc](assets/flag.enc), [assets/pairs.txt](assets/pairs.txt) |
| Verifikasi | Lokal: rekonstruksi karakteristik diferensial 6-round berhasil, 7 subkunci (112-bit) memverifikasi seluruh pasangan P/C, flag terdekripsi sempurna |

## Ringkasan

Soal menyediakan implementasi cipher Feistel 7-round dengan ukuran blok 32-bit
(dibagi menjadi dua paruh 16-bit $L$ dan $R$). Kunci master berukuran 112-bit
yang dipecah menjadi 7 subkunci independen 16-bit ($K_0$ hingga $K_6$).
Fungsi ronde $F(x, K)$ melakukan XOR terhadap subkunci, substitusi 4-bit SBOX,
dan permutasi nibble. Diberikan `pairs.txt` dan `flag.enc`.

`pairs.txt` memuat **14 blok**, masing-masing diawali baris
`# input difference: <ΔP>` lalu **20.000 baris** `P C1 C2`, dengan
`C1 = enc(P)` dan `C2 = enc(P ⊕ ΔP)`. Jadi tiap baris adalah satu pasangan
plaintext yang selisihnya tepat $\Delta P$. Blok pertama memakai
$\Delta P = \mathtt{0000000a}$ (hanya nibble terbawah $R$ yang aktif, bernilai
`0xa`).

Celah utama terletak pada properti diferensial SBOX 4-bit dan ketiadaan difusi
antarnibble yang kuat (permutasi hanya menukar posisi nibble tanpa pencampuran
linear seperti MDS matrix). Hal ini memungkinkan serangan **Differential
Cryptanalysis** untuk memulihkan subkunci ronde terakhir secara bertahap
(*round peeling*) dari $K_6$ mundur hingga $K_1$, lalu menyelesaikan $K_0$
secara langsung.

## Alur penyelesaian

### 1. Analisis fungsi ronde dan DDT SBOX

Blok 32-bit direpresentasikan sebagai $(L, R)$ masing-masing 16-bit (4 nibble).
Fungsi ronde:

```python
def round_f(x, k):
    y = x ^ k
    m = (
        SBOX[y & 0xF]
        | (SBOX[(y >> 4) & 0xF] << 4)
        | (SBOX[(y >> 8) & 0xF] << 8)
        | (SBOX[(y >> 12) & 0xF] << 12)
    )
    return permute(m)
```

`SBOX = [1,8,14,12,2,0,3,4,11,9,15,13,6,10,7,5]`. Tabel Distribusi Diferensial
(DDT) dihitung dari `DDT[Δx][Δy] = #{x : SBOX[x] ⊕ SBOX[x⊕Δx] = Δy}`. Entri
yang menjadi tulang punggung serangan:

| $\Delta x$ | $\Delta y$ terbaik | Jumlah | Probabilitas |
| --- | --- | ---: | --- |
| `0xa` | `0x5` | 12/16 | **3/4** |
| `0x5` | `0xa` | 8/16 | 1/2 |

Permutasi hanya menukar posisi pasangan nibble ($0 \leftrightarrow 1$,
$2 \leftrightarrow 3$) tanpa mengubah nilai nibble, jadi tidak ada difusi
antar-nibble; satu nibble aktif tetap satu nibble aktif sepanjang trail.

### 2. Pelacakan karakteristik diferensial (*trail*)

Mulai dari $(\Delta L_0, \Delta R_0) = (\mathtt{0000}, \mathtt{000a})$ dan ambil
transisi SBOX paling mungkin di tiap ronde. Karena hanya satu nibble aktif,
trail-nya bolak-balik antara `0xa` dan `0x5`:

| Setelah ronde | $\Delta L$ | $\Delta R$ | Prob. kumulatif |
| ---: | --- | --- | --- |
| 1 | `000a` | `0050` | 3/4 |
| 2 | `0050` | `0000` | 9/16 |
| 3 | `0000` | `0050` | 9/16 |
| 4 | `0050` | `000a` | 27/128 |
| 5 | `000a` | `0000` | ≈ 0,141 |
| 6 | `0000` | `000a` | ≈ 0,141 |

Karakteristik 6-round berakhir di $(\Delta L_6, \Delta R_6) =
(\mathtt{0000}, \mathtt{000a})$. Pada ronde terakhir (ke-7):
$$C_L = R_6, \quad C_R = L_6 \oplus F(R_6, K_6)$$
sehingga
$$\Delta C_L = \Delta R_6 = \mathtt{000a}, \quad
\Delta C_R = \Delta L_6 \oplus \Delta F(R_6, K_6).$$

Pasangan yang mengikuti karakteristik ini akan menunjukkan
$\Delta C_L = \mathtt{000a}$; pasangan dengan $\Delta C_L$ lain dibuang sebagai
*noise*. Untuk pasangan yang lolos filter, selisih keluaran $F$ pada ronde
terakhir adalah $\Delta F = \Delta C_R \oplus \Delta L_6$.

### 3. Pemulihan kunci ronde (*round peeling*)

Karena $F$ memproses tiap nibble secara independen sebelum permutasi, nibble
subkunci $K_6$ dipulihkan satu per satu dengan *voting*. Input SBOX pada ronde
ke-7 adalah nibble dari $C_L$, dan karena permutasi, keluaran nibble posisi
`nib` muncul di posisi pasangannya (`0↔1`, `2↔3`) pada $\Delta F$.

1. Saring pasangan yang $\Delta C_L = \mathtt{000a}$ (mengikuti karakteristik).
2. Untuk tiap pasangan, baca input diff dari $\Delta C_L$ dan output diff dari
   $\Delta F$ pada nibble yang bersangkutan.
3. Uji 16 nilai nibble kunci: jika $\text{SBOX}(x_1 \oplus k) \oplus
   \text{SBOX}(x_2 \oplus k) = \Delta y$, tambah satu *vote*.
4. Kunci yang benar muncul pada **setiap** pasangan valid, sedangkan kunci salah
   hanya sesekali, sehingga nibble dengan suara terbanyak menang telak. Ke-14
   blok $\Delta P$ ikut memberi suara agar seluruh nibble $K_6$ tercakup.
5. Kupas satu ronde (*peel*): dekripsi semua ciphertext satu ronde ke belakang
   dengan $K_6$, lalu ulangi untuk $K_5, K_4, K_3, K_2, K_1$.

### 4. Pemulihan $K_0$ dan dekripsi flag

Setelah cipher terkelupas hingga 1 ronde tersisa:
$$C_{1, L} = R_0, \quad C_{1, R} = L_0 \oplus F(R_0, K_0)$$
$$F(R_0, K_0) = L_0 \oplus C_{1, R}$$

Karena $F(x, K) = \text{permute}(\text{SBOX}(x \oplus K))$, maka:
$$K_0 = \text{SBOX}^{-1}(\text{permute}(L_0 \oplus C_{1, R})) \oplus R_0$$

Subkunci yang berhasil dipulihkan:
- $K_0 = \text{0xa383}$
- $K_1 = \text{0x3ab5}$
- $K_2 = \text{0xd728}$
- $K_3 = \text{0x7222}$
- $K_4 = \text{0x9737}$
- $K_5 = \text{0x7212}$
- $K_6 = \text{0xfdec}$

Subkunci ini diverifikasi terhadap seluruh pasangan di `pairs.txt`, menghasilkan
kecocokan 100%. Mendekripsi `flag.enc` dengan urutan subkunci menghasilkan flag.

## Flag

```text
NFXCTF{d1ff3r3nt14l_crypt0_pwn5_f31st3l_45322835}
```

## Reproduksi

Jalankan solver Python standar (tanpa dependensi eksternal):

Dari folder writeup ini:

```bash
python3 solve.py
```

Keluaran:
```text
[*] Performing differential cryptanalysis on 7-round Feistel...
[+] Recovered Subkeys: ['a383', '3ab5', 'd728', '7222', '9737', '7212', 'fdec']
[+] Flag: NFXCTF{d1ff3r3nt14l_crypt0_pwn5_f31st3l_45322835}
```

Jalankan pengujian unit:
```bash
python3 -m unittest -v
```

## Bukti

- [assets/cipher.py](assets/cipher.py): implementasi enkripsi cipher Feistel 7-round.
- [assets/pairs.txt](assets/pairs.txt): pasangan plaintext-ciphertext dengan selisih input tertentu.
- [assets/flag.enc](assets/flag.enc): berkas keluaran flag terenkripsi.
- [solve.py](solve.py): skrip analisis diferensial, penghitungan DDT, dan rekonstruksi subkunci.
- [test_solve.py](test_solve.py): pengujian unit untuk verifikasi subkunci dan validasi flag.
