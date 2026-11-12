#!/usr/bin/env python3
"""
Solver for Forgotten Commit (Boot to Root / Git Recovery)
Challenge: Forgotten Commit
Category: Boot to Root (Medium)
Flag: NFXCTF{g1t_d4ngl1ng_bl0b_h4v0c_5c8a19d4}
"""

import hashlib
import os
import re
import subprocess
import tarfile
import tempfile

def solve(tar_path=None, blob_path=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not tar_path:
        tar_path = os.path.join(base_dir, 'assets', 'shadow_repo.tar.gz')
    if not blob_path:
        blob_path = os.path.join(base_dir, 'assets', '21d5a194fb6a627b1702cbf74b51589789988b72.blob')

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract archive
        with tarfile.open(tar_path, 'r:*') as tar:
            tar.extractall(path=tmpdir)

        repo_dir = tmpdir
        # Find directory containing .git
        for root, dirs, _ in os.walk(tmpdir):
            if '.git' in dirs:
                repo_dir = root
                break

        # 1. Recover author email from initial commit (706f270)
        # Using git log
        cmd_author = ['git', '-C', repo_dir, 'log', '--format=%ae', '706f2702eb1a619012bb71c58e2b3db82049d1b9', '-n', '1']
        res = subprocess.run(cmd_author, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        author_email = res.stdout.strip()

        # 2. Recover leaked AWS key from .env.staging at initial commit
        cmd_show = ['git', '-C', repo_dir, 'show', '706f2702eb1a619012bb71c58e2b3db82049d1b9:.env.staging']
        res_env = subprocess.run(cmd_show, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        env_content = res_env.stdout
        m_aws = re.search(r'AWS_ACCESS_KEY_ID=([A-Za-z0-9_-]+)', env_content)
        aws_key = m_aws.group(1) if m_aws else ''

        # 3. Recover PGP fingerprint and encrypted flag hex from dangling blob
        blob_content = ''
        if os.path.exists(blob_path):
            with open(blob_path, 'r', encoding='utf-8', errors='ignore') as f:
                blob_content = f.read()
        else:
            # Check git fsck
            cmd_fsck = ['git', '-C', repo_dir, 'fsck', '--lost-found']
            res_fsck = subprocess.run(cmd_fsck, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Read dangling blob
            m_dangling = re.search(r'dangling blob ([0-9a-f]{40})', res_fsck.stdout + res_fsck.stderr)
            if m_dangling:
                blob_hash = m_dangling.group(1)
                cmd_cat = ['git', '-C', repo_dir, 'cat-file', '-p', blob_hash]
                blob_content = subprocess.run(cmd_cat, stdout=subprocess.PIPE, text=True, check=True).stdout

        m_pgp = re.search(r'PGP_FINGERPRINT=([A-Za-z0-9_-]+)', blob_content)
        pgp_fingerprint = m_pgp.group(1) if m_pgp else ''

        m_flag_hex = re.search(r'ENCRYPTED_FLAG_HEX=([0-9a-fA-F]+)', blob_content)
        flag_hex = m_flag_hex.group(1) if m_flag_hex else ''

        # 4. Form key string and decrypt
        key_str = f"{author_email}|{aws_key}|{pgp_fingerprint}"
        key = hashlib.sha256(key_str.encode('utf-8')).digest()

        ct = bytes.fromhex(flag_hex)
        stream = b''
        counter = 0
        while len(stream) < len(ct):
            stream += hashlib.sha256(key + counter.to_bytes(4, 'big')).digest()
            counter += 1

        plaintext = bytes([c ^ s for c, s in zip(ct, stream[:len(ct)])])
        flag = plaintext.decode('utf-8')
        return {
            'author_email': author_email,
            'aws_key': aws_key,
            'pgp_fingerprint': pgp_fingerprint,
            'key_str': key_str,
            'flag': flag
        }

def main():
    result = solve()
    print(f"[*] Author Email: {result['author_email']}")
    print(f"[*] Leaked AWS Key: {result['aws_key']}")
    print(f"[*] PGP Fingerprint: {result['pgp_fingerprint']}")
    print(f"[*] KDF Key String: {result['key_str']}")
    print(f"[+] Recovered Flag: {result['flag']}")

if __name__ == '__main__':
    main()
