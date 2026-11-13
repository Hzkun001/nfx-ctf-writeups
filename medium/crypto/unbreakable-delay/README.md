# Unbreakable Delay

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Author | Kad |
| Lampiran / sumber | [assets/sample_parameters.json](assets/sample_parameters.json) |
| Layanan | `nc s1.nfx.my.id 43118` |
| Verifikasi | Flag diperoleh dari instance live saat sesi kompetisi; aljabar Wesolowski VDF dan branch-and-bound factoring teruji |

## Ringkasan

Soal mengimplementasikan protokol **Verifiable Delay Function (VDF)** skema
**Wesolowski** di atas gelanggang $\mathbb{Z}_n$. Layanan mengharuskan prover
memberikan bukti matematis $\pi$ untuk mengevaluasi eksponensiasi berulang
dengan parameter delay sangat besar $T = 2^{256}$:

$$y \equiv g^{2^{2^{256}}} \pmod n$$

Secara normal, komputasi berulang ini didesain memerlukan waktu sekuensial
triliunan tahun tanpa bisa diparalelkan. Namun, server memberikan petunjuk
bocoran berupa nilai bitwise XOR antara dua faktor prima:

$$\text{hint} = p \oplus q$$

Dengan petunjuk tersebut, modulus RSA 2048-bit $n = p \times q$ dapat
difaktorkan secara cepat (~21 detik) menggunakan algoritma branch-and-bound
modulo $2^{i+1}$. Mengetahui faktor prima $p$ dan $q$ memungkinkan penghitungan
fungsi totient Euler $\phi(n) = (p-1)(q-1)$. Melalui reduksi eksponen
modulo $\phi(n)$, bukti $\pi$ untuk tantangan bilangan prima $l$ dapat
dihitung secara instan tanpa perlu menunggu penundaan sekuensial.

## Alur penyelesaian

### 1. Pemeriksaan awal

Koneksi ke layanan `nc s1.nfx.my.id 43118` memberikan parameter:
- Modulus $n$ (2048-bit)
- Petunjuk $p \oplus q$ (1022-bit)
- Target evaluasi $y \in \mathbb{Z}_n$
- Bilangan prima tantangan verifier $l \approx 2^{38}$

### 2. Faktorisasi $n$ dari petunjuk $p \oplus q$

Karena $p$ dan $q$ bilangan prima ganjil, bit ke-0 keduanya pasti bernilai 1
($p_0 = q_0 = 1$). Penelusuran dilakukan dari LSB ke MSB:

Untuk setiap bit $i$ dari 1 hingga 1024:
- Diberikan $K_i = (p \oplus q)_i$.
- Pasangan bit $(p_i, q_i)$ yang mungkin adalah $(0, K_i)$ atau $(1, 1 \oplus K_i)$.
- Setiap kandidat diperiksa apakah memenuhi kongruensi modular:
  $$(p_{test} \times q_{test}) \equiv n \pmod{2^{i+1}}$$

Karena kendala modular $2^{i+1}$ membatasi sisa cabang, jumlah kandidat
aktif pada setiap langkah sangat kecil dan stabil (ratusan hingga ribuan state).
Faktor prima 1024-bit $p$ dan $q$ berhasil dipulihkan secara penuh dalam ~21 detik.

### 3. Bypass Wesolowski VDF

Pada skema Wesolowski VDF, verifier menguji validitas bukti $\pi$ melalui relasi:

$$\pi^l \cdot g^r \equiv y \pmod n \quad \text{dengan } r = 2^T \bmod l$$

Di mana $T = 2^{256}$. Pembagian Euclidean pada eksponen menghasilkan:
$$2^T = q_{div} \cdot l + r \implies q_{div} = \frac{2^T - r}{l}$$

Bagi pihak luar yang tidak mengetahui faktorisasi $n$, menghitung $g^{q_{div}} \pmod n$
tetap memerlukan operasi sekuensial panjang. Namun, karena $p$ dan $q$ telah
diketahui:
1. Hitung $\phi(n) = (p-1)(q-1)$.
2. Karena $\gcd(l, \phi(n)) = 1$, invers modular $l^{-1} \pmod{\phi(n)}$ dapat dihitung dengan mudah.
3. Eksponen $2^T \bmod \phi(n)$ dihitung instan melalui eksponensiasi modular:
   $$\text{two\_t\_mod\_phi} = \text{pow}(2, 2^{256}, \phi(n))$$
4. Eksponen bukti $q_{div}$ modulo $\phi(n)$:
   $$q_{div} \equiv (2^T - r) \cdot l^{-1} \pmod{\phi(n)}$$
5. Bukti valid dihitung:
   $$\pi \equiv g^{q_{div}} \pmod n$$
   (dengan basis generator $g = 3$).

### 4. Verifikasi hasil

Nilai $\pi$ diuji secara lokal:
$$(\pi^l \cdot g^r) \bmod n \stackrel{?}{=} y$$
Persamaan bernilai identik (`True`). Bukti $\pi$ dikirimkan ke server melalui
socket koneksi, dan server langsung merespons dengan flag kompetisi.

## Flag

```text
NFX{x0r_f4ct0r1ng_4nd_f4st_vdf_byp4ss_m4k3s_1t_h4rd}
```

## Reproduksi

Jalankan verifikasi offline menggunakan parameter pengujian:

```bash
python3 solve.py
```

Jalankan terhadap server live (bila aktif):

```bash
python3 solve.py --remote --host s1.nfx.my.id --port 43118
```

Uji unit test:

```bash
python3 -m unittest -v
```

## Bukti

- [assets/sample_parameters.json](assets/sample_parameters.json): rekaman parameter numerik sesi kompetisi.
- [solve.py](solve.py): implementasi branch-and-bound factoring dan kalkulasi bukti VDF.
- [test_solve.py](test_solve.py): unit test aljabar dan verifikasi struktur VDF.

## Penggunaan AI

Analisis pereduksian relasi $p \oplus q$ menjadi pencarian branch-and-bound serta bypass pembuktian interaktif VDF Pietrzak dibantu oleh AI.
