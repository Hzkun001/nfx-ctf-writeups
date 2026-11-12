#!/usr/bin/env python3
"""
Differential Cryptanalysis Solver for 7-round Feistel Cipher
Challenge: Feistel Differential
Category: Crypto (Medium)
Flag: NFXCTF{d1ff3r3nt14l_crypt0_pwn5_f31st3l_45322835}
"""

import os
import sys

ROUNDS = 7
MASK16 = 0xFFFF

SBOX = [1, 8, 14, 12, 2, 0, 3, 4, 11, 9, 15, 13, 6, 10, 7, 5]
SBOX_INV = [0] * 16
for _i, _v in enumerate(SBOX):
    SBOX_INV[_v] = _i

partner = {0: 1, 1: 0, 2: 3, 3: 2}

def permute(m):
    n0 = m & 0xF
    n1 = (m >> 4) & 0xF
    n2 = (m >> 8) & 0xF
    n3 = (m >> 12) & 0xF
    return n1 | (n0 << 4) | (n3 << 8) | (n2 << 12)

def round_f(x, k):
    y = x ^ k
    m = (
        SBOX[y & 0xF]
        | (SBOX[(y >> 4) & 0xF] << 4)
        | (SBOX[(y >> 8) & 0xF] << 8)
        | (SBOX[(y >> 12) & 0xF] << 12)
    )
    return permute(m)

def encrypt_block(block, subkeys):
    L = (block >> 16) & MASK16
    R = block & MASK16
    for k in subkeys:
        L, R = R, L ^ round_f(R, k)
    return (L << 16) | R

def decrypt_block(block, subkeys):
    L = (block >> 16) & MASK16
    R = block & MASK16
    for k in reversed(subkeys):
        L, R = R ^ round_f(L, k), L
    return (L << 16) | R

DDT = [[0]*16 for _ in range(16)]
for x in range(16):
    for dx in range(16):
        dy = SBOX[x] ^ SBOX[x ^ dx]
        DDT[dx][dy] += 1

def parse_pairs(filename):
    sections = []
    current_diff = None
    current_pairs = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if current_diff is not None:
                    sections.append((current_diff, current_pairs))
                diff_str = line.split(':')[1].strip()
                current_diff = int(diff_str, 16)
                current_pairs = []
            else:
                parts = line.split()
                p = int(parts[0], 16)
                c1 = int(parts[1], 16)
                c2 = int(parts[2], 16)
                current_pairs.append((p, c1, c2))
    if current_diff is not None:
        sections.append((current_diff, current_pairs))
    return sections

def trace_best_trail(dL, dR, n_rounds):
    prob = 1.0
    for _ in range(n_rounds):
        dF_before_perm = 0
        for nib in range(4):
            dnib = (dR >> (4 * nib)) & 0xF
            if dnib == 0:
                continue
            best_dy = max(range(1, 16), key=lambda dy: DDT[dnib][dy])
            p = DDT[dnib][best_dy] / 16
            prob *= p
            dF_before_perm |= (best_dy << (4 * nib))
        dF = permute(dF_before_perm)
        dL, dR = dR, dL ^ dF
    return dL, dR, prob

def attack_key_nibble(pairs, exp_dL, exp_dR, nib_pos):
    out_nib = partner[nib_pos]
    votes = [0] * 16
    valid = 0

    for _, c1, c2 in pairs:
        c1_L = (c1 >> 16) & MASK16
        c2_L = (c2 >> 16) & MASK16
        c1_R = c1 & MASK16
        c2_R = c2 & MASK16

        dC_L = c1_L ^ c2_L
        dC_R = c1_R ^ c2_R

        if dC_L != exp_dR:
            continue

        f_diff = dC_R ^ exp_dL
        obs_out = (f_diff >> (4 * out_nib)) & 0xF
        if obs_out == 0:
            continue

        in_diff = (dC_L >> (4 * nib_pos)) & 0xF
        if DDT[in_diff][obs_out] == 0:
            continue

        valid += 1
        x1 = (c1_L >> (4 * nib_pos)) & 0xF
        for k_cand in range(16):
            y1 = x1 ^ k_cand
            y2 = y1 ^ in_diff
            if SBOX[y1] ^ SBOX[y2] == obs_out:
                votes[k_cand] += 1

    return votes, valid

def peel_last(sections_dict, key):
    new_dict = {}
    for diff, pairs in sections_dict.items():
        new_pairs = []
        for p, c1, c2 in pairs:
            c1_L = (c1 >> 16) & MASK16
            c1_R = c1 & MASK16
            c2_L = (c2 >> 16) & MASK16
            c2_R = c2 & MASK16

            prev_c1_R = c1_L
            prev_c1_L = c1_R ^ round_f(c1_L, key)
            new_c1 = (prev_c1_L << 16) | prev_c1_R

            prev_c2_R = c2_L
            prev_c2_L = c2_R ^ round_f(c2_L, key)
            new_c2 = (prev_c2_L << 16) | prev_c2_R

            new_pairs.append((p, new_c1, new_c2))
        new_dict[diff] = new_pairs
    return new_dict

