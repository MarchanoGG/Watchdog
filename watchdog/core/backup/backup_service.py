from watchdog.core.backup.ssh_handler import SSHHandler
from watchdog.core.backup.rsync_handler import RsyncHandler
from watchdog.utils.logger import WatchdogLogger
from pathlib import Path
from datetime import datetime

class BackupService:
    def __init__(self, config):
        self.config = config
        self.logger = WatchdogLogger("backup")

    def backup_all(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        servers = self.config.get_servers()

        for server in servers:
            self.logger.info(f"Start backup process {server['name']}")

            ssh_cfg = server["ssh"]
            ssh = SSHHandler(
                host=server["ip"],
                username=ssh_cfg["user"],
                password=ssh_cfg["password"],
                port=ssh_cfg.get("port", 22)
            )
            ssh.connect()
            self.logger.info(f"Connected to {server['name']} via SSH")
            
            rsync = RsyncHandler(server["ip"], user=ssh_cfg["user"], port=ssh_cfg.get("port", 22))

            # Create local backup directory
            local_base = Path(f"/mnt/ssd/backups/{timestamp}/{server['name'].lower()}/")
            local_base.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Local backup directory created: {local_base}")
            
            # Collect exclude patterns
            exclude_flags = " ".join(
                f"--exclude='{pattern}'" for pattern in server.get("excludes", [])
            )
            self.logger.info(f"Excluding patterns: {exclude_flags}")

            for target in server["targets"]:
                self.logger.info(f"Backing up {target['path']} from {server['name']}")
                remote_tmp = f"/tmp/backup_{Path(target['path']).name}.tar.gz"
                
                ssh.exec_sudo(
                    f"tar -czf {remote_tmp} {exclude_flags} {target['path']}"
                )
                
                rsync.download(remote_tmp, str(local_base))
                ssh.exec_sudo(f"rm {remote_tmp}")

            ssh.close()
            self.logger.info(f"Backup process for {server['name']} completed successfully")