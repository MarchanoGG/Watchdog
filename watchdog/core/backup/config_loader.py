import json
import os
from pathlib import Path

class BackupConfig:
    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = json.load(f)

    def get_servers(self):
        servers = self.config.get("servers", [])
        for server in servers:
            if server.get("ssh", {}).get("password", "").startswith("env:"):
                env_var = server["ssh"]["password"].split("env:")[1]
                server["ssh"]["password"] = os.getenv(env_var)

            if (mysql := server.get("mysql")) and isinstance(mysql.get("password"), str):
                if mysql["password"].startswith("env:"):
                    env_var = mysql["password"].split("env:")[1]
                    mysql["password"] = os.getenv(env_var)
                    
        return servers