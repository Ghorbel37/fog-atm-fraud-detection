from ftplib import FTP, error_perm
import os

# ---------- CONFIGURATION ----------
FTP_HOST = "192.168.1.158"
FTP_USER = "fognode1"
FTP_PASS = "root"
LOCAL_ROOT = "."  # Local folder to save files

# ---------- FUNCTION ----------
def download_ftp_tree(ftp: FTP, remote_dir: str, local_dir: str, indent: str = ""):
    """
    Recursively downloads files from FTP server while preserving folder structure.
    """
    try:
        ftp.cwd(remote_dir)
    except error_perm:
        # It's a file
        local_file_path = os.path.join(local_dir, remote_dir)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        with open(local_file_path, 'wb') as f:
            ftp.retrbinary(f"RETR {remote_dir}", f.write)
        print(f"[DOWNLOADING] {remote_dir}")
        return

    # It's a folder
    print(f"[FOLDER] {remote_dir}/")
    os.makedirs(os.path.join(local_dir, remote_dir), exist_ok=True)

    file_list = []
    ftp.retrlines("NLST", file_list.append)

    for item in file_list:
        download_ftp_tree(ftp, item, os.path.join(local_dir, remote_dir), indent + "    ")

    ftp.cwd("..")

# ---------- MAIN SCRIPT ----------
def main():
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    print(f"Connected to FTP server: {FTP_HOST}\n")

    # List root folders/files
    root_items = []
    ftp.retrlines("NLST", root_items.append)

    for item in root_items:
        download_ftp_tree(ftp, item, LOCAL_ROOT)

    ftp.quit()
    print("\nAll files downloaded successfully.")

if __name__ == "__main__":
    main()
