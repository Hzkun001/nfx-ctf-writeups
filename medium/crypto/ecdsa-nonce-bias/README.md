# ECDSA Nonce Bias

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Input yang dianalisis | [assets/output.txt](assets/output.txt), [assets/pubkey.pem](assets/pubkey.pem), [assets/challenge.py](assets/challenge.py) |
| Verifikasi | Lokal: 200 tanda tangan terverifikasi, kunci publik cocok, semua nonce < 2^248, tag AES-GCM valid |

## Ringkasan

Soal memberi 200 tanda tangan ECDSA pada kurva **secp256k1** dengan **nonce
yang bias 8 bit**: setiap nonce `k < 2^248` (8 bit teratas selalu 0,
`top8_k = 0`, `K_BITS = 248`). Ini kasus klasik **Hidden Number Problem
(HNP)**: dari `s·k ≡ h + r·d (mod n)` kita dapat `k = a·d + b (mod n)`
dengan `a = r/s`, `b = h/s`. Dengan 48 tanda tangan cukup untuk menyusun
**lattice dimensi 50** yang direduksi LLL; vektor pendeknya mengandung
kunci privat `d`. Kunci itu diverifikasi terhadap public key, lalu
`key = SHA256(d 32-byte big-endian)` membuka ciphertext AES-GCM berisi flag.

## Alur penyelesaian

### 1. Pemeriksaan awal

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `output.txt` | 69.107 B | `74f93d9a…23aa73e9` |
| `pubkey.pem` | 174 B | `500c7aaa…3360212` |
| `challenge.py` | 1.010 B | `b2df03ad…64417063` |

`challenge.py` adalah ringkasan untuk peserta (tidak dieksekusi). `output.txt`
memuat `N` (orde secp256k1), 200 entri `(r, s, h, msg, K_BITS, top8_k)`,
`pubkey_pem`, dan `flag_ciphertext` (nonce + ct + tag AES-GCM).

### 2. Susun persamaan HNP

Untuk setiap tanda tangan, dengan `n` = orde kurva:

```text
s_i · k_i ≡ h_i + r_i · d  (mod n)
a_i = r_i · s_i⁻¹  (mod n)
b_i = h_i · s_i⁻¹  (mod n)
k_i = a_i · d + b_i  (mod n),   0 < k_i < B = 2^248
```

### 3. Lattice + LLL

Ambil **48** tanda tangan pertama, `C = floor(n/B) = 255`, `M = floor(n/2)`.
Lattice **dimensi 50** tersusun dari:

- 48 baris pertama: diagonal berisi `n·C`;
- baris ke-49: `(a_1·C, …, a_48·C, 1, 0)` — koordinat ini menghasilkan `d`;
- baris terakhir: `((b_1−B/2)·C, …, (b_48−B/2)·C, 0, M)`.

Kombinasi yang tepat menghasilkan koordinat pertama `C·(k_i − B/2)` yang
kecil, koordinat privat `d mod n`, dan koordinat terakhir `M`. LLL
(`delta=0.99`) menemukan vektor pendek; kandidat dari kolom privat diuji
terhadap public key. Pada instance ini kandidat yang cocok ditemukan dalam
sekitar **0,43 detik** pada reduksi pertama.

### 4. Verifikasi menyeluruh

Kandidat kunci diperiksa dengan semua **200** tanda tangan (bukan hanya 48):

- SHA256 setiap `msg` cocok dengan `h`;
- semua tanda tangan terverifikasi terhadap `pubkey.pem` (yang juga sama
  dengan `pubkey_pem` di dalam `output.txt`);
- `d` menghasilkan titik publik yang sama persis dengan PEM;
- semua nonce hasil rekonstruksi `k = (h + r·d)/s mod n` positif dan `< 2^248`;
- AES-GCM dengan `key = SHA256(d.to_bytes(32, "big"))` **terautentikasi** saat
  dekripsi — format flag tidak dipakai untuk menebak kunci.

## Flag

```text
NXCTF{ecds4_hnp_n0nc3_b14s_8b1t_l4tt1c3_a3d2ae498097}
```

Prefiks **NXCTF** dipertahankan sesuai plaintext; placeholder
`NFX{your_flag_here}` tidak dipakai. Bukti *accepted* platform belum tersedia.

## Reproduksi

Dependensi: Python 3.11, `fpylll`, `cysignals`, `cryptography`
(lihat [requirements.txt](requirements.txt)).

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python solve.py
.venv/bin/python -m unittest -v
```

[Solver](solve.py) memeriksa SHA256 ketiga input, memverifikasi seluruh
tanda tangan, menyusun lattice 48 tanda tangan, menjalankan LLL, lalu
mendekripsi AES-GCM. Lima tes mencakup hash input, metadata bias, hash
pesan, reproduksi flag, dan penolakan input yang diubah. Tanpa `fpylll`,
tiga tes hash tetap jalan dan dua tes lattice di-skip.

## Bukti

- [output.txt](assets/output.txt), [pubkey.pem](assets/pubkey.pem),
  [challenge.py](assets/challenge.py) dengan SHA256 di atas.

## Penggunaan AI

OpenAI Codex membantu menyusun lattice HNP, pemilihan parameter
C/M, validasi 200 tanda tangan, dan penyuntingan writeup.
