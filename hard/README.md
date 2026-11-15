# Hard Challenges — NFX CTF 2026

[← Kembali ke Indeks Utama](../README.md)

Daftar 9 challenge tingkat kesulitan **Hard** yang berhasil diselesaikan pada NFX CTF 2026.

---

## Ringkasan Solves (9 Challenge)

| Kategori | Challenge | Deskripsi Singkat |
| --- | --- | --- |
| **Cryptography** | [Broken Signature Scheme](crypto/broken-signature-scheme/README.md) | Tanda tangan RSA multiplicative dipalsukan, n difaktorkan Fermat, kunci AES-GCM dari `p‖q`. |
| | [FlagKeepers](crypto/flagkeepers/README.md) | Nonce reuse AES-GCM → H dipulihkan lewat GCD polinomial → tag palsu untuk `admin = True`. |
| **Binary Exploitation (Pwn)** | [TheForgottenState](binary-exploit-pwn/theforgottenstate/README.md) | Use-after-free pada `table[i]` → fake header untuk arbitrary R/W → `free@got` jadi `system`. |
| **Reverse Engineering** | [Castaway](reverse-engineering/castaway/README.md) | State berantai bergantung pada ciphertext sehingga tiap byte bisa dibalik; opaque predicate selalu false. |
| | [Hard VM Bytecode](reverse-engineering/vm-bytecode/README.md) | Resolve jump table VM, lalu balik blok LOAD/XOR/ADD/ROL/CMP per karakter. |
| | [Hard Feistel](reverse-engineering/feistel/README.md) | Feistel 16 ronde dibalik dengan round key dari `.rodata` dan ciphertext di `.data`. |
| **Forensics** | [Bluebird Session](forensics/bluebird-session/README.md) | Crack hash shadow, dekripsi GNOME Keyring v0, lalu password arsip dipakai sebagai flag. |
| **Miscellaneous & Logic** | [My Lovely Freya](miscellaneous-logic/my-lovely-freya/README.md) | Tinggi PNG dipulihkan dari panjang scanline; password di gambar membuka surat AES-256-CBC. |
| **OSINT** | [Tragedi 9/11](osint/tragedi-9-11/README.md) | Pengunggah video di Reddit → akun GitHub → flag di riwayat commit `.env`. |
