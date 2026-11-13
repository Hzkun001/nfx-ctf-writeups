# Hard VM Bytecode

[Indeks kategori](../README.md) · [Hard](../../README.md) · [Indeks utama](../../../README.md)

| Informasi | Nilai |
| --- | --- |
| Kategori | Reverse Engineering |
| Difficulty | Hard |
| Author | cypera |
| Lampiran / sumber | [assets/hard_vm](assets/hard_vm) (ELF 64-bit LSB PIE, stripped, dari `NFCC-Com/qazwsx`, `rev/Hard_01_VM_Bytecode/hard_vm`) |
| Verifikasi | Lokal: `./assets/hard_vm '<flag>'` mencetak `Correct! Bytecode VM berhasil dibongkar.` |

## Ringkasan

Binary bukan validator biasa: ia menjalankan **bytecode kustom** pada VM kecil
dengan interpreter berbasis *jump table*. Setiap karakter diproses oleh satu blok
lima instruksi tetap — **LOAD, XOR, ADD, ROL, CMP** — dan program terdiri dari 33
blok (33 karakter flag) ditutup opcode **HALT**.

Karena setiap blok hanya berisi operasi satu arah yang semuanya dapat dibalik
(`ROL`, `ADD`, `XOR`), flag dapat dipulihkan langsung dari operand `CMP` tiap
blok tanpa perlu mengeksekusi VM-nya sama sekali. Tidak ada cabang, tidak ada
umpan balik antarblok — cukup satu pass.

## Alur penyelesaian

### 1. Pemeriksaan awal

```bash
file assets/hard_vm        # ELF 64-bit LSB pie executable, stripped
strings -a assets/hard_vm | grep -iE 'pemakaian|wrong|correct'
```

```text
Pemakaian: %s <flag>
Wrong!
Correct! Bytecode VM berhasil dibongkar.
```

Panjang input divalidasi `strlen(argv[1]) == 0x21` (33 byte).

### 2. Memetakan VM di `.rodata`

```bash
objdump -s -j .rodata assets/hard_vm
```

| Alamat | Ukuran | Peran |
| --- | --- | --- |
| `0x2060` | 24 byte (6 × int32) | tabel dispatch opcode → handler |
| `0x2080` | 498 byte (166 × 3) | bytecode program |

Interpreter melakukan:

```text
movsxd rax, [rdi + rax*4]     ; rdi = 0x2060
add    rax, rdi
jmp    rax
```

sehingga tiap entri tabel adalah **offset relatif** terhadap `0x2060`. Hasil
resolve-nya:

| Opcode | Target | Handler |
| --- | --- | --- |
| 1 | `0x11b6` | `reg[rsi] = flag[rcx]` — **LOAD** |
| 2 | `0x11a8` | `reg[rsi] ^= rcx` — **XOR** |
| 3 | `0x115c` | `reg[rsi] += rcx` — **ADD** |
| 4 | `0x119d` | `reg[rsi] = rol8(reg[rsi], rcx & 7)` — **ROL** |
| 5 | `0x11ae` | `if (reg[rsi] != rcx) fail` — **CMP** |
| 0xff | `0x11cc` | sukses — **HALT** |

Catatan: entri opcode **0** juga menunjuk ke handler LOAD, tetapi tidak pernah
dipakai karena interpreter menolak opcode 0 lebih dulu (`test al,al; je wrong`).

### 3. Struktur program

166 instruksi = 165 instruksi body + 1 HALT, dengan pola berulang tiap 5:

```text
01 00 i       LOAD  reg[0] = flag[i]      (i = indeks blok)
02 00 k1      XOR   reg[0] ^= k1
03 00 k2      ADD   reg[0] += k2
04 00 r       ROL   reg[0] = rol8(reg[0], r)
05 00 t       CMP   reg[0] == t           (target)
```

Jadi tiap karakter dihitung independen:

```text
t = rol8( flag[i] ^ k1 + k2 , r )
```

### 4. Membalik transformasi

Karena semua operasi invertibel, balik urutannya per blok:
**ROR** (kebalikan ROL) → **SUB** (kebalikan ADD) → **XOR**.

```python
x = target
x = rotr8(x, r)          # kebalikan ROL
x = (x - k2) & 0xff      # kebalikan ADD
x ^= k1                  # kebalikan XOR
```

Atau langsung jalankan solver:

```bash
python3 solve.py
```

### 5. Verifikasi hasil

```bash
./assets/hard_vm 'NFX{vm_byt3c0d3_1s_l1k3_4_puzzl3}'
# Correct! Bytecode VM berhasil dibongkar.

./assets/hard_vm 'NFX{aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}'
# Wrong!
```

## Flag

```text
NFX{vm_byt3c0d3_1s_l1k3_4_puzzl3}
```

## Reproduksi

Hanya butuh Python 3 (pustaka standar, tanpa dependensi eksternal):

```bash
# 1. Jalankan solver
python3 solve.py

# 2. Jalankan unit test
python3 -m unittest -v
```

[solve.py](solve.py) memverifikasi SHA-256 lampiran, me-resolve tabel dispatch
dari `.rodata` (bukan hardcode nama opcode), mem-parse bytecode hingga HALT,
memvalidasi pola tiap blok, lalu membalik ROL/ADD/XOR untuk mencetak flag.
[test_solve.py](test_solve.py) menguji keutuhan berkas input, kebenaran flag,
pemetaan tabel dispatch (termasuk entri 0 yang duplikat), **eksekusi VM
reimplementasi** yang menerima flag benar dan menolak flag salah, terminator
HALT, inversi rotasi, dan penolakan berkas yang dimodifikasi.

## Bukti

- Berkas tantangan terverifikasi: [assets/hard_vm](assets/hard_vm)
  (SHA256: `54cc69e2f8213ccb685818c3a371a08c87caf9d487d5a47b157ab3bcf7f93697`).
- Tabel dispatch di `0x2060`, bytecode 498 byte di `0x2080`.
- Output verifikasi: `./assets/hard_vm '<flag>'` → `Correct! Bytecode VM berhasil dibongkar.`
- VM reimplementasi (LOAD/XOR/ADD/ROL/CMP) meloloskan flag yang dipulihkan dan
  menolak flag salah — diuji otomatis.

## Penggunaan AI

Penyusunan solver (resolve tabel dispatch dan pembalikan blok instruksi) serta
penyuntingan naskah writeup dibantu oleh model AI; seluruh langkah analisis dan
verifikasi dijalankan ulang secara lokal.
