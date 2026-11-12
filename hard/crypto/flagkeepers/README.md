# FlagKeepers

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Hard |
| Author | Ariaf |
| Lampiran / sumber | [assets/app.py](assets/app.py) (pada repositori soal: `crypto/FlagKeepers/app.py`) |
| Layanan | `nc s1.nfx.my.id 44421` |
| Verifikasi | Flag diperoleh dari instance live saat sesi kompetisi; aritmetika GF(2^128) dan pemulihan GCD polinomial teruji valid |

## Ringkasan

**FlagKeepers** adalah layanan audit dan disaster recovery berbasis AES-GCM.
Layanan ini mengelola dua konteks enkripsi: `key_a` (Audit Log) dan `key_b`
(Recovery Log). Celah fatalnya adalah kedua konteks berbagi satu nilai
**session nonce** yang sama persis:

```python
self.session_nonce = os.urandom(12)
```

Penggunaan kembali nonce di bawah kunci yang sama (`key_b`) pada menu
**Option 2** (Recovery Log) memicu kerentanan klasik **AES-GCM Forbidden Attack**.
Tag autentikasi AES-GCM dihitung sebagai evaluasi polinomial GHASH di medan
Galois $\text{GF}(2^{128})$ ditambah term masking enkripsi counter nol:

$$T = \text{GHASH}_H(C) \oplus E_K(J_0)$$

Dengan mengumpulkan ciphertext dan tag dari nonce yang sama, suku $E_K(J_0)$
dapat dieliminasi melalui operasi XOR antara dua tag. Menghitung $\gcd$
(Greatest Common Divisor) dari polinomial selisih di $\text{GF}(2^{128})$
memungkinkan pemulihan *authentication subkey* $H_b$. Dari subkey ini,
keystream AES-CTR di-XOR untuk memalsukan ciphertext dan tag valid untuk
payload `admin = True`, lalu dikirimkan ke menu disaster recovery (**Option 4**)
guna mengekstrak flag.

## Alur penyelesaian

### 1. Pemeriksaan awal

Berkas layanan `app.py`:

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `app.py` | 2.222 byte | `5a4aa4e5d0425fb479283507f049ca4f6a68c20bb6d62def758568dd868104ba` |

Struktur enkripsi dan counter:
- `Option 1` (Audit): mengenkripsi dengan `key_a` dan `session_nonce`, lalu mengubah variabel `idx = (idx + 16) % 256`.
- `Option 2` (Recovery): mengenkripsi dengan `key_b` dan `session_nonce`, lalu mengubah `idx = (idx - 16) % 256`.
- `Option 4` (Verify & Flag): meminta ciphertext dan tag, mendekripsi dengan `key_b`, memverifikasi tag GCM, lalu mengecek apakah string `b"admin = True"` ada pada `msg[:idx]`. Jika lolos, flag `/app/flag.txt` dicetak.

### 2. Formulasi serangan polinomial GHASH

Blok data GHASH dibentuk dari ciphertext yang dipad 16 byte serta blok panjang:
$$X = C_1 \parallel C_2 \parallel \dots \parallel C_m \parallel L$$
di mana $L = \text{len}(AAD) \parallel \text{len}(C)$.

Tag autentikasi untuk pesan $i$:
$$T_i = C_{i,1} H^m \oplus C_{i,2} H^{m-1} \oplus \dots \oplus L_i H \oplus S$$
dengan $S = E_{K_b}(J_0)$.

Ketika dua pesan berbeda $C_1$ dan $C_2$ dienkripsi dengan nonce yang sama di bawah $K_b$:
$$T_1 \oplus T_2 = \sum_{k=1}^m (C_{1,k} \oplus C_{2,k}) H^{m+1-k} \oplus (L_1 \oplus L_2) H$$

Persamaan di atas merupakan polinomial $P(x)$ di atas medan Galois $\text{GF}(2^{128})$
dengan polinomial reduksi $f(x) = x^{128} + x^7 + x^2 + x + 1$ (konstanta `0xE1...`).
Subkey $H_b$ yang asli merupakan salah satu akar dari $P(x)$.

### 3. Pemulihan subkey $H_b$ dengan polinomial GCD

Dengan mengambil 3 sampel recovery log $(PT_1, CT_1, T_1)$, $(PT_2, CT_2, T_2)$, dan $(PT_3, CT_3, T_3)$, kita menyusun dua polinomial selisih:
- $P_{12}(x) = \Delta \text{GHASH}_{12}(x) \oplus (T_1 \oplus T_2)$
- $P_{13}(x) = \Delta \text{GHASH}_{13}(x) \oplus (T_1 \oplus T_3)$

Keduanya berbagi faktor linier $(x \oplus H_b)$. Menggunakan algoritma Euclidean:
$$G(x) = \gcd(P_{12}(x), P_{13}(x))$$
Komputasi GCD di $\text{GF}(2^{128})$ menghasilkan polinomial berderajat 1:
$$G(x) = x \oplus H_b$$
Sehingga nilai $H_b$ berhasil dipulihkan dalam waktu $< 0,1$ detik.

Term masking $S_b$ kemudian dihitung:
$$S_b = T_1 \oplus \text{GHASH}(H_b, C_1)$$

### 4. Sinkronisasi nilai `idx` dan pemalsuan tag

Untuk memenuhi syarat `b"admin = True" in msg[:idx]`:
1. Saat awal, `idx = 0`.
2. Setelah 3 kali memanggil `Option 2`:
   $$\text{idx} = (0 - 16 \times 3) \bmod 256 = 208$$
3. Kita panggil `Option 1` sebanyak 2 kali:
   $$\text{idx} = (208 + 16 \times 2) \bmod 256 = 240$$
4. Keystream dipulihkan dari XOR pasangan pertama:
   $$\text{Keystream} = PT_1 \oplus CT_1$$
5. Plaintext target adalah `target_pt = b"admin = True"`. Ciphertext palsu:
   $$CT_{forged} = target\_pt \oplus \text{Keystream}[:\text{len}(target\_pt)]$$
6. Tag autentikasi palsu dihitung secara deterministik:
   $$Tag_{forged} = \text{GHASH}(H_b, CT_{forged}) \oplus S_b$$

### 5. Verifikasi hasil

Payload palsu dikirimkan ke menu `Option 4`. Server mendekripsi pesan dengan sukses, memverifikasi tag GCM, memvalidasi substring `admin = True` pada `msg[:240]`, dan memberikan flag.

## Flag

```text
NFX{gcm_f0rb1dd3n_4tt4ck_du4l_t4g_c0ll1s10n_m4st3r}
```

## Reproduksi

Dependensi: Python 3.10+ dan **PyCryptodome** (`pip install -r requirements.txt`).

Jalankan solver terhadap instance target:

```bash
python3 solve.py --host s1.nfx.my.id --port 44421
```

Jalankan unit test matematika:

```bash
python3 -m unittest -v
```

## Bukti

- [assets/app.py](assets/app.py): kode sumber layanan FlagKeepers.
- [solve.py](solve.py): implementasi penuh aritmetika medan $\text{GF}(2^{128})$, GCD polinomial, dan eksploitasi socket.
- [test_solve.py](test_solve.py): unit test pembuktian sifat invers medan dan ketepatan faktorisasi GCD.
