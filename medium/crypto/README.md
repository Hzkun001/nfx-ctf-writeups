# Medium · Crypto

[Kembali ke Medium](../README.md) · [Indeks utama](../../README.md)

Tantangan kriptografi: enkripsi, encoding, skema tanda tangan, dan konstruksi
matematis lemah.

| Challenge | Writeup | Verifikasi |
| --- | --- | --- |
| Black Box Protocol N4T0 | [Baca penyelesaian](blackbox-protocol-n4t0/README.md) | Lokal; float32 round-trip, mask huruf, dan panjang bagian diverifikasi |
| ECDSA Nonce Bias | [Baca penyelesaian](ecdsa-nonce-bias/README.md) | Lokal; 200 tanda tangan, public key, batas nonce, dan tag AES-GCM terverifikasi |
| Unbreakable Delay | [Baca penyelesaian](unbreakable-delay/README.md) | Live & lokal; branch-and-bound factoring dari p ^ q dan bypass Wesolowski VDF via phi(n) |
| Feistel Differential | [Baca penyelesaian](feistel-differential/README.md) | Lokal; karakteristik diferensial 6-round, pemulihan 7 subkunci (112-bit), dan dekripsi flag |
| Cihuy LWE | [Baca penyelesaian](cihuy-lwe/README.md) | Lokal; pemulihan rahasia LWE ternary via Kannan embedding LLL/BKZ, PRF counter SHA-256 terverifikasi |
| Static IV Offline | [Baca penyelesaian](static-iv-offline/README.md) | Lokal; derivasi kunci AES-256-CBC dari MASTER & counter, unpadding PKCS#7, flag terdekripsi sempurna |
| RSA Coppersmith Cihuy | [Baca penyelesaian](rsa-coppersmith-cihuy/README.md) | Lokal; reduksi kisi Howgrave-Graham LLL via python-flint, pemulihan 212-bit LSB p, faktorisasi modulus n 1024-bit, dekripsi flag RSA |
