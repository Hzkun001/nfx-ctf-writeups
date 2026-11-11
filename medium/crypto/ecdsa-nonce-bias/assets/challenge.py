# ======================= challenge.py =======================
# FILE UNTUK PESERTA — hanya ringkasan, tanpa solusi.
import json, sys

def load(path="output.txt"):
    return json.load(open(path))

def main():
    d = load(sys.argv[1] if len(sys.argv) > 1 else "output.txt")
    print("kurva        :", d["curve"])
    print("jumlah sig   :", len(d["signatures"]))
    s0 = d["signatures"][0]
    print("contoh r     :", s0["r"][:18], "...")
    print("contoh s     :", s0["s"][:18], "...")
    print("contoh h     :", s0["h"][:18], "...")
    print("top8_k       :", s0["top8_k"], " K_BITS =", s0["K_BITS"])
    print("flag cipher  : nonce=%s..., tag=%s..." %
          (d["flag_ciphertext"]["nonce_hex"][:8],
           d["flag_ciphertext"]["tag_hex"][:8]))
    print()
    print("hint 1: nonce k < 2^248, 8 bit teratas selalu 0")
    print("hint 2: ini HNP, susun lattice, LLL/BKZ, recover d")
    print("hint 3: key AES-GCM = SHA256(d), d dalam 32 byte big-endian")

if __name__ == "__main__":
    main()