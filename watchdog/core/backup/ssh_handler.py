import paramiko

class SSHHandler:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password
        )

    def exec_sudo(self, command):
        full_cmd = f'echo "{self.password}" | sudo -S {command}'
        stdin, stdout, stderr = self.client.exec_command(full_cmd)
        return stdout.read().decode(), stderr.read().decode()

    def close(self):
        if self.client:
            self.client.close()