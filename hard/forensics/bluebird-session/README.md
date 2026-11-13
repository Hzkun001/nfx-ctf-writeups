# Bluebird Session

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Forensics |
| Difficulty | Hard |
| Input yang dianalisis | [assets/login.keyring](assets/login.keyring), dump kredensial GNOME Keyring dari arsip `Evidence.zip` |
| Verifikasi | Lokal: shadow hash SHA-512 `mizore` dipecahkan, dekripsi GNOME Keyring AES-128-CBC terautentikasi checksum MD5, kata sandi membuka `for_nozomi.zip` |

## Ringkasan

Tantangan **Bluebird Session** menyajikan investigasi forensik artefak Linux
Ubuntu 24.04 berbasis dump sistem operasi. Skenario berpusat pada dua pengguna,
`mizore` dan `nozomi` (karakter dari *Liz and the Blue Bird*).

Penyelesaian memerlukan pembongkaran rantai kriptografi multi-lapis:
1. Menemukan hash kata sandi user `mizore` di `/etc/shadow` dan memecahkannya
   menggunakan kamus bertema menjadi `Bluebirds1927!`.
2. Menganalisis berkas basis data rahasia `login.keyring` (GNOME Keyring format v0)
   milik `mizore`. Perkakas publik (`keyring2john`) gagal mengekstrak hash karena
   salah membaca offset ciphertext. Berkas didekripsi menggunakan implementasi
   spesifikasi biner resmi (`symkey_generate_simple` SHA-256 iteratif 3.421 rounds +
   AES-128-CBC) dan diautentikasi dengan checksum MD5.
3. Plaintext rahasia berjudul *"Mizore Promise Note"* membocorkan kata sandi arsip:
   `MizoreCanFly2077!@`.
4. Berkas `for_nozomi.zip` dibuka untuk mengambil artefak memori dan flag.

Selain jalur forensik terencana, terdapat celah kebocoran operasional (*unintended*)
pada file `.bash_history` milik `nozomi` yang mencatat perintah `7z` beserta argumen
password mentah.

## Alur penyelesaian

### 1. Pemeriksaan awal & audit sistem

Arsip bukti disediakan dalam `Evidence.zip` (password `nxctf.id`). Berkas berisi
dump sistem berkas Ubuntu 24.04.

Pemeriksaan `/etc/passwd` menunjukkan tiga user interaktif:
- `aria` (uid 1000)
- `mizore` (uid 1001)
- `nozomi` (uid 1002)

Pemeriksaan log paket `/var/log/apt/history.log` mengungkap perkakas yang sengaja
dipasang oleh pembuat soal:
```text
apt install -y gnome-keyring libsecret-tools seahorse p7zip-full openssl
```
Pemasangan `libsecret-tools` dan `gnome-keyring` menjadi petunjuk langsung bahwa
data sensitif disimpan di dalam GNOME Keyring.

### 2. Cracking hash shadow user mizore

Entri pada `/etc/shadow`:
```text
mizore:$6$bluebird$DapjL6a0nzC4W7lGKYhAtHOEPMW06uuQOg4DiPxOWF3RKE6RRSKIumUGXj3QmER5G4ceko4QUsikFswkW330E1:20684:0:99999:7:::
```

Format `$6$` menandakan algoritma **SHA-512 Crypt** dengan salt `bluebird`.
Serangan kamus berbasis kata kunci bertema anime *Liz and the Blue Bird* memecahkan
hash ini:

```bash
john --format=sha512crypt mizore.hash --wordlist=theme.txt
```

Hasil cracking:
```text
mizore:Bluebirds1927!
```

Divalidasi dengan OpenSSL:
```bash
openssl passwd -6 -salt bluebird "Bluebirds1927!"
# $6$bluebird$DapjL6a0nzC4W7lGKYhAtHOEPMW06uuQOg4DiPxOWF3RKE6RRSKIumUGXj3QmER5G4ceko4QUsikFswkW330E1
```

### 3. Rekonstruksi & dekripsi GNOME Keyring (`login.keyring`)

Berkas target berada di `home/mizore/.local/share/keyrings/login.keyring` (566 byte,
SHA256 `9aa5f380bb318e691f624beb2d20266cee09eb9b173af600e650a8dd623e1ee8`).