def recover_subkeys(pairs_file):
    sections = parse_pairs(pairs_file)
    sections_dict = {diff: pairs for diff, pairs in sections}

    # Round 6
    trails_6r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL6, dR6, prob = trace_best_trail(dL0, dR0, 6)
        trails_6r[diff] = (dL6, dR6, prob)

    k6_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL6, dR6, _) in trails_6r.items():
        active = [(n, (dR6 >> (4 * n)) & 0xF) for n in range(4) if (dR6 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sections_dict[diff], dL6, dR6, nib)
            for i in range(16):
                k6_votes[nib][i] += v[i]

    K6 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k6_votes[nib][i])
        K6 |= best << (4 * nib)

    # Round 5
    sec6 = peel_last(sections_dict, K6)
    trails_5r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL5, dR5, prob = trace_best_trail(dL0, dR0, 5)
        trails_5r[diff] = (dL5, dR5, prob)

    k5_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL5, dR5, _) in trails_5r.items():
        active = [(n, (dR5 >> (4 * n)) & 0xF) for n in range(4) if (dR5 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sec6[diff], dL5, dR5, nib)
            for i in range(16):
                k5_votes[nib][i] += v[i]

    K5 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k5_votes[nib][i])
        K5 |= best << (4 * nib)

    # Round 4
    sec5 = peel_last(sec6, K5)
    trails_4r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL4, dR4, prob = trace_best_trail(dL0, dR0, 4)
        trails_4r[diff] = (dL4, dR4, prob)

    k4_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL4, dR4, _) in trails_4r.items():
        active = [(n, (dR4 >> (4 * n)) & 0xF) for n in range(4) if (dR4 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sec5[diff], dL4, dR4, nib)
            for i in range(16):
                k4_votes[nib][i] += v[i]

    K4 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k4_votes[nib][i])
        K4 |= best << (4 * nib)

    # Round 3
    sec4 = peel_last(sec5, K4)
    trails_3r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL3, dR3, prob = trace_best_trail(dL0, dR0, 3)
        trails_3r[diff] = (dL3, dR3, prob)

    k3_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL3, dR3, _) in trails_3r.items():
        active = [(n, (dR3 >> (4 * n)) & 0xF) for n in range(4) if (dR3 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sec4[diff], dL3, dR3, nib)
            for i in range(16):
                k3_votes[nib][i] += v[i]

    K3 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k3_votes[nib][i])
        K3 |= best << (4 * nib)

    # Round 2
    sec3 = peel_last(sec4, K3)
    trails_2r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL2, dR2, prob = trace_best_trail(dL0, dR0, 2)
        trails_2r[diff] = (dL2, dR2, prob)

    k2_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL2, dR2, _) in trails_2r.items():
        active = [(n, (dR2 >> (4 * n)) & 0xF) for n in range(4) if (dR2 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sec3[diff], dL2, dR2, nib)
            for i in range(16):
                k2_votes[nib][i] += v[i]

    K2 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k2_votes[nib][i])
        K2 |= best << (4 * nib)

    # Round 1
    sec2 = peel_last(sec3, K2)
    trails_1r = {}
    for diff in sections_dict:
        dL0 = (diff >> 16) & MASK16
        dR0 = diff & MASK16
        dL1, dR1, prob = trace_best_trail(dL0, dR0, 1)
        trails_1r[diff] = (dL1, dR1, prob)

    k1_votes = {n: [0] * 16 for n in range(4)}
    for diff, (dL1, dR1, _) in trails_1r.items():
        active = [(n, (dR1 >> (4 * n)) & 0xF) for n in range(4) if (dR1 >> (4 * n)) & 0xF]
        if not active:
            continue
        for nib, _ in active:
            v, _ = attack_key_nibble(sec2[diff], dL1, dR1, nib)
            for i in range(16):
                k1_votes[nib][i] += v[i]

    K1 = 0
    for nib in range(4):
        best = max(range(16), key=lambda i: k1_votes[nib][i])
        K1 |= best << (4 * nib)

    # Round 0: Direct inversion
    sec1 = peel_last(sec2, K1)
    diff0 = list(sec1.keys())[0]
    p, c1, _ = sec1[diff0][0]
    P_L = (p >> 16) & MASK16
    P_R = p & MASK16
    C_R = c1 & MASK16

    f_out = P_L ^ C_R
    sbox_out = permute(f_out)
    K0 = 0
    for nib in range(4):
        s_nib = (sbox_out >> (4 * nib)) & 0xF
        r_nib = (P_R >> (4 * nib)) & 0xF
        K0 |= (SBOX_INV[s_nib] ^ r_nib) << (4 * nib)

    return [K0, K1, K2, K3, K4, K5, K6]

def decrypt_ciphertext(subkeys, flag_enc_file):
    with open(flag_enc_file, 'r', encoding='utf-8') as f:
        ct_hex = f.read().strip()

    ct_bytes = bytes.fromhex(ct_hex)
    plaintext = b''
    for i in range(0, len(ct_bytes), 4):
        block = int.from_bytes(ct_bytes[i:i+4], 'big')
        dec = decrypt_block(block, subkeys)
        plaintext += dec.to_bytes(4, 'big')

    # Remove PKCS7 / zero padding
    pad_len = plaintext[-1]
    if 1 <= pad_len <= 4 and all(b == pad_len for b in plaintext[-pad_len:]):
        return plaintext[:-pad_len].decode('utf-8')
    return plaintext.rstrip(b'\x00').decode('utf-8', errors='ignore')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, 'assets')
    pairs_file = os.path.join(assets_dir, 'pairs.txt')
    flag_file = os.path.join(assets_dir, 'flag.enc')

    if not os.path.exists(pairs_file):
        # Fallback to local root if testing
        if os.path.exists('/home/hzsan/pairs.txt'):
            pairs_file = '/home/hzsan/pairs.txt'
            flag_file = '/home/hzsan/flag.enc'

    print("[*] Performing differential cryptanalysis on 7-round Feistel...")
    subkeys = recover_subkeys(pairs_file)
    print(f"[+] Recovered Subkeys: {[f'{k:04x}' for k in subkeys]}")

    flag = decrypt_ciphertext(subkeys, flag_file)
    print(f"[+] Flag: {flag}")
    return flag

if __name__ == '__main__':
    main()
