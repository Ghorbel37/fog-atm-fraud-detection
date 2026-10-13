import os
import shutil
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def refresh_copy(src, dst):
    """Replace dst with a fresh copy of src (file or folder).

    Copies instead of symlinks: pyftpdlib refuses to serve symlinks that
    point outside the user's home folder, and copying on every start keeps
    the files up to date after retraining.
    """
    if os.path.islink(dst) or os.path.isfile(dst):
        os.remove(dst)
    elif os.path.isdir(dst):
        shutil.rmtree(dst)

    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(project_root, "models")
    data_dir = os.path.join(project_root, "data")

    # Where FTP user folders will be stored
    ftp_root = os.path.join(project_root, "ftp_root")
    os.makedirs(ftp_root, exist_ok=True)

    # Fog node list
    fog_nodes = [1, 2]

    for node in fog_nodes:
        node_dir = os.path.join(ftp_root, f"fognode{node}")
        models_link = os.path.join(node_dir, "models")
        data_subdir = os.path.join(node_dir, "data")
        data_file_src = os.path.join(data_dir, f"simulation_node_{node}.csv")
        data_file_dst = os.path.join(data_subdir, f"simulation_node_{node}.csv")

        # Create directories
        os.makedirs(node_dir, exist_ok=True)
        os.makedirs(data_subdir, exist_ok=True)

        # Copy the models (shared folder)
        if os.path.isdir(models_dir):
            refresh_copy(models_dir, models_link)
        else:
            print(f"Warning: {models_dir} not found, no models to serve.")

        # Copy the correct simulation file
        if os.path.exists(data_file_src):
            refresh_copy(data_file_src, data_file_dst)
        else:
            print(f"Warning: {data_file_src} not found.")

    # FTP User Setup
    ftp_password = os.getenv("FTP_PASSWORD", "root")
    ftp_port = int(os.getenv("FTP_PORT", "21"))
    authorizer = DummyAuthorizer()
    for node in fog_nodes:
        # restrict user to its own folder only
        home_dir = os.path.join(ftp_root, f"fognode{node}")
        authorizer.add_user(
            f"fognode{node}", ftp_password, home_dir, perm="elr"
        )

    handler = FTPHandler
    handler.authorizer = authorizer

    address = ("0.0.0.0", ftp_port)
    server = FTPServer(address, handler)

    print("FTP Server running. Each fognode has isolated access.")
    server.serve_forever(timeout=1)

if __name__ == "__main__":
    main()

# Run with:
# python.exe .\src\ftp_server.py 