#### Struktur biner format v0
1. **Magic Header (16 byte):** `GnomeKeyring\n\r\x00\n`.
2. **Metadata:** `iters = 3421`, `salt = 871fa30523eb6c6b` (8 byte).
3. **Item publik:** Item ID 1 bertipe generic, atribut `app = bluebird`, `target = for_nozomi_note`.
4. **Ciphertext:** Berada pada offset 198 dengan ukuran 368 byte.

#### Derivasi kunci & integritas
Sesuai implementasi GNOME Keyring (`egg_symkey_generate_simple`):
- Hash awal $H_0 = \text{SHA256}(\text{password} \parallel \text{salt})$.
- Diulang sebanyak 3.420 kali: $H_i = \text{SHA256}(H_{i-1})$.
- Kunci AES-128: $H[0:16]$, IV: $H[16:32]$.
- Plaintext didekripsi dengan AES-128-CBC. 16 byte pertama adalah checksum MD5 dari sisa payload:
  $$\text{MD5}(\text{payload}[16:]) == \text{plaintext}[:16]$$

Dengan kata sandi `Bluebirds1927!`, checksum MD5 cocok dan payload terbaca:
```text
Label  : Mizore Promise Note
Secret :
For Nozomi,

I promised I would keep playing, even if the sound could no longer reach you.
Every note we left behind still belongs to the same sky.

The archive is for you.
for_nozomi.zip password: MizoreCanFly2077!@
```

### 4. Ekstraksi arsip `for_nozomi.zip` & validasi media

Berkas `for_nozomi.zip` di `home/nozomi/Documents/` diekstrak menggunakan kata sandi
`MizoreCanFly2077!@`:
- `README.txt`: Berisi pesan pengantar memori.
- 5 berkas `.jpg`: Menggunakan nama Discord Snowflake ID (2017–2020) yang memuat ilustrasi Nozomi & Mizore.
- Berkas `Ensemble.mp4`: Pemeriksaan spektrogram audio pada detik-detik akhir menunjukkan frekuensi peluruhan instrumen oboe alami (~1.192 Hz) tanpa modulasi data tersembunyi (LSB/DTMF).

### 5. Jalur pintas (unintended history leak)

Pemeriksaan riwayat terminal di `home/nozomi/.bash_history` menunjukkan kebocoran perintah
langsung:
```bash
7z a -tzip ../for_nozomi.zip . -p'MizoreCanFly2077!@'
```
Perintah ini membocorkan kata sandi tanpa perlu memecahkan hash dan mendekripsi keyring.

## Flag

Format flag resmi event NFX CTF:

```text
NFX{MizoreCanFly2077!@}
```

> **Catatan:** Pada platform kompetisi dengan prefix varian `NXCTF` atau `nxctf`,
> nilai flag yang setara adalah `NXCTF{MizoreCanFly2077!@}` atau `nxctf{MizoreCanFly2077!@}`.
> Kredensial akun Mizore yang dipulihkan adalah `Bluebirds1927!`.

## Reproduksi

Dependensi: Python 3.10+ dan **PyCryptodome** (`pip install pycryptodome`).

Jalankan solver otomatis:

```bash
python3 solve.py
```

Jalankan pengujian unit:

```bash
python3 -m unittest -v
```

[Solver](solve.py) memverifikasi SHA-256 berkas input, melakukan derivasi kunci
iteratif SHA-256 (3.421 rounds), mendekripsi AES-128-CBC, memvalidasi integritas MD5,
dan mengekstrak flag secara deterministik.

## Bukti

- [assets/login.keyring](assets/login.keyring): Berkas basis data GNOME Keyring target (SHA-256: `9aa5f380bb31...`).
- [assets/mizore.shadow.txt](assets/mizore.shadow.txt): Entri shadow hash `$6$bluebird$...` user `mizore`.
- [assets/README.txt](assets/README.txt): Catatan yang diekstrak dari `for_nozomi.zip`.
- [solve.py](solve.py): Implementasi mandiri dekripsi biner GNOME Keyring.
- [test_solve.py](test_solve.py): Pengujian unit integritas dan penolakan password salah.

## Penggunaan AI

Analisis spesifikasi biner format GNOME Keyring v0 (`dump-keyring0-format.c`) dan
rekonstruksi fungsi `egg_symkey_generate_simple` dibantu oleh AI untuk mengoreksi
bug offset pembacaan ciphertext pada perkakas open-source lama.
