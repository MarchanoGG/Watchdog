import paramiko
from watchdog.utils.logger import WatchdogLogger

class SSHHandler:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.logger = WatchdogLogger("backup")

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password
        )
        self.logger.info(f"Connected to {self.host} as {self.username}")

    def exec_sudo(self, command):
        full_cmd = f'echo "{self.password}" | sudo -S {command}'
        stdin, stdout, stderr = self.client.exec_command(full_cmd)
        exit_code = stdout.channel.recv_exit_status()
        self.logger.info(f"Executed command: {command} with exit code {exit_code}")
        return stdout.read().decode(), stderr.read().decode(), exit_code

    def exec(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        self.logger.info(f"Executed command: {command} with exit code {exit_code}")
        return stdout.read().decode(), stderr.read().decode(), exit_code

    def close(self):
        if self.client:
            self.client.close()