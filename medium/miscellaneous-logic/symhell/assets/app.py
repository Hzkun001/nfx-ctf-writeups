import os
import re
import shutil
import socket
import subprocess
import threading

HOST = "0.0.0.0"
PORT = 1337

BANNER = (
    "\033[1;36m"
    "  ██████╗ ██╗   ██╗███╗   ███╗██╗  ██╗███████╗██╗     ██╗    \n"
    "  ██╔════╝╚██╗ ██╔╝████╗ ████║██║  ██║██╔════╝██║     ██║    \n"
    "  ███████╗ ╚████╔╝ ██╔████╔██║███████║█████╗  ██║     ██║    \n"
    "  ╚════██║  ╚██╔╝  ██║╚██╔╝██║██╔══██║██╔══╝  ██║     ██║    \n"
    "  ███████║   ██║   ██║ ╚═╝ ██║██║  ██║███████╗███████╗███████╗\n"
    "  ╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝\n"
    "\033[0m"
    "\033[1;33m  ═════════════════════════════════════════════════════════════\033[0m\n"
    "\033[1;35m  [!] EXTREME BASH JAIL (v3.0)\033[0m\n"
    "\033[1;30m  -------------------------------------------------------------\033[0m\n"
    "  \033[1;31m✖ Letters [a-z, A-Z]\033[0m   \033[1;30m|\033[0m \033[1;31m✖ Digits [0-9]\033[0m\n"
    "  \033[1;31m✖ Wildcards [?, *]\033[0m     \033[1;30m|\033[0m \033[1;31m✖ Hash [#]\033[0m\n"
    "  \033[1;31m✖ Herestrings [<<<]\033[0m    \033[1;30m|\033[0m \033[1;32m✔ Heredocs [<<] ALLOWED\033[0m\n"
    "\033[1;33m  ═════════════════════════════════════════════════════════════\033[0m\n\n"
    "\033[1;36msymhell\033[1;31m▸\033[0m "
)

PROMPT = "\033[1;36msymhell\033[1;31m▸\033[0m "
DENIED_MSG = (
    "\033[1;31m[!] ACCESS DENIED: Input contains forbidden characters! "
    "(a-z, A-Z, 0-9, ?, *, #, <<<)\033[0m\n" + PROMPT
)

def handle(conn):
    conn.sendall(BANNER.encode())

    while True:
        try:
            data = conn.recv(2048)
            if not data:
                break

            line = data.decode(errors="ignore").strip()
            if not line:
                conn.sendall(PROMPT.encode())
                continue

            if line.lower() in ["exit", "quit"]:
                break

            # Filter: Block letters, digits, wildcards ?, *, hash #, and herestrings <<<
            if re.search(r"[a-zA-Z0-9?*#]|\<{3}", line):
                conn.sendall(DENIED_MSG.encode())
                continue

            try:
                exec_path = shutil.which("bash") or "/bin/bash"
                res = subprocess.run(
                    line,
                    shell=True,
                    executable=exec_path,
                    capture_output=True,
                    text=True,
                    timeout=7,
                )
                out = res.stdout
                if not out:
                    out = res.stderr or "[!] No output returned"
            except subprocess.TimeoutExpired:
                out = "\033[1;31m[!] Command execution timed out.\033[0m"
            except Exception as e:
                out = f"\033[1;31m[!] Execution error: {e}\033[0m"

            conn.sendall(f"{out.strip()}\n{PROMPT}".encode())

        except Exception:
            break

    conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    print(f"[*] SymHell server listening on {HOST}:{PORT}")

    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=handle, args=(conn,), daemon=True)
            t.start()
        except Exception:
            pass

if __name__ == "__main__":
    main()
