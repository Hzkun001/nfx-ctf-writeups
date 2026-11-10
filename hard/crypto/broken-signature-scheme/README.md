# Broken Signature Scheme

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Hard |
| Input yang dianalisis | [assets/output.txt](assets/output.txt) dan [assets/challenge.py](assets/challenge.py) dari soal |
| Verifikasi | Lokal: tanda tangan palsu, faktorisasi Fermat, 20 bit bocor, dan tag AES-GCM semuanya terverifikasi |

## Ringkasan

Soal berlapis tiga. **Layer 1**: skema tanda tangan RSA yang *multiplicative*
tanpa hash dan tanpa padding (`sig(m) = m^d mod N`), sehingga produk dari
beberapa tanda tangan yang sah menghasilkan tanda tangan sah untuk produk
pesannya — dipakai untuk memalsukan tanda tangan atas `give-me-the-flag`.
**Layer 2**: modulus 2047-bit dengan dua faktor prima 1024-bit yang
sangat berdekatan (`q ≈ p + 2^300`), sehingga **metode Fermat** langsung
menemukan faktor pada kandidat pertama. **Layer 3**: `key =
SHA256(p_bytes || q_bytes)` membuka ciphertext AES-GCM yang berisi flag.

## Alur penyelesaian

### 1. Pemeriksaan awal

`output.txt` (4.392 byte, SHA256
`a89d84089e4e67617d57a223474dab7ced37eda40d5b2df31f4b8454c28d4eb7`) berisi:

| Field | Nilai |
| --- | --- |
| `N` | 2047-bit (hex) |
| `e` | 65537 |
| `leak` | `0x69252`, posisi bit 500, 20 bit |
| `delta_bits` | 300 |
| `valid_sigs` | 6 pasangan `(msg, sig)` |
| `target_msg_hex` | `give-me-the-flag` |
| `flag_cipher` | nonce 12 byte + ciphertext + tag 16 byte (AES-GCM) |

`challenge.py` hanya pemuat informasi; tidak dieksekusi.

### 2. Layer 1 — pemalsuan tanda tangan multiplicative

Karena `sig(m) = m^d mod N` tanpa hash/padding, berlaku
`sig(m1)·sig(m2) ≡ sig(m1·m2) (mod N)`. Entri 1, 2, dan 3 jika dikalikan
menghasilkan target `give-me-the-flag` modulo N, sehingga produk ketiga
tanda tangannya adalah tanda tangan sah untuk target tersebut. Semua enam
tanda tangan yang diberikan diverifikasi dengan `e = 65537`, dan tanda
tangan palsu juga diverifikasi dengan `sig^e ≡ target (mod N)`.

### 3. Layer 2 — faktorisasi Fermat

Ditulis `N = a² − b²` dengan `a = ceil(√N)`. Pada instance ini `a² − N`
sudah merupakan kuadrat sempurna pada kandidat pertama, sehingga
`p = a − b` dan `q = a + b` langsung. Gap aktual `q − p = 2^300 + 2104`,
jauh di bawah skala yang bisa ditahan modulus 2047-bit pada langkah Fermat
pertama; tidak diperlukan reduksi lattice ataupun Coppersmith.

Verifikasi independen dari 20 bit yang bocor:

```python
((p >> 500) & ((1 << 20) - 1)) == 0x69252
```

Solver juga memeriksa `p*q == N`, kecocokan bit bocor, dan relasi gap.
Setelah faktorisasi, tanda tangan palsu dibandingkan dengan
`target^d mod N` memakai eksponen privat hasil — hasilnya cocok.

### 4. Layer 3 — dekripsi terautentikasi

Enkode `p` dan `q` sebagai byte big-endian minimal tanpa tanda (kecil lebih
dulu; masing-masing 128 byte pada instance ini), lalu turunkan:

```text
key = SHA256(p_bytes || q_bytes)
```

Ciphertext AES-GCM dibuka dengan kunci itu; **tag terverifikasi**, jadi
plaintext terautentikasi tanpa menebak format flag.

## Flag

```text
NXCTF{mult1_l4y3r_l4tt1c3_r54_s1gn4tur3_hnp_8c211ad6b5a6}
```

Prefiks **NXCTF** dipertahankan sesuai plaintext hasil dekripsi. Bukti
*accepted* platform belum tersedia.

## Reproduksi

Dependensi: Python 3.10+ dan **pycryptodome**.

```bash
python3 solve.py            # memakai assets/output.txt
python3 -m unittest -v      # tiga tes
```

[Solver](solve.py) memeriksa SHA256 input, memverifikasi keenam tanda
tangan, mencari subset yang berproduk sama dengan target, memfaktorisasi
dengan Fermat, memeriksa bit bocor, menyilangkan tanda tangan palsu dengan
kunci privat, lalu membuka AES-GCM. Tiga tes mencakup reproduksi flag,
kecocokan bit bocor, dan penolakan input yang diubah. Berkas masukan tidak
diubah; faktor dan tanda tangan palsu tidak dimasukkan ke repo.

## Bukti

- [output.txt asli](assets/output.txt), SHA256 `a89d8408…d4eb7`.
- [challenge.py](assets/challenge.py) sebagai referensi skema.

## Penggunaan AI

OpenAI Codex membantu merancang pencarian subset tanda tangan, faktorisasi
Fermat, penurunan kunci SHA256(p||q), dan penyuntingan writeup.
