import subprocess

class RsyncHandler:
    def __init__(self, host, user="root", port=22):
        self.host = host
        self.user = user
        self.port = port

    def download(self, remote_path, local_path):
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -p {self.port}",
            f"{self.user}@{self.host}:{remote_path}",
            local_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Rsync failed: {result.stderr.decode()}")
        return result.stdout.decode()
