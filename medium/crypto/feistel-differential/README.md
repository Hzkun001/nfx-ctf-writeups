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
dan permutasi bit/nibble. Diberikan berkas `pairs.txt` berisi kumpulan pasangan
plaintext-ciphertext dengan perbedaan input $\Delta P$ tertentu, serta `flag.enc`.

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

Tabel Distribusi Diferensial (DDT) SBOX dihitung untuk seluruh kemungkinan
input diff $\Delta x \in [0, 15]$ dan output diff $\Delta y \in [0, 15]$.
SBOX memiliki diferensial berprobabilitas tinggi (hingga $p = 6/16$ atau $8/16$
pada pola tertentu). Fungsi permutasi bit menukar posisi pasangan nibble
$0 \leftrightarrow 1$ dan $2 \leftrightarrow 3$ tanpa mengubah nilai nibble.

### 2. Pelacakan karakteristik diferensial (*trail*)

Dengan DDT dan permutasi yang merupakan involusi, kita dapat menelusuri
karakteristik diferensial berprobabilitas tertinggi dari ronde awal:

$$(\Delta L_0, \Delta R_0) \xrightarrow{r\text{ ronde}} (\Delta L_r, \Delta R_r)$$

Untuk ronde terakhir ke-7:
$$C_L = R_6, \quad C_R = L_6 \oplus F(R_6, K_6)$$
Perbedaan pada ciphertext memenuhi:
$$\Delta C_L = \Delta R_6, \quad \Delta C_R = \Delta L_6 \oplus \Delta F(R_6, K_6)$$

Jika kita memilih pasangan dengan $\Delta C_L = \Delta R_6$ (sesuai prediksi
karakteristik 6-round), maka output diferensial dari $F$ adalah:
$$\Delta F = \Delta C_R \oplus \Delta L_6$$

### 3. Pemulihan kunci ronde (*round peeling*)

Karena $F$ beroperasi secara independen per nibble sebelum permutasi, kandidat
nibble subkunci $K_{6, \text{nib}}$ dapat di-*voting* satu per satu:

1. Untuk setiap pasangan valid, hitung output diff pada nibble pasangan.
2. Uji 16 kemungkinan nilai nibble subkunci. Jika $\text{SBOX}(x_1 \oplus k) \oplus \text{SBOX}(x_2 \oplus k) == \Delta y$, tambahkan *vote*.
3. Nibble dengan suara terbanyak dipilih sebagai subkunci ronde tersebut.
4. Lakukan dekripsi satu ronde ke belakang (*peel*) pada seluruh ciphertext menggunakan subkunci yang baru diperoleh.
5. Ulangi proses untuk memulihkan $K_5$, $K_4$, $K_3$, $K_2$, dan $K_1$.

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

```bash
cd medium/crypto/feistel-differential
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
python3 test_solve.py
```

## Bukti

- [assets/cipher.py](assets/cipher.py): implementasi enkripsi cipher Feistel 7-round.
- [assets/pairs.txt](assets/pairs.txt): pasangan plaintext-ciphertext dengan selisih input tertentu.
- [assets/flag.enc](assets/flag.enc): berkas keluaran flag terenkripsi.
- [solve.py](solve.py): skrip analisis diferensial, penghitungan DDT, dan rekonstruksi subkunci.
- [test_solve.py](test_solve.py): pengujian unit untuk verifikasi subkunci dan validasi flag.

## Penggunaan AI

Analisis DDT, propagasi *trail*, dan formulasi *round peeling* dikembangkan
dengan bantuan AI untuk mempercepat komputasi voting pada dataset `pairs.txt`.
