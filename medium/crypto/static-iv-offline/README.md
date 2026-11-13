# Static IV Offline

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Crypto |
| Difficulty | Medium |
| Author | rio |
| Lampiran / sumber | [assets/challenge.py](assets/challenge.py), [assets/output.txt](assets/output.txt) |
| Verifikasi | Lokal; derivasi kunci AES-256-CBC dari MASTER & counter, unpadding PKCS#7, flag terdekripsi sempurna |

## Ringkasan

Tantangan mengimplementasikan enkripsi simetris menggunakan algoritma **AES-256-CBC** secara luring (*offline*). Ciphertext dibentuk dari plaintext `PREFIX + b"|" + flag` yang diberi padding standar PKCS#7. Inisialisasi cipher menggunakan Initialization Vector (IV) statis 16-byte, serta kunci AES 256-bit yang diturunkan melalui fungsi hash SHA-256 terhadap konkatenasi nilai master dan pencacah (*counter*):

$$\text{key} = \text{SHA256}(\text{MASTER} \parallel \text{counter.to\_bytes}(4, \text{'little'}))[:32]$$

Kelemahan fatal terletak pada keterbukaan seluruh parameter pembentuk kunci: konstanta `MASTER` ditinggalkan di dalam skrip `challenge.py`, sementara nilai `counter`, `iv_hex`, dan `ct_hex` disertakan di dalam berkas `output.txt`. Dengan seluruh parameter yang terbuka secara penuh, kunci enkripsi dapat dihitung secara langsung dan ciphertext didekripsi secara deterministik.

## Alur penyelesaian

### 1. Pemeriksaan awal & inventarisasi berkas

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `assets/challenge.py` | 901 B | `9db56543f1a9e477b346b4f17c648d3617f959ecae2d04a15b3e95e7d870ae00` |
| `assets/output.txt` | 328 B | `9b02a67da90ec0ae31f8f7a183a95f9561bc5131c453429a6dc1f002a66eb970` |

Potongan kode enkripsi pada `challenge.py`:

```python
MASTER = b"\x13\x37" * 16           # 32 byte master key bocor
PREFIX = b"user-input-goes-here:"

def get_key(counter):
    return hashlib.sha256(MASTER + counter.to_bytes(4, "little")).digest()[:32]

def encrypt_flag(flag: bytes, iv: bytes, counter: int) -> bytes:
    key = get_key(counter)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(PREFIX + b"|" + flag, 16))
```

Pada `output.txt` tercatat:
- `counter`: 11
- `iv_hex`: `"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"` (16 byte `0xAA`)
- `ct_hex`: ciphertext sepanjang 160 karakter heksadesimal (80 byte / 5 blok AES)

### 2. Rekonstruksi kunci dan dekripsi

Karena `MASTER` dan `counter` diketahui:
1. Konversikan `counter = 11` menjadi 4-byte *little-endian* integer: `b"\x0b\x00\x00\x00"`.
2. Bentuk input hash: `b"\x13\x37" * 16 + b"\x0b\x00\x00\x00"`.
3. Hitung SHA-256 digest dan ambil 32 byte pertama sebagai kunci AES.
4. Dekode `iv_hex` menjadi 16 byte IV.
5. Inisialisasi cipher `AES.new(key, AES.MODE_CBC, iv)`.
6. Dekripsi ciphertext 80 byte dan lepaskan PKCS#7 padding.

### 3. Ekstraksi flag

Hasil dekripsi menghasilkan plaintext byte:
```text
b"user-input-goes-here:|NXCTF{cbc_1v_r3u53_l34k5_k3y5tr34m_b0fbd4d35f80}"
```

Memisahkan prefix `user-input-goes-here:|` mengungkap string flag secara utuh.

## Flag

```text
NXCTF{cbc_1v_r3u53_l34k5_k3y5tr34m_b0fbd4d35f80}
```

## Reproduksi

Dependensi tercantum pada [requirements.txt](requirements.txt) (`pycryptodome`).

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan pengujian unit otomatis
python3 -m unittest -v
```

Keluaran solver:
```text
[+] Recovered Flag: NXCTF{cbc_1v_r3u53_l34k5_k3y5tr34m_b0fbd4d35f80}
```

## Bukti

- Berkas implementasi tantangan: [assets/challenge.py](assets/challenge.py).
- Berkas keluaran ciphertext & parameter: [assets/output.txt](assets/output.txt).
- Skrip pemulihan flag: [solve.py](solve.py).
- Pengujian unit otomatis: [test_solve.py](test_solve.py).

## Penggunaan AI

Struktur solver dan verifikasi parsing blok CBC disusun dengan bantuan AI untuk memastikan pemulihan deterministik dan pengujian unit otomatis berjalan bersih.
