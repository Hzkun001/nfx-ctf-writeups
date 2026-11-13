# RSA Coppersmith Cihuy

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Author | Illal |
| Lampiran / sumber | [assets/chall.py](assets/chall.py) |
| Verifikasi | Lokal; reduksi kisi Howgrave-Graham LLL via python-flint, pemulihan 212-bit LSB p, faktorisasi modulus n 1024-bit, dekripsi flag RSA |

## Ringkasan

Tantangan mengimplementasikan kriptosistem **RSA 1024-bit** ($n = p \times q$) dengan eksponen publik standar $e = 65537$. Diberikan ciphertext $c$, modulus publik $n$, serta bocoran 300 bit tertinggi (*Most Significant Bits* / MSB) dari faktor prima $p$ (di mana ukuran $p \approx 512$ bit dan bit yang belum diketahui berukuran 212 bit).

Berdasarkan teorema **Coppersmith** untuk pemulihan faktor prima dengan bit parsial (*factoring with known high bits* melalui formulasi Howgrave-Graham), jika diketahui setidaknya:

$$k > \frac{1}{2} \log_2(p) \approx \frac{1}{4} \log_2(n) = 256 \text{ bit}$$

maka sisa bit rendah yang belum diketahui ($x_0 < 2^{212}$) dapat dihitung dalam waktu polinomial sebagai akar integer kecil dari polinomial monik univariat:

$$f(x) = a + x \equiv 0 \pmod p$$

Karena jumlah bit MSB yang diketahui adalah 300 bit ($300 > 256$), batas teoritis terpenuhi dengan margin aman. Basis kisi integer disusun dan direduksi menggunakan algoritma **LLL** via pustaka `python-flint`, memulihkan akar $x_0$ secara instan ($< 0{,}1$ detik), memfaktorkan $n$, dan mendekripsi flag.

## Alur penyelesaian

### 1. Pemeriksaan awal & parameter berkas

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `assets/chall.py` | 674 B | `be1635552e0b4fd1d83259896b5dee6498d7bbd944c82d0292c1b0fc32d33cf1` |

Parameter pada berkas soal:
- Modulus $n$: integer 1024-bit ($n \approx 2^{1024}$)
- Eksponen publik $e = 65537$
- Ciphertext $c$: integer 1024-bit
- `p_msb`: representasi heksadesimal 300 bit teratas dari $p$
- `unknown_bits`: 212 bit

Nilai perkiraan awal $a$ dan batas akar $X$:
$$a = p_{\text{msb}} \ll 212$$
$$X = 2^{212}$$

Sehingga faktor prima yang dicari adalah $p = a + x_0$ dengan $|x_0| < X$.

### 2. Konstruksi kisi Coppersmith / Howgrave-Graham

Untuk mencari akar kecil $x_0$ dari $f(x) = a + x \pmod p$, dibentuk kumpulan polinomial berderajat rendah yang memiliki kelipatan modulo $p^m$:

$$g_{i}(x) = n^{m-i} f(x)^i \quad (0 \le i < m)$$
$$h_{j}(x) = x^j f(x)^m \quad (0 \le j < t)$$

Total dimensi kisi yang dibentuk adalah $d = m + t$. Untuk $m = 3$ dan $t = 3$, dimensi kisi adalah $6 \times 6$.

Matriks basis kisi $\mathbf{M}$ disusun dari vektor koefisien tiap polinomial yang diskalakan dengan perpangkatan batas atas akar $X$:

$$\mathbf{M}_{r, k} = \text{coeff}_k(P_r) \cdot X^k$$

Reduksi basis kisi menggunakan algoritma **LLL** (`fmpz_mat.lll()`) menghasilkan vektor pendek yang koefisiennya merepresentasikan polinomial $g(x) \in \mathbb{Z}[x]$ sedemikian hingga seluruh akarnya di atas modulus $p$ juga merupakan akar eksak atas himpunan bilangan bulat $\mathbb{Z}$.

### 3. Pemulihan faktor prima dan dekripsi flag

1. Polinomial hasil reduksi LLL difaktorkan atau dicari akarnya di $\mathbb{Z}$ menggunakan `g.roots()`.
2. Ditemukan akar tunggal non-negatif $x_0 < X$:
   $$p = a + x_0$$
3. Menghitung $\gcd(p, n)$ memastikan bahwa $p$ membagi habis $n$:
   $$q = \frac{n}{p}$$
4. Menghitung totient Euler:
   $$\phi(n) = (p - 1)(q - 1)$$
5. Menghitung eksponen privat:
   $$d \equiv e^{-1} \pmod{\phi(n)}$$
6. Dekripsi RSA standar:
   $$m \equiv c^d \pmod n$$
7. Konversi nilai numerik $m$ ke dalam representasi byte menghasilkan string flag.

## Flag

```text
NFXCTF{C0pp3rsm1th_p4rt14l_k3y_3xp0sur3_9617eda9}
```

## Reproduksi

Dependensi tercantum pada [requirements.txt](requirements.txt) (`python-flint` dan `pycryptodome`).

```bash
# 1. Siapkan virtual environment dan pasang dependensi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Jalankan solver
python3 solve.py

# 3. Jalankan pengujian unit otomatis
python3 -m unittest -v
```

Keluaran solver:
```text
[+] Recovered Flag: NFXCTF{C0pp3rsm1th_p4rt14l_k3y_3xp0sur3_9617eda9}
```

## Bukti

- Berkas implementasi soal: [assets/chall.py](assets/chall.py).
- Skrip solver kisi Howgrave-Graham LLL: [solve.py](solve.py).
- Pengujian unit otomatis: [test_solve.py](test_solve.py).

## Penggunaan AI

Formulasi kisi Coppersmith Howgrave-Graham berdimensi $6 \times 6$ dan integrasi FLINT integer polynomial solver dioptimalkan dengan bantuan AI untuk memastikan reduksi LLL berjalan cepat dan deterministik.
