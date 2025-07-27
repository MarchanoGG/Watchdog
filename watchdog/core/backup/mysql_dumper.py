"""
    MySQL dump helper - creates a gz-compressed dump on the remote host
    and downloads it via rsync.
"""

from __future__ import annotations

from watchdog.core.verify.manifest import Manifest
from watchdog.core.verify.checksum import sha256_stream, xxh3_stream

from pathlib import Path
from datetime import datetime
from typing import Dict

from watchdog.utils.logger import WatchdogLogger
from .ssh_handler import SSHHandler
from .rsync_handler import RsyncHandler


class MySQLDumper:
    def __init__(
        self,
        ssh: SSHHandler,
        rsync: RsyncHandler,
        mysql_cfg: Dict,
        server_name: str,
        local_base: Path,
        manifest: Manifest,
    ) -> None:
        self.ssh = ssh
        self.rsync = rsync
        self.cfg = mysql_cfg
        self.server_name = server_name
        self.local_base = local_base
        self.manifest = manifest
        self.logger = WatchdogLogger("backup")

    def dump(self) -> None:
        if not self.cfg.get("enabled", True):
            self.logger.info(f"MySQL dump disabled for {self.server_name}")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_tmp = f"/tmp/mysql_{ts}.sql.gz"
        local_file = self.local_base / f"mysql_{ts}.sql.gz"

        user = self.cfg["user"]
        pw   = self.cfg["password"]
        port = self.cfg.get("port", 3306)
        extra = self.cfg.get("dump_options", "")

        self.logger.info(f"Dumping MySQL on {self.server_name} …")

        # Note: using single quotes around password to avoid issues with special chars
        dump_cmd = (
            f"mysqldump -h127.0.0.1 -P{port} -u{user} -p'{pw}' "
            f"--all-databases {extra} | gzip > {remote_tmp}"
        )

        out, err, code = self.ssh.exec(dump_cmd)

        # Check for insecure password usage
        insecure_msg = "mysqldump: [Warning] Using a password on the command line interface can be insecure."
        err_clean = err.replace(insecure_msg, "").strip()

        if code != 0:
            self.logger.error(f"mysqldump exit {code}: {err_clean}")
            raise RuntimeError("MySQL dump failed")
        if err_clean:
            self.logger.warning(f"mysqldump stderr: {err_clean}")

        self.rsync.download(remote_tmp, str(self.local_base))
        self.ssh.exec_sudo(f"rm {remote_tmp}")

        sha = sha256_stream(local_file)
        xxh = xxh3_stream(local_file)
        self.manifest.add_artifact(
            path=local_file,
            sha256=sha,
            size=local_file.stat().st_size,
            art_type="mysql",
            xxh3=xxh,
        )

        self.logger.info(f"MySQL dump saved → {local_file}")
