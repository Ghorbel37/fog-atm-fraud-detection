from ftplib import FTP

FTP_HOST = "192.168.1.158"
FTP_USER = "fognode1"
FTP_PASS = "root"

REMOTE_DIR = "/"
LOCAL_DIR = "utils"  # dossier local sur la machine Fog

import os

def download_file(ftp, filename):
    local_path = os.path.join(LOCAL_DIR, filename)
    with open(local_path, "wb") as f:
        ftp.retrbinary(f"RETR {filename}", f.write)
    print(f"[DOWNLOAD] {filename} downloaded.")

def main():
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

    try:
        print("[INFO] Connecting to FTP...")
        ftp = FTP(FTP_HOST, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
        print("[SUCCESS] Connected.")

        ftp.cwd(REMOTE_DIR)

        files = ftp.nlst()
        print("[INFO] Files found:", files)

        for file in files:
            download_file(ftp, file)

        ftp.quit()
        print("[DONE] All model files downloaded.")

    except Exception as e:
        print("[ERROR] Failed:", e)

if __name__ == "__main__":
    main()
