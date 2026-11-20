<div align="center">

# NFX CTF 2026 — Writeups

**Dokumentasi penyelesaian challenge NFX CTF 2026 oleh [Hzkun001](https://github.com/Hzkun001)** (`hz-was-here`)

![Writeups](https://img.shields.io/badge/writeups-33-blue?style=flat-square)
![Medium](https://img.shields.io/badge/medium-23-green?style=flat-square)
![Hard](https://img.shields.io/badge/hard-9-orange?style=flat-square)
![Insane](https://img.shields.io/badge/insane-1-red?style=flat-square)
![Track](https://img.shields.io/badge/track-umum-lightgrey?style=flat-square)

[Scoreboard](#scoreboard) ·
[Daftar Writeup](#daftar-writeup) ·
[Metodologi](#metodologi) ·
[Struktur Repositori](#struktur-repositori)

</div>
---

## Daftar Writeup

### Ringkasan per Kategori

| Kategori | Medium | Hard | Insane | Total |
| --- | :---: | :---: | :---: | :---: |
| Web Exploitation | 2 | – | – | 2 |
| Binary Exploitation (Pwn) | 2 | 1 | 1 | 4 |
| Reverse Engineering | 2 | 3 | – | 5 |
| Cryptography | 7 | 2 | – | 9 |
| Forensics | 2 | 1 | – | 3 |
| Miscellaneous & Logic | 5 | 1 | – | 6 |
| Boot to Root | 1 | – | – | 1 |
| OSINT | 2 | 1 | – | 3 |
| **Total** | **23** | **9** | **1** | **33** |

### Medium — 23 solve

Indeks lengkap: [medium/README.md](medium/README.md)

| Kategori | Challenge | Teknik |
| --- | --- | --- |
| Web | [NexaPartner](medium/web-exploitation/nexapartner/README.md) | Prototype pollution `__proto__` lewat `POST /api/settings` untuk membuka konsol audit admin |
| Web | [NexaIdentity](medium/web-exploitation/nexaidentity/README.md) | NoSQL operator injection (`$ne`) pada `POST /login` untuk masuk sebagai admin |
| Pwn | [Pipa Nu Kotor](medium/binary-exploit-pwn/pipa-nu-kotor/README.md) | Field `flags` tak terinisialisasi diwarisi lewat reuse tcache sehingga halaman proteksi bisa ditulis |
| Pwn | [NFXCTF Convention](medium/binary-exploit-pwn/nfxctf-convention/README.md) | Overwrite rank via `strcpy`, leak format string, lalu stack overflow ke `system("/bin/sh")` |
| Reverse | [Medium RC4](medium/reverse-engineering/medium-rc4/README.md) | Kunci dan ciphertext RC4 dibaca dari `.rodata`, lalu didekripsi (RC4 simetris) |
| Reverse | [Medium TEA](medium/reverse-engineering/medium-tea/README.md) | Kunci TEA yang diobfuskasi sebagai `sub`/`add`, lalu dekripsi 32 ronde terbalik |
| Crypto | [Black Box Protocol N4T0](medium/crypto/blackbox-protocol-n4t0/README.md) | Workbook tiga lapis: ejaan NATO, hex ASCII, dan reinterpretasi bit float32 |
| Crypto | [ECDSA Nonce Bias](medium/crypto/ecdsa-nonce-bias/README.md) | Nonce bias 8 bit → Hidden Number Problem; lattice LLL memulihkan private key |
| Crypto | [Unbreakable Delay](medium/crypto/unbreakable-delay/README.md) | Faktorisasi n dari bocoran `p ⊕ q`, lalu bukti VDF Wesolowski dihitung lewat φ(n) |
| Crypto | [Feistel Differential](medium/crypto/feistel-differential/README.md) | Differential cryptanalysis Feistel 7 ronde; subkunci dipulihkan ronde demi ronde |
| Crypto | [Cihuy LWE](medium/crypto/cihuy-lwe/README.md) | LWE dengan rahasia ternary dipecahkan lewat Kannan embedding + LLL/BKZ |
| Crypto | [Static IV Offline](medium/crypto/static-iv-offline/README.md) | `MASTER` dan counter bocor sehingga kunci AES-CBC bisa diturunkan langsung |
| Crypto | [RSA Coppersmith Cihuy](medium/crypto/rsa-coppersmith-cihuy/README.md) | 300 bit atas `p` diketahui; Coppersmith (Howgrave-Graham) memulihkan 212 bit sisanya |
| Forensics | [Art Evidence Secret](medium/forensics/art-evidence-secret/README.md) | Password dari metadata PNG, dua payload AES-GCM di LSB kanal merah dan biru |
| Forensics | [Weak Handshake](medium/forensics/weak-handshake/README.md) | Prima RSA berdekatan difaktorkan dengan Fermat, lalu sesi TLS 1.2 (EMS) didekripsi |
| Misc | [Dokodemo Door](medium/miscellaneous-logic/dokodemo-door/README.md) | PDF ter-XOR kunci berulang; kunci 16 byte dari known plaintext dan statistik kolom |
| Misc | [The Alchemist's Sandbox](medium/miscellaneous-logic/the-alchemists-sandbox/README.md) | PyJail tanpa digit/kutip lewat `getattr` + `chr`, lalu balik transformasi 32 putaran |
| Misc | [Stay](medium/miscellaneous-logic/stay/README.md) | Karakter Unicode zero-width sebagai alfabet 2 bit → Base64 → repeating-key XOR |
| Misc | [Wujud Aseli Atmin](medium/miscellaneous-logic/wujud-aseli-atmin/README.md) | ZIP tersembunyi setelah `IEND`, perbaiki signature PNG, lalu LSB kanal merah |
| Misc | [SymHell](medium/miscellaneous-logic/symhell/README.md) | Bash jail tanpa huruf/angka: glob `[_-{]`, aritmetika `$(())`, dan substring untuk membentuk `cat` |
| Boot to Root | [Forgotten Commit](medium/boot-to-root/forgotten-commit/README.md) | Kredensial dari commit lama + dangling blob via `git fsck` → kunci XOR stream |
| OSINT | [The Ghost Operator](medium/osint/the-ghost-operator/README.md) | UID kunci GPG commit → rentry yang dihapus → Wayback Machine → geolokasi safehouse |
| OSINT | [Fresh Arrival](medium/osint/fresh-arrival/README.md) | Registrasi PK-ADL → MSN 26854 → fotografer JetPhotos dan operator pertama airframe |

### Hard — 9 solve

Indeks lengkap: [hard/README.md](hard/README.md)

| Kategori | Challenge | Teknik |
| --- | --- | --- |
| Pwn | [TheForgottenState](hard/binary-exploit-pwn/theforgottenstate/README.md) | Use-after-free pada `table[i]` → fake header untuk arbitrary R/W → `free@got` jadi `system` |
| Reverse | [Castaway](hard/reverse-engineering/castaway/README.md) | State berantai bergantung pada ciphertext sehingga tiap byte bisa dibalik; opaque predicate selalu false |
| Reverse | [Hard VM Bytecode](hard/reverse-engineering/vm-bytecode/README.md) | Resolve jump table VM, lalu balik blok LOAD/XOR/ADD/ROL/CMP per karakter |
| Reverse | [Hard Feistel](hard/reverse-engineering/feistel/README.md) | Feistel 16 ronde dibalik dengan round key dari `.rodata` dan ciphertext di `.data` |
| Crypto | [Broken Signature Scheme](hard/crypto/broken-signature-scheme/README.md) | Tanda tangan RSA multiplicative dipalsukan, n difaktorkan Fermat, kunci AES-GCM dari `p‖q` |
| Crypto | [FlagKeepers](hard/crypto/flagkeepers/README.md) | Nonce reuse AES-GCM → H dipulihkan lewat GCD polinomial → tag palsu untuk `admin = True` |
| Forensics | [Bluebird Session](hard/forensics/bluebird-session/README.md) | Crack hash shadow, dekripsi GNOME Keyring v0, lalu password arsip dipakai sebagai flag |
| Misc | [My Lovely Freya](hard/miscellaneous-logic/my-lovely-freya/README.md) | Tinggi PNG dipulihkan dari panjang scanline; password di gambar membuka surat AES-256-CBC |
| OSINT | [Tragedi 9/11](hard/osint/tragedi-9-11/README.md) | Pengunggah video di Reddit → akun GitHub → flag di riwayat commit `.env` |

### Insane — 1 solve

Indeks lengkap: [insane/README.md](insane/README.md)

| Kategori | Challenge | Teknik |
| --- | --- | --- |
| Pwn | [NarrowGate](insane/binary-exploit-pwn/narrowgate/README.md) | Leak format string, integer truncation pada validasi ukuran, lalu ROP open/read/write karena seccomp |

---

## Metodologi

1. **Reproducible.** Challenge non-web dilengkapi solver Python 3 beserta unit test yang bisa dijalankan ulang. Dua challenge web direproduksi dengan `curl` karena instansinya sudah tidak aktif; artefak respons HTTP-nya disimpan sebagai bukti.
2. **Bukti visual asli.** Screenshot antarmuka, konsol server, rekaman paket jaringan, dan diagram penjelas disertakan agar setiap argumen teknis punya dasar yang nyata.
3. **Hipotesis dipisah dari fakta.** Setiap writeup membedakan pengujian di lingkungan lokal dari respons aktual instance server CTF.

### Tools

| Area | Tools |
| --- | --- |
| Pwn / Reversing | GDB, Pwntools, Ghidra, IDA Free, ROPgadget, Checksec |
| Web | Burp Suite, cURL, Chromium DevTools, Python Requests |
| Crypto | SageMath, PyCryptodome / Python Cryptography, Z3 |
| Forensics / OSINT | Wireshark, Tshark, Binwalk, Exiftool, open registries, Wayback Machine |

---

## Struktur Repositori

```text
nfx-ctf-writeups/
├── README.md              # Indeks utama dan rekap scoreboard
├── assets/
│   └── scoreboard/        # Bukti tangkapan layar scoreboard akhir
├── templates/
│   └── WRITEUP.md         # Template writeup
├── medium/                # 23 challenge
│   ├── web-exploitation/
│   ├── binary-exploit-pwn/
│   ├── reverse-engineering/
│   ├── crypto/
│   ├── forensics/
│   ├── miscellaneous-logic/
│   ├── boot-to-root/
│   └── osint/
├── hard/                  # 9 challenge
│   ├── binary-exploit-pwn/
│   ├── reverse-engineering/
│   ├── crypto/
│   ├── forensics/
│   ├── miscellaneous-logic/
│   └── osint/
└── insane/                # 1 challenge
    └── binary-exploit-pwn/
```

Setiap folder challenge berdiri sendiri:

| Berkas | Isi |
| --- | --- |
| `README.md` | Analisis masalah, rincian kelemahan, alur eksploitasi bertahap, dan flag |
| `solve.py` / `test_solve.py` | Skrip solver otomatis dan pembuktiannya |
| `assets/` | Bukti visual (screenshot, diagram, arsip terdekripsi, atau file input) |
