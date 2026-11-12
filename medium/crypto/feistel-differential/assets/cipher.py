ROUNDS = 7
MASK16 = 0xFFFF

SBOX = [1, 8, 14, 12, 2, 0, 3, 4, 11, 9, 15, 13, 6, 10, 7, 5]
SBOX_INV = [0] * 16
for _i, _v in enumerate(SBOX):
    SBOX_INV[_v] = _i


def permute(m):
    """Swap nibble pairs: [n0,n1,n2,n3] -> [n1,n0,n3,n2]."""
    n0 = m & 0xF
    n1 = (m >> 4) & 0xF
    n2 = (m >> 8) & 0xF
    n3 = (m >> 12) & 0xF
    return n1 | (n0 << 4) | (n3 << 8) | (n2 << 12)


def permute_inv(m):
    """Swap is an involution: its own inverse."""
    return permute(m)


def round_f(x, k):
    y = x ^ k
    m = (
        SBOX[y & 0xF]
        | (SBOX[(y >> 4) & 0xF] << 4)
        | (SBOX[(y >> 8) & 0xF] << 8)
        | (SBOX[(y >> 12) & 0xF] << 12)
    )
    return permute(m)


def key_schedule(master):
    """Split a 112-bit master key into seven 16-bit round subkeys."""
    return [(master >> (16 * i)) & MASK16 for i in range(ROUNDS)]


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
