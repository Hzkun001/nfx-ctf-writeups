# Forgotten Commit (Shadow Ops Portal)

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Boot to Root |
| Difficulty | Medium |
| Author | Kaelen Vance |
| Lampiran / sumber | [assets/shadow_repo.tar.gz](assets/shadow_repo.tar.gz) |
| Verifikasi | Lokal: rekonstruksi riwayat commit Git, audit objek tak terindeks via `git fsck`, derivasi kunci SHA256, dan dekripsi flag XOR stream teruji 100% |

## Ringkasan

Tantangan memberikan arsip repositori Git bernama `shadow_repo.tar.gz` yang
merepresentasikan utilitas deployment internal *Shadow Ops Portal*. Saat
diekstraksi, direktori kerja tampak bersih karena commit terakhir pada branch
`main` menghapus kunci rahasia sebelum rilis publik.

Melalui audit riwayat Git dan pemeriksaan objek database biner Git (`.git/objects`)
menggunakan `git fsck`, ditemukan dua artefak penting:
1. Commit historis `706f270` (*Initial staging configuration*) yang membocorkan
   `AWS_ACCESS_KEY_ID` pada `.env.staging` serta email author.
2. Sebuah objek terlepas (*dangling blob*) `21d5a194fb6a627b1702cbf74b51589789988b72`
   yang menyimpan catatan pemulihan operator beserta ciphertext flag.

Dengan menggabungkan ketiga parameter identitas sesuai format kunci yang ditentukan,
kunci enkripsi diturunkan via SHA256 untuk mendekripsi *keystream* XOR dan
memperoleh flag root.

## Alur penyelesaian

### 1. Pemeriksaan awal repositori

Ekstraksi arsip `shadow_repo.tar.gz` menghasilkan folder repositori Git:

```bash
tar -xzf shadow_repo.tar.gz
cd shadow_repo
git status
```

Pemeriksaan riwayat commit via `git log`:

```text
commit a9e13b26146a71c87d43831b6493c2b3ae5aa908 (HEAD -> main)
Author: Kaelen Vance <k.vance@ops-shadow-nfx.internal>
Date:   Fri Oct 4 08:00:00 2024 +0700

    Remove sensitive staging key before public release

commit 706f2702eb1a619012bb71c58e2b3db82049d1b9
Author: Kaelen Vance <k.vance@ops-shadow-nfx.internal>
Date:   Fri Oct 4 07:00:00 2024 +0700

    Initial staging configuration
```

Terdapat dua commit dalam riwayat. Commit terakhir menyatakan telah menghapus
kunci sensitif staging.

### 2. Menemukan kredensial yang dihapus pada commit sebelumnya

Periksa perbedaan antarkommit atau inspeksi langsung isi berkas `.env.staging`
pada commit `706f270`:

```bash
git show 706f2702eb1a619012bb71c58e2b3db82049d1b9:.env.staging
```

Keluaran:
```text
# DO NOT COMMIT TO PRODUCTION
AWS_ACCESS_KEY_ID=AKIA-NFX-99204811
STAGE_HOST=vault.ops-shadow-nfx.internal
```

Dari commit awal ini diperoleh dua parameter:
- **Author Email:** `k.vance@ops-shadow-nfx.internal`
- **Leaked AWS Key ID:** `AKIA-NFX-99204811`

### 3. Menemukan dangling blob via `git fsck`

Meskipun riwayat commit hanya memiliki dua titik, objek database Git mungkin
menyimpan objek terlepas (*unreferenced / dangling objects*) dari operasi commit,
rebase, atau reset sebelumnya:

```bash
git fsck --lost-found
```

Keluaran:
```text
Checking object directories: 100% (256/256), done.
dangling blob 21d5a194fb6a627b1702cbf74b51589789988b72
```

Tampilkan isi dari dangling blob tersebut menggunakan `git cat-file`:

```bash
git cat-file -p 21d5a194fb6a627b1702cbf74b51589789988b72
```

Keluaran:
```text
OPERATOR RECOVERY NOTE
PGP_FINGERPRINT=4F9E-881C-B204-77A1
ENCRYPTED_FLAG_HEX=2b462d2964457eea57886bb55efb59f72f35c6d87db4b134e0d74cb3b29a83e858800871b4e7bbeb
KEY_FORMAT=<author_email>|<leaked_aws_key_id>|<pgp_fingerprint>
```

Objek ini menyediakan parameter ketiga:
- **PGP Fingerprint:** `4F9E-881C-B204-77A1`
- **Encrypted Flag (Hex):** `2b462d...beb`

### 4. Derivasi kunci dan dekripsi stream XOR

Sesuai instruksi `KEY_FORMAT`:

```text
key_string = "k.vance@ops-shadow-nfx.internal|AKIA-NFX-99204811|4F9E-881C-B204-77A1"
```

Algoritma dekripsi:
1. Hitung `key = SHA256(key_string.encode('utf-8'))`.
2. Bentuk *keystream* semu dengan menggabungkan blok hash counter berurutan:
   $$\text{stream} = \text{SHA256}(\text{key} \parallel \text{counter}_{32\text{-bit big-endian}})$$
3. Lakukan operasi XOR antara `ciphertext` dan `stream`:
   $$\text{plaintext}[i] = \text{ciphertext}[i] \oplus \text{stream}[i]$$

Eksekusi algoritma ini langsung memulihkan flag.

## Flag

```text
NFXCTF{g1t_d4ngl1ng_bl0b_h4v0c_5c8a19d4}
```

## Reproduksi

Jalankan solver Python standar:

```bash
cd medium/boot-to-root/forgotten-commit
python3 solve.py
```

Keluaran:
```text
[*] Author Email: k.vance@ops-shadow-nfx.internal
[*] Leaked AWS Key: AKIA-NFX-99204811
[*] PGP Fingerprint: 4F9E-881C-B204-77A1
[*] KDF Key String: k.vance@ops-shadow-nfx.internal|AKIA-NFX-99204811|4F9E-881C-B204-77A1
[+] Recovered Flag: NFXCTF{g1t_d4ngl1ng_bl0b_h4v0c_5c8a19d4}
```

Jalankan pengujian unit:
```bash
python3 test_solve.py
```

## Penggunaan AI

Analisis dangling blob pada struktur internal Git dan verifikasi keystream
counter dibantu oleh AI untuk mengotomatisasi ekstraksi metadata commit.
