# WatchDog

Automated **back-ups**, **verification** & **uptime monitoring** for a Linux Server
— with instant Discord alerts.

> **TL;DR install**

```bash
# Requirements (Ubuntu 24.04 Server)
sudo apt update && sudo apt install git rsync curl tar python3-venv

# 1 Clone
sudo git clone https://github.com/MarchanoGG/WatchDog.git /opt/watchdog
cd /opt/watchdog

# 2 Configs
cp watchdog/config/backup_config.json.example  watchdog/config/backup_config.json
cp watchdog/config/status_config.json.example  watchdog/config/status_config.json
nano watchdog/config/*.json            # fill in servers, urls, passwords

# 3 Create venv + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4 Systemd service
sudo cp docs/watchdog.service.template /etc/systemd/system/watchdog.service
sudo systemctl daemon-reload && sudo systemctl enable --now watchdog

# 5 Webhook secret
echo "DISCORD_WEBHOOK_URL=your_webhook" | sudo tee -a /opt/watchdog/.env
```

## Features

| Module            | What it does | Default schedule |
| :---------------- | :------ | :---- |
| BackupService        |   	Tar+gzip website files, /etc/, MySQL dump over SSH, download via rsync to external SSD   | 22:30 daily |
| Manifest          |   Writes SHA-256 + xxh3 checksums for each artefact	   | immediately after each file |
| VerifierService   |  Streams files once → validates hash, `gzip -t`, tar headers, MySQL footer   | right after back-up |
| StatusChecker |  	Every 30 s: HTTP/HTTPS or TCP ping. Sends 🔴 / 🟢 to Discord on UP↔DOWN transitions   | 30 s |
| PulseService |  Daily summary embed (backup ✔ / verify ✔)	  | 	22:30 daily |
| CLI wrapper |  	`watchdog backup`, `watchdog pulse`, `watchdog notify`  | on demand |

## Project layout
```bash
/opt/watchdog
├── watchdog.sh                # CLI bin (symlinked to /usr/local/bin/watchdog)
├── watchdog/                  # Python package
│   ├── core/
│   │   ├── backup/            # BackupService, SSH/Rsync helpers
│   │   ├── verify/            # VerifierService + inspectors
│   │   ├── status/            # StatusChecker
│   │   ├── pulse/             # PulseService
│   ├── config/                # *.json configs
│   └── utils/                 # Logger & flag helpers
├── logs/                      # Rotated daily (backup.log, status.log, …)
└── docs/                      # watchdog.service.template, extra notes

```

## Configuration files

1 - backup_config.json
```json
{
  "servers": [
    {
      "name": "ServerName",
      "ip":   "192.168.1.1",
      "ssh":  { "user": "watchdog", "password": "env:SERVER_SERVERNAME_PASSWORD" },
      "mysql":{ "enabled": true,
                "user": "root",
                "password": "env:MYSQL_SERVERNAME_ROOT_PASSWORD",
                "dump_options": "--single-transaction --quick --lock-tables=false" },
      "excludes": ["node_modules"],
      "targets": [
        { "path": "/sites/", "type": "directory", "verify": true },
        { "path": "/etc/",   "type": "list",      "verify": false }
      ]
    }
  ]
}
```

2 - status_config.json
```json
{
  "interval_sec": 30,
  "timeout_sec": 5,
  "targets": [
    { "name": "Website Name", "url": "https://websitername.nl", "method": "https" },
    { "name": "DB-port", "host": "136.144.164.5", "port": 3306, "method": "tcp" }
  ]
}
```

3 - .env
```ini
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SERVER_SERVERNAME_PASSWORD=superSecretSSH
MYSQL_SERVERNAME_ROOT_PASSWORD=anotherSecret
```

## CLI usage

| Command            | Effect | 
| :---------------- | :------ | 
| `watchdog backup`  | 	Run backup flow immediately  | 
| `watchdog pulse` | Run backup → verify → Discord summary   | 
| `watchdog notify`   |  Test-message to Discord | 

## How verification works

1. Manifest stores filename + size + SHA-256 + xxh3.
2. Stream once per file
   - Compare size ⟶ hash match
   - `gzip -t` for CRC
   - `tarfile` header walk (no extraction)
   - MySQL dump: check `-- MySQL dump` header & `-- Dump completed` footer
3. Edge-trigger: if hash mismatch/file missing → Discord Warning

## Log files

All in /opt/watchdog/logs/ (daily rotate):
- backup.log
- status.log
- pulse.log
- … plus per-class logs (SSHHandler, Verifier, …)

## License
MIT — free for personal & commercial use.
**Happy backing-up & monitoring!**
