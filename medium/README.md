# Medium Challenges — NFX CTF 2026

[← Kembali ke Indeks Utama](../README.md)

Daftar 23 challenge tingkat kesulitan **Medium** yang berhasil diselesaikan pada NFX CTF 2026.

---

## Ringkasan Solves (23 Challenge)

| Kategori | Challenge | Deskripsi Singkat |
| --- | --- | --- |
| **Web Exploitation** | [NexaPartner](web-exploitation/nexapartner/README.md) | Prototype pollution `__proto__` lewat `POST /api/settings` untuk membuka konsol audit admin. |
| | [NexaIdentity](web-exploitation/nexaidentity/README.md) | NoSQL operator injection (`$ne`) pada `POST /login` untuk masuk sebagai admin. |
| **Cryptography** | [Black Box Protocol N4T0](crypto/blackbox-protocol-n4t0/README.md) | Workbook tiga lapis: ejaan NATO, hex ASCII, dan reinterpretasi bit float32. |
| | [ECDSA Nonce Bias](crypto/ecdsa-nonce-bias/README.md) | Nonce bias 8 bit → Hidden Number Problem; lattice LLL memulihkan private key. |
| | [Unbreakable Delay](crypto/unbreakable-delay/README.md) | Faktorisasi n dari bocoran `p ⊕ q`, lalu bukti VDF Wesolowski dihitung lewat φ(n). |
| | [Feistel Differential](crypto/feistel-differential/README.md) | Differential cryptanalysis Feistel 7 ronde; subkunci dipulihkan ronde demi ronde. |
| | [Cihuy LWE](crypto/cihuy-lwe/README.md) | LWE dengan rahasia ternary dipecahkan lewat Kannan embedding + LLL/BKZ. |
| | [Static IV Offline](crypto/static-iv-offline/README.md) | `MASTER` dan counter bocor sehingga kunci AES-CBC bisa diturunkan langsung. |
| | [RSA Coppersmith Cihuy](crypto/rsa-coppersmith-cihuy/README.md) | 300 bit atas `p` diketahui; Coppersmith (Howgrave-Graham) memulihkan 212 bit sisanya. |
| **Miscellaneous & Logic** | [Dokodemo Door](miscellaneous-logic/dokodemo-door/README.md) | PDF ter-XOR kunci berulang; kunci 16 byte dari known plaintext dan statistik kolom. |
| | [The Alchemist's Sandbox](miscellaneous-logic/the-alchemists-sandbox/README.md) | PyJail tanpa digit/kutip lewat `getattr` + `chr`, lalu balik transformasi 32 putaran. |
| | [Stay](miscellaneous-logic/stay/README.md) | Karakter Unicode zero-width sebagai alfabet 2 bit → Base64 → repeating-key XOR. |
| | [Wujud Aseli Atmin](miscellaneous-logic/wujud-aseli-atmin/README.md) | ZIP tersembunyi setelah `IEND`, perbaiki signature PNG, lalu LSB kanal merah. |
| | [SymHell](miscellaneous-logic/symhell/README.md) | Bash jail tanpa huruf/angka: glob `[_-{]`, aritmetika `$(())`, dan substring untuk membentuk `cat`. |
| **Forensics** | [Art Evidence Secret](forensics/art-evidence-secret/README.md) | Password dari metadata PNG, dua payload AES-GCM di LSB kanal merah dan biru. |
| | [Weak Handshake](forensics/weak-handshake/README.md) | Prima RSA berdekatan difaktorkan dengan Fermat, lalu sesi TLS 1.2 (EMS) didekripsi. |
| **Binary Exploitation (Pwn)** | [Pipa Nu Kotor](binary-exploit-pwn/pipa-nu-kotor/README.md) | Field `flags` tak terinisialisasi diwarisi lewat reuse tcache sehingga halaman proteksi bisa ditulis. |
| | [NFXCTF Convention](binary-exploit-pwn/nfxctf-convention/README.md) | Overwrite rank via `strcpy`, leak format string, lalu stack overflow ke `system("/bin/sh")`. |
| **Reverse Engineering** | [Medium RC4](reverse-engineering/medium-rc4/README.md) | Kunci dan ciphertext RC4 dibaca dari `.rodata`, lalu didekripsi (RC4 simetris). |
| | [Medium TEA](reverse-engineering/medium-tea/README.md) | Kunci TEA yang diobfuskasi sebagai `sub`/`add`, lalu dekripsi 32 ronde terbalik. |
| **Boot to Root** | [Forgotten Commit](boot-to-root/forgotten-commit/README.md) | Kredensial dari commit lama + dangling blob via `git fsck` → kunci XOR stream. |
| **OSINT** | [The Ghost Operator](osint/the-ghost-operator/README.md) | UID kunci GPG commit → rentry yang dihapus → Wayback Machine → geolokasi safehouse. |
| | [Fresh Arrival](osint/fresh-arrival/README.md) | Registrasi PK-ADL → MSN 26854 → fotografer JetPhotos dan operator pertama airframe. |
