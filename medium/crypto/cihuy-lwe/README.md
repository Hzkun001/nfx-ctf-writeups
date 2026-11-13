# Cihuy LWE

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Author | Illal |
| Lampiran / sumber | [assets/lwe.py](assets/lwe.py) |
| Verifikasi | Lokal; rekonstruksi rahasia ternary via Kannan embedding LLL/BKZ, seluruh 64 persamaan cocok, PRF counter SHA-256 terverifikasi |

## Ringkasan

Tantangan menyajikan skema **Learning With Errors (LWE)** berparameter kecil dengan modulus prima $q = 257$, dimensi rahasia $n = 40$, dan jumlah sampel $m = 64$. Kunci rahasia $s \in \{-1, 0, 1\}^{40}$ bertipe *small ternary secret*, sedangkan noise $e \in [-2, 2]^{64}$ memiliki magnitudo sangat kecil. Diberikan matriks publik $A \in \mathbb{Z}_q^{m \times n}$, vektor publik $b = A s + e \pmod q$, serta ciphertext 41 byte ($ct$).

Karena rasio sampel terhadap dimensi ($m/n = 1{,}6$) cukup tinggi dan noise sangat terbatas ($\|e\|_\infty \le 2$), pemulihan rahasia LWE dapat dipetakan menjadi kasus **Closest Vector Problem (CVP)** atau **Shortest Vector Problem (SVP)** melalui teknik **Kannan's embedding**. Basis kisi integer berdimensi 105 disusun dan direduksi menggunakan algoritma **LLL** dan **BKZ-20** via pustaka `fpylll`. Vektor terpendek yang dihasilkan memuat pasangan $(e, -s, 4)$. Kunci $s$ yang dipulihkan kemudian digunakan sebagai seed untuk PRF berbasis SHA-256 counter, membuka dekripsi ciphertext dan menghasilkan flag.

## Alur penyelesaian

### 1. Pemeriksaan awal & model matematis

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `assets/lwe.py` | 13.064 B | `6a996ad10f8ee04aed2f3befe3f1268b2b4bff8c9d6c6740b2cd88db0a623e1c` |

Struktur data pada berkas soal terdiri dari:
- Modulus $q = 257$
- Dimensi rahasia $n = 40$
- Jumlah baris/sampel $m = 64$
- Matriks publik $A$ berukuran $64 \times 40$
- Vektor publik $b$ berukuran 64 elemen
- Ciphertext $ct$ berupa string heksadesimal sepanjang 82 karakter (41 byte)

Persamaan pembentuk sampel adalah:

$$b \equiv A s + e \pmod{257}$$

Karakteristik komponen rahasia:
- Vektor rahasia $s \in \{-1, 0, 1\}^{40}$ dengan norm kuadrat $\|s\|^2 = 25$.
- Vektor galat $e \in [-2, 2]^{64}$ dengan norm kuadrat $\|e\|^2 = 103$.

### 2. Konstruksi kisi Kannan's embedding

Hubungan linear modular $A s + e \equiv b \pmod q$ dapat dinyatakan sebagai keberadaan vektor bilangan bulat $k \in \mathbb{Z}^{64}$ sedemikian hingga:

$$A s - q k - b = -e$$

Kita dapat mengonstruksi kisi baris $\mathbf{B}$ berdimensi $(m + n + 1) \times (m + n + 1) = 105 \times 105$ dengan faktor skala embedding $T = 4$:

$$\mathbf{B} = \begin{pmatrix} q \cdot \mathbf{I}_{64} & \mathbf{0}_{64 \times 40} & \mathbf{0}_{64 \times 1} \\ \mathbf{A}^T & \mathbf{I}_{40} & \mathbf{0}_{40 \times 1} \\ \mathbf{b}^T & \mathbf{0}_{1 \times 40} & T \end{pmatrix}$$

