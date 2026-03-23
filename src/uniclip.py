import re
import subprocess
from utils import get_platform_executable, creation_flags
from settings import config

class Uniclip:
    def __init__(self):
        # Separate process fields for server and client
        self.server_process = None
        self.client_process = None

    def get_uniclip_executable_full_path(self):
        """Get platform-specific uniclip binary path."""
        return get_platform_executable('uniclip', 'uniclip')

    def start_server(self):
        if self.server_process:
            self.stop_server()

        self.server_process = subprocess.Popen(
            [self.get_uniclip_executable_full_path(), '--secure'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=creation_flags
        )

        # Limit readline attempts to prevent infinite blocking
        ip_port = ""
        max_lines = 50
        for _ in range(max_lines):
            if self.server_process.poll() is not None:
                break
            line = self.server_process.stdout.readline().decode('utf-8').strip()
            if line:
                match = re.search(r"uniclip (\d+\.\d+\.\d+\.\d+:\d+)", line)
                if match:
                    ip_port = match.group(1)
                    break
        return ip_port

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

    def start_client(self, ip_port):
        if self.client_process:
            self.stop_client()
        self.client_process = subprocess.Popen(
            [self.get_uniclip_executable_full_path(), '--secure', ip_port],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=creation_flags
        )
        self.client_process.stdin.flush()
        self._get_client_output()
        # Use password from config instead of hardcoded value
        password = config.UNICLIP_PASSWORD
        self.client_process.stdin.write(f'{password}\n'.encode('utf-8'))
        self.client_process.stdin.flush()
        self._get_client_output()
        self.client_process.stdin.flush()

    def stop_client(self):
        if self.client_process:
            self.client_process.terminate()
            self.client_process = None

    def stop_all(self):
        self.stop_server()
        self.stop_client()

    def _get_client_output(self):
        if self.client_process:
            return self.client_process.stdout.readline().decode('utf-8').strip()
        return None
