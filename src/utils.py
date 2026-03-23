import os
import sys
import subprocess
import platform

def get_absolute_folder_data_path(folder_name):
    uniclip_folder = None
    if getattr(sys, 'frozen', False):
        uniclip_folder = os.path.join(sys._MEIPASS, 'static', folder_name)
    else:
        uniclip_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', folder_name)
    return uniclip_folder

def get_absolute_file_data_path(folder_name, file_name):
    return os.path.join(get_absolute_folder_data_path(folder_name), file_name)

# Platform detection
system = platform.system().lower()
machine = platform.machine()

def is_windows():
    """Check if running on Windows."""
    return system == 'windows'

def is_mac():
    """Check if running on macOS."""
    return system == 'darwin'

def is_linux():
    """Check if running on Linux."""
    return system == 'linux'

# Windows subprocess flag to suppress console windows
creation_flags = 0
if is_windows():
    creation_flags = subprocess.CREATE_NO_WINDOW


def get_platform_executable(binary_base, folder, extensions=None):
    """Get platform-specific executable path with automatic architecture detection.
    
    Generic helper for resolving platform-specific binaries like hidapitester, uniclip, etc.
    
    Args:
        binary_base: Base name of binary (e.g., 'hidapitester', 'uniclip')
        folder: Folder name in static/ directory
        extensions: Dict mapping platform to extension (default: .exe for Windows, none for others)
        
    Returns:
        Full path to platform-specific executable
        
    Example:
        get_platform_executable('uniclip', 'uniclip')
        # Returns: .../static/uniclip/uniclip-windows-x86_64.exe (on Windows x64)
    """
    if extensions is None:
        extensions = {'windows': '.exe', 'darwin': '', 'linux': ''}
    
    ext = extensions.get(system, '')
    
    # Platform-specific naming
    if system == 'windows':
        # Windows: typically x86_64 only
        filename = f'{binary_base}-windows-x86_64{ext}'
    elif system == 'darwin':
        # macOS: arm64 or x86_64
        arch = 'arm64' if machine == 'arm64' else 'x86_64'
        filename = f'{binary_base}-macos-{arch}{ext}'
    else:  # linux
        # Linux: x86_64, armv7l, armv6, arm64, x86
        if machine == 'armv7l':
            arch = 'armv7l'
        elif machine == 'armv6l':
            arch = 'armv6'
        elif machine == 'aarch64':
            arch = 'arm64'
        elif machine in ('i386', 'i686'):
            arch = 'x86'
        else:
            arch = 'x86_64'
        filename = f'{binary_base}-linux-{arch}{ext}'
    
    return get_absolute_file_data_path(folder, filename)