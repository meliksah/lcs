@echo off
REM Logitech Channel Switcher - Switch to Channel 2
REM 
REM FIRST-TIME USERS: This will auto-configure on first run!
REM (Or run "configure.bat" for manual/interactive setup)
REM 
REM This script uses pythonw.exe to run silently without a console window.
REM To create a keyboard shortcut: Right-click this file > Create Shortcut > 
REM Right-click the shortcut > Properties > Shortcut key > Set your key combo

pythonw.exe "%~dp0..\cli_switcher.py" --channel 2 --quiet
