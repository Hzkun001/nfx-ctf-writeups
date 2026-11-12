#!/usr/bin/env python3
import os, time
from os import urandom
from Crypto.Cipher import AES

FLAG = open("/app/flag.txt").read().strip().encode() if os.path.exists("/app/flag.txt") else b"NFX{placeholder}"
key_a = urandom(16)
key_b = urandom(16)
nonce = urandom(12)
idx = 0

def encrypt(key, pt):
    ct, tag = AES.new(key, AES.MODE_GCM, nonce=nonce).encrypt_and_digest(pt)
    return ct, tag

def decrypt(key, ct, tag):
    return AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag)

print("=" * 50)
print("  VaultGate — Encrypted Audit & Recovery")
print("=" * 50)
print("[1] Audit log  [2] Recovery log  [3] Sign  [4] Flag  [5] Exit")

while True:
    try:
        c = input("\n> ").strip()
        if c == "1":
            idx = (idx + 16) % 256
            msg = f"AUDIT|ts={int(time.time())}|r={urandom(4).hex()}|t={urandom(6).hex()}|OK".encode()
            ct, tag = encrypt(key_a, msg)
            print(f"Nonce: {nonce.hex()}\nLog [{msg.decode()}]\nCT: {ct.hex()}\nTag: {tag.hex()}")

        elif c == "2":
            idx = (idx - 16) % 256
            msg = f"RECOVERY|ts={int(time.time())}|r={urandom(4).hex()}|t={urandom(6).hex()}|OK".encode()
            ct, tag = encrypt(key_b, msg)
            print(f"Nonce: {nonce.hex()}\nLog [{msg.decode()}]\nCT: {ct.hex()}\nTag: {tag.hex()}")

        elif c == "3":
            ct = bytes.fromhex(input("CT: ").strip())
            tag = bytes.fromhex(input("Tag: ").strip())
            msg = decrypt(key_a, ct, tag)
            if b"admin = True" in msg:
                print("Error: cannot sign admin messages.")
            elif b"admin = False" not in msg[idx:idx + 16]:
                print(f"Error: need 'admin = False' at [{idx}:{idx + 16}].")
            else:
                print("OK")

        elif c == "4":
            ct = bytes.fromhex(input("CT: ").strip())
            tag = bytes.fromhex(input("Tag: ").strip())
            msg = decrypt(key_b, ct, tag)
            if b"admin = True" in msg[:idx] and b"admin = False" not in msg:
                print(FLAG.decode())
            else:
                print("Access denied.")

        elif c == "5":
            break
    except Exception as e:
        print(f"Error: {e}")