Jika kita mengalikan basis baris $\mathbf{B}$ dari kiri dengan vektor kombinasi bulat $\mathbf{w} = (-k^T, s^T, -1)$:

$$\mathbf{w} \mathbf{B} = (-k^T q + s^T A^T - b^T, \; s^T, \; -T) = (-e^T, \; s^T, \; -T)$$

Norm Euclidean dari vektor kisi target ini adalah:

$$\|\mathbf{v}_{\text{target}}\| = \sqrt{\|e\|^2 + \|s\|^2 + T^2} = \sqrt{103 + 25 + 16} = \sqrt{144} = 12$$

Berdasarkan *Gaussian heuristic*, panjang vektor terpendek yang diharapkan pada kisi acak berdimensi 105 dengan determinan $\det(\mathbf{B}) = q^{64} \cdot T = 257^{64} \cdot 4$ adalah jauh lebih besar ($\approx 70$). Perbedaan celah (*gap*) ini memastikan bahwa vektor $(\pm e, \mp s, \pm 4)$ akan muncul di antara baris-baris pertama setelah reduksi basis kisi.

Reduksi dilakukan dengan:
1. `LLL.reduction(basis, delta=0.99)`
2. `BKZ.reduction(basis, BKZ.Param(block_size=20, max_loops=4))`

Proses reduksi selesai dalam waktu kurang dari satu detik pada mesin lokal.

### 3. Derivasi keystream PRF & dekripsi flag

Setelah baris yang memiliki nilai kolom terakhir $\pm 4$ ditemukan:
1. Ekstrak vektor $s$ dan $e$.
2. Verifikasi keabsahan dengan memastikan bahwa $(A s + e) \pmod{257} == b$ untuk seluruh 64 sampel.
3. Representasikan elemen bertanda $s_i \in \{-1, 0, 1\}$ ke dalam bentuk unsigned byte (di mana $-1 \equiv 255 = \text{0xFF}$). Ini menghasilkan seed sepanjang 40 byte.
4. Fungsi pembangkit keystream pada soal menggunakan PRF berbasis HMAC/counter SHA-256:

$$\text{stream} = \text{SHA256}(\text{seed} \parallel \text{counter.to\_bytes}(4, \text{'big'}))$$

Untuk ciphertext sepanjang 41 byte, dibutuhkan counter 0 dan 1 (menghasilkan 64 byte keystream, diambil 41 byte pertama). Operasi XOR antara ciphertext dan keystream menghasilkan string flag.

## Flag

```text
NFXCTF{l4tt1c3_sm4ll_s3cr3t_LWE_7e2a0195}
```

Format flag `NFXCTF{...}` terverifikasi secara matematis dan lolos uji integritas dekripsi.

## Reproduksi

Dependensi yang dibutuhkan tercantum pada [requirements.txt](requirements.txt) (`fpylll` dan `cysignals`).

```bash
# 1. Siapkan virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Jalankan solver
python3 solve.py

# 3. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi hash masukan, memuat matriks $A$ dan vektor $b$, menyusun basis kisi berdimensi 105, melakukan reduksi LLL + BKZ-20, memverifikasi seluruh persamaan sampel, dan mendekripsi ciphertext. [test_solve.py](test_solve.py) menguji keaslian berkas tantangan, batasan parameter, integritas solusi, dan deteksi modifikasi berkas input.

## Bukti

- Berkas tantangan terverifikasi: [assets/lwe.py](assets/lwe.py) (SHA256: `6a996ad10f8ee04aed2f3befe3f1268b2b4bff8c9d6c6740b2cd88db0a623e1c`).
- Solver teruji: [solve.py](solve.py).
- Pengujian unit otomatis: [test_solve.py](test_solve.py).

## Penggunaan AI

Pengembangan solver dan penyusunan kisi embedding Kannan dibantu oleh model AI untuk memformulasikan relasi reduksi matriks $(m+n+1) \times (m+n+1)$ serta verifikasi batasan norm secara eksak.
