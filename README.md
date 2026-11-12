# NFX CTF 2026 Writeups

Dokumentasi penyelesaian challenge NFX CTF oleh [Hzkun001](https://github.com/Hzkun001).
Repositori ini mencakup difficulty **Medium, Hard, dan Insane**.

> **Status: draf persiapan pengumpulan.** Identitas peserta, screenshot
> scoreboard akhir, serta daftar writeup masih perlu dilengkapi.

## Identitas peserta

| Data | Keterangan |
| --- | --- |
| Nama terdaftar di ctf.nfx.my.id | Belum diisi |
| Username terdaftar di ctf.nfx.my.id | Belum dikonfirmasi |
| Track | Belum dikonfirmasi: Umum / Mahasiswa NF |
| GitHub | [Hzkun001](https://github.com/Hzkun001) |

## Scoreboard akhir

Screenshot posisi akhir harus berasal dari scoreboard **track peserta**.
Simpan bukti di [`assets/scoreboard/`](assets/scoreboard/README.md), lalu tampilkan
gambar di bagian ini setelah berkasnya tersedia.

**Status:** screenshot akhir belum tersedia; posisi dan skor belum dicantumkan.

## Daftar writeup

| Difficulty | Indeks | Status |
| --- | --- | --- |
| Medium | [Lihat daftar](medium/README.md) | 9 writeup: NexaPartner, NexaIdentity, Dokodemo Door, The Alchemist's Sandbox, Stay, Art Evidence Secret, Black Box Protocol N4T0, ECDSA Nonce Bias, Pipa Nu Kotor |
| Hard | [Lihat daftar](hard/README.md) | 2 writeup: My Lovely Freya, Broken Signature Scheme |
| Insane | [Lihat daftar](insane/README.md) | Menunggu konfirmasi daftar challenge |

Setiap writeup memuat nama challenge, deskripsi singkat, alur penyelesaian,
dan string flag utuh. Bukti verifikasi lokal dibedakan dari bukti bahwa flag
diterima platform. Prefiks dan kapitalisasi flag dipertahankan sesuai hasil.

## Struktur repositori

```text
.
├── README.md
├── medium/
│   ├── README.md
│   ├── web-exploitation/
│   ├── binary-exploit-pwn/
│   ├── reverse-engineering/
│   ├── boot-to-root/
│   ├── miscellaneous-logic/
│   ├── forensics/
│   └── crypto/
├── hard/
│   └── README.md
├── insane/
│   └── README.md
├── assets/
│   └── scoreboard/
│       └── README.md
└── templates/
    └── WRITEUP.md
```

Folder kategori yang sama tersedia di dalam `medium/`, `hard/`, dan
`insane/`. Setiap challenge ditempatkan di bawah difficulty dan kategorinya:

```text
medium/web-exploitation/nama-challenge/
├── README.md          # Ringkasan dan langkah penyelesaian
├── solve.py           # Jika solver diperlukan
└── assets/            # Screenshot atau bukti yang dirujuk dalam writeup
```

| Kategori | Nama folder |
| --- | --- |
| Web Exploitation | `web-exploitation/` |
| Binary Exploit (Pwn) | `binary-exploit-pwn/` |
| Reverse Engineering | `reverse-engineering/` |
| Boot to Root | `boot-to-root/` |
| Miscellaneous & Logic | `miscellaneous-logic/` |

Daftar kategori masih menunggu pelengkapan menjadi delapan kategori sesuai
label resmi platform. Nama yang belum dikonfirmasi belum dibuatkan folder.

## Menambah writeup

1. Pastikan challenge termasuk Medium, Hard, atau Insane sesuai platform.
2. Pilih subfolder kategori yang sesuai, lalu buat folder challenge dengan
   huruf kecil dan tanda hubung.
3. Salin [`templates/WRITEUP.md`](templates/WRITEUP.md) menjadi `README.md`
   di folder challenge, lalu isi dan hapus semua penanda yang belum lengkap.
4. Tulis langkah yang menghasilkan flag. Cantumkan perintah, output penting,
   dan kebutuhan solver agar hasil dapat diulang.
5. Tambahkan tautan ke indeks kategori terkait. Sertakan bukti penerimaan
   flag bila tersedia, tanpa membuat klaim accepted berdasarkan uji lokal saja.

## Penggunaan AI

Penyusunan struktur dokumentasi dibantu **OpenAI Codex**. Jika AI digunakan
untuk memahami soal, mengembangkan solver, atau debugging suatu challenge,
bantuannya dapat dijelaskan singkat pada writeup terkait.

## Pengumpulan

Berdasarkan pedoman yang diberikan panitia:

- Writeup wajib untuk **Track Umum**, opsional untuk **Mahasiswa NF**.
- Batas pengumpulan: **13 November 2026, pukul 23:59 WIB**.
- Pastikan tautan repositori dan seluruh gambar dapat dibaca panitia.

Sebelum mengumpulkan:

- [ ] Nama, username CTF, dan track sudah benar.
- [ ] Screenshot scoreboard akhir track peserta sudah ditampilkan.
- [ ] Semua writeup Medium, Hard, dan Insane yang akan dilaporkan sudah terdaftar.
- [ ] Setiap writeup memuat langkah penyelesaian dan flag utuh.
- [ ] Semua tautan relatif dan gambar dapat dibuka.
- [ ] Status draf dan penanda yang belum diisi sudah diperbarui.
- [ ] Tautan pengumpulan dapat diakses tanpa login oleh panitia.
