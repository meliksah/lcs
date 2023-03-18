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

system = platform.system().lower()
creation_flags = 0
if system == 'windows':  # Check if the current OS is Windows
    creation_flags = subprocess.CREATE_NO_WINDOW