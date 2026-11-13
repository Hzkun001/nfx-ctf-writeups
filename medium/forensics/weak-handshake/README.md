# Weak Handshake

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Forensics |
| Difficulty | Medium |
| Author | Ariaf |
| Lampiran / sumber | [assets/capture.pcapng](assets/capture.pcapng) (dari `NFCC-Com/qazwsx`, `foren/weak_handshake/capture.pcapng`) |
| Verifikasi | Lokal: dekripsi TLS mereproduksi [assets/ending.jpg](assets/ending.jpg) identik byte-per-byte (SHA256 `6af35477…2575`) |

## Ringkasan

Capture berisi tiga alur data:

1. **FTP anonim** ke port 2121 — mengunduh `clannad.webp` (umpan; "kenangan
   yang mudah terlihat di awal").
2. **Sesi TLS pertama** ke `tomoyo.local:8443` — mengunduh `/begin.jpg`.
3. **Sesi TLS kedua** ke `tomoyo.local:8443` — mengunduh `/ending.jpg`, yang
   memuat flag sebagai teks overlay.

Kedua sesi TLS memakai cipher **`TLS_RSA_WITH_AES_128_CBC_SHA` (`0x002f`)** dan
menegosiasikan ekstensi **`0x0017` (extended master secret)**. Sertifikat server
memakai **RSA 1024-bit** dengan dua prima yang **berdekatan** (`q - p = 236`),
sehingga dapat difaktorisasi dengan metode **Fermat** dalam hitungan detik.
Dari faktor tersebut diperoleh private key, lalu premaster secret didekripsi dan
key material TLS diturunkan.

Inilah "handshake yang tidak cukup kuat": kunci RSA 1024-bit dengan prima
berdekatan meruntuhkan seluruh kerahasiaan sesi.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
tshark -r assets/capture.pcapng -q -z io,phs
tshark -r assets/capture.pcapng -Y 'tls.handshake' \
  -T fields -e frame.number -e tls.handshake.type -e tls.handshake.extensions_server_name
```

Terlihat 2 sesi TLS dengan SNI `tomoyo.local`, ditambah FTP ke port 2121.
Ekspor objek FTP memberi `clannad.webp` — tidak berisi flag (umpan).

### 2. Memetakan parameter TLS

```bash
tshark -r assets/capture.pcapng -Y 'tls.handshake.type==2' \
  -T fields -e tls.handshake.ciphersuite
```

| Parameter | Nilai |
| --- | --- |
| Versi | TLS 1.2 (`0x0303`) |
| Cipher suite | `0x002f` = TLS_RSA_WITH_AES_128_CBC_SHA |
| Ekstensi ServerHello | `0xff01`, `0x0016`, **`0x0017` (extended master secret)** |
| IV | eksplisit 16 byte per record (TLS 1.1+) |

### 3. Faktorisasi sertifikat (titik lemah)

Ekstrak sertifikat dari ServerHello, lalu ambil modulus:

```bash
openssl x509 -inform DER -in cert.der -noout -modulus
```

Modulus **1024-bit**, dua prima 512-bit dengan selisih **236**. Fermat langsung
menemukannya:

```python
import math
a = math.isqrt(n)
if a * a < n: a += 1
while True:
    b2 = a * a - n
    b = math.isqrt(b2)
    if b * b == b2:
        p, q = a - b, a + b
        break
    a += 1
```

> **Catatan implementasi:** wajib memakai `math.isqrt`, bukan `int(n ** 0.5)`.
> Untuk bilangan 1024-bit, konversi float kehilangan presisi sehingga titik awal
> `a` meleset jauh dan Fermat gagal.

Lalu `d = pow(65537, -1, (p-1)*(q-1))`.

### 4. Dekripsi premaster secret dan turunkan key

`ClientKeyExchange` membawa 128 byte RSA terenkripsi. Dekripsi dengan private
key menghasilkan premaster secret (48 byte, setelah membuang padding PKCS#1 v1.5
`00 02 ... 00`).

Karena **extended master secret** dinegosiasikan, master secret memakai
**session hash** (SHA-256 atas transkrip handshake), bukan `client_random +
server_random`:

```python
master = PRF(secret, b"extended master secret", SHA256(transcript), 48)
kb     = PRF(master, b"key expansion", server_random + client_random, 104)
```

`PRF` = TLS 1.2 `P_hash` dengan **SHA-256** (bukan SHA-1/MD5 seperti TLS 1.0/1.1).
Dari 104 byte: `client_mac[20]`, `server_mac[20]`, `client_key[16]`,
`server_key[16]`, `client_iv[16]`, `server_iv[16]`.

### 5. Dekripsi record aplikasi

Tiap record `0x17` didekripsi AES-128-CBC dengan **IV eksplisit** (16 byte awal
payload), lalu MAC 20 byte di akhir dibuang.

**Detail padding yang wajib benar:** pada TLS, byte terakhir plaintext berisi
`padding_length`, dan **total padding = `padding_length + 1`** byte (byte itu
sendiri ikut dibuang). Kesalahan umum adalah membuang hanya `padding_length`
byte, sehingga menyisakan 1 byte per record:

| Record | byte terakhir | run padding | dibuang |
| --- | --- | --- | --- |
| 1 (header HTTP) | `0x00` | 1 | 1 |
| 2..20 (body) | `0x0f` | 16 | 16 |
| 21 (akhir) | `0x03` | 4 | 4 |

Bila salah, hasilnya kelebihan 20 byte dan JPEG menjadi rusak/bergeser —
gejala yang mudah disalahartikan sebagai "flag tidak ada".

### 6. Mengambil flag

Plaintext server diawali header HTTP lalu body JPEG 323692 byte. Flag tertulis
sebagai **teks overlay semi-transparan** dua baris di bagian bawah gambar,
memakai warna flat `rgb(233, 219, 219)`:

```
{D36A64128F80788B
60C677EF94FA7157}
```

Isolasi warna tersebut membuat teks terbaca jauh lebih andal daripada OCR
langsung pada gambar penuh.

## Flag

```text
NFX{D36A64128F80788B60C677EF94FA7157}
```

## Reproduksi

Butuh `tshark`, `openssl`, dan paket Python `cryptography`:

```bash
pip install cryptography

# 1. Jalankan solver (menulis ending.jpg)
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 pcap, menyusun ulang TCP per arah,
memfaktorisasi modulus dengan Fermat, menurunkan key via PRF SHA-256 + extended
master secret, mendekripsi record dengan padding `pad+1`, lalu mengekstrak JPEG.
[test_solve.py](test_solve.py) menguji keutuhan pcap, keberadaan dua sesi,
sifat lemah sertifikat (`q - p = 236`), cipher suite & ekstensi EMS, determinisme
PRF, **reproduksi gambar identik byte-per-byte**, dan penolakan input berubah.

## Bukti

- Berkas tantangan: [assets/capture.pcapng](assets/capture.pcapng)
  (SHA256: `de2f31ef3b6a57f63f65a31edfb20e455afd6030fa8b9040003268126be76562`).
- Hasil dekripsi: [assets/ending.jpg](assets/ending.jpg) 323692 byte
  (SHA256: `6af3547729d20261bd77d7b9196afab088f7ee0d5e3e272871e94281d36d2575`),
  direproduksi identik oleh solver.
- Modulus RSA 1024-bit, `q - p = 236`; cipher `0x002f`; ekstensi `0x0017`.
- Teks overlay pada gambar: `{D36A64128F80788B` / `60C677EF94FA7157}`.

## Penggunaan AI

Penyusunan solver (faktorisasi Fermat, derivasi key TLS 1.2 dengan extended
master secret, penanganan padding `pad+1`) dan penyuntingan naskah writeup
dibantu oleh model AI; seluruh langkah analisis dan verifikasi dijalankan ulang
secara lokal.
