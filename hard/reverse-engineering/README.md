# Hard · Reverse Engineering

[Kembali ke Hard](../README.md) · [Indeks utama](../../README.md)

Analisis program dan rekonstruksi algoritma atau perilakunya.

| Challenge | Writeup | Verifikasi |
| --- | --- | --- |
| Castaway | [Baca penyelesaian](castaway/README.md) | Lokal; state berantai diturunkan dari ciphertext sehingga transformasi per byte bisa dibalik (binary menerima flag) |
| Hard VM Bytecode | [Baca penyelesaian](vm-bytecode/README.md) | Lokal; resolve jump table VM, lalu balik blok LOAD/XOR/ADD/ROL/CMP per karakter (binary menerima flag) |
| Hard Feistel | [Baca penyelesaian](feistel/README.md) | Lokal; Feistel 16 ronde dibalik dengan round key dari `.rodata` (binary menerima flag) |
