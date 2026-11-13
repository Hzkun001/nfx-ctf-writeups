# ======================= challenge.py =======================
# FILE UNTUK PESERTA
# Skrip ini memperlihatkan bagaimana flag dienkripsi. MASTER terbuka.
import hashlib, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

MASTER = b"\x13\x37" * 16           # <-- ini bocor, bug kedua
PREFIX = b"user-input-goes-here:"

def get_key(counter):
    return hashlib.sha256(MASTER + counter.to_bytes(4, "little")).digest()[:32]

def encrypt_flag(flag: bytes, iv: bytes, counter: int) -> bytes:
    key = get_key(counter)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(PREFIX + b"|" + flag, 16))

if __name__ == "__main__":
    data = json.load(open("output.txt"))
    print("counter:", data["counter"])
    print("iv_hex :", data["iv_hex"])
    print("ct_hex :", data["ct_hex"][:64], "...")
    print("hint: MASTER ada di file ini. counter ada di output.txt.")