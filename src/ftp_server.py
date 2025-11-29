import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def create_symlink_or_copy(src, dst):
    """Create symlink if supported, else copy file."""
    if os.name != "nt":  # Windows does not allow symlink without admin
        try:
            os.symlink(src, dst)
            return
        except:
            pass
    # fallback: create a copy
    if os.path.isdir(src):
        import shutil
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        import shutil
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

        # Create symlink/copy to models (shared folder)
        if not os.path.exists(models_link):
            create_symlink_or_copy(models_dir, models_link)

        # Copy the correct simulation file
        if os.path.exists(data_file_src):
            create_symlink_or_copy(data_file_src, data_file_dst)

    # FTP User Setup
    authorizer = DummyAuthorizer()
    for node in fog_nodes:
        # restrict user to its own folder only
        home_dir = os.path.join(ftp_root, f"fognode{node}")
        authorizer.add_user(
            f"fognode{node}", "root", home_dir, perm="elr"
        )

    handler = FTPHandler
    handler.authorizer = authorizer

    address = ("0.0.0.0", 21)
    server = FTPServer(address, handler)

    print("FTP Server running. Each fognode has isolated access.")
    server.serve_forever(timeout=1)

if __name__ == "__main__":
    main()
