import platform
import re
import subprocess
from utils import get_absolute_file_data_path, creation_flags

class Uniclip:
    def __init__(self):
        self.process = None
    def get_uniclip_executable_full_path(self):
        # Determine the system's architecture and platform
        arch = platform.machine()
        system = platform.system().lower()
        executable = 'uniclip-windows-x86_64.exe'
        # Select the appropriate executable
        if system == 'windows':
            if arch == 'x86_64':
                executable = 'uniclip-windows-x86_64.exe'
            elif arch == 'armv6l':
                executable = 'uniclip-windows-armv6.exe'
            elif arch == 'x86':
                executable = 'uniclip-windows-x86.exe'
        elif system == 'linux':
            if arch == 'x86_64':
                executable = 'uniclip-linux-x86_64'
            elif arch == 'armv6l':
                executable = 'uniclip-linux-armv6'
            elif arch == 'arm64':
                executable = 'uniclip-linux-arm64'
            elif arch == 'x86':
                executable = 'uniclip-linux-x86'
        elif system == 'darwin':  # macOS
            if arch == 'x86_64':
                executable = 'uniclip-macos-x86_64'
            elif arch == 'arm64':
                executable = 'uniclip-macos-arm64'
        return get_absolute_file_data_path('uniclip', executable)
    def start_server(self):
        if self.process:
            self.stop_server()
        self.process = subprocess.Popen([self.get_uniclip_executable_full_path(), '--secure'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)

        ip_port = ""
        while True:
            line = self.process.stdout.readline().decode('utf-8').strip()
            print(line)
            if line:
                match = re.search(r"uniclip (\d+\.\d+\.\d+\.\d+:\d+)", line)
                if match:
                    ip_port = match.group(1)
                    break
        return ip_port

    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def start_client(self, ip_port):
        if self.process:
            self.stop_client()
        self.process = subprocess.Popen([self.get_uniclip_executable_full_path(), '--secure', ip_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags)
        self.process.stdin.flush()
        print(self.get_output())
        self.process.stdin.write(b'lcs1234\n')
        self.process.stdin.flush()
        print(self.get_output())
        self.process.stdin.flush()

    def stop_client(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def get_output(self):
        if self.process:
            return self.process.stdout.readline().decode('utf-8').strip()
        return None