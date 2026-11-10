# ======================= challenge.py =======================
import json, sys

def load(path="output.txt"):
    return json.load(open(path))

def main():
    d = load(sys.argv[1] if len(sys.argv) > 1 else "output.txt")
    N = int(d["N"], 16)
    print("N bits     :", N.bit_length())
    print("e          :", d["e"])
    print("leak       :", d["leak"], "pos", d["leak_pos"], "bits", d["leak_bits"])
    print("delta_bits :", d["delta_bits"])
    print("valid sigs :", len(d["valid_sigs"]))
    print("target msg :", bytes.fromhex(d["target_msg_hex"]))
    print()
    print("Skema: sig(m) = m^d mod N  (RSA multiplicative, H identitas)")
    print("RSA  : q = nextprime(p + 2^300), leak 20 bit tengah p")
    print("Flag : AES-GCM, key = SHA256(p||q)")
    print("Petunjuk layer 1: produk sig(m_i) menghasilkan sig(prod m_i)")

if __name__ == "__main__":
    main()