@echo off
REM Logitech Channel Switcher - Configure Devices
REM Run this script to set up your keyboard and mouse assignment

echo ======================================================================
echo  Logitech Channel Switcher - CONFIGURATION
echo ======================================================================
echo.

REM Check if config already exists
if exist "%USERPROFILE%\.lcs_config\config.json" (
    echo Configuration already exists at:
    echo %USERPROFILE%\.lcs_config\config.json
    echo.
    set /p RECONFIGURE="Do you want to reconfigure? (y/n): "
    
    if /i NOT "%RECONFIGURE%"=="y" (
        echo.
        echo Configuration unchanged. Exiting.
        pause
        exit /b 0
    )
    
    echo.
    del "%USERPROFILE%\.lcs_config\config.json"
    echo Old configuration deleted.
    echo.
)

REM Run configuration
python.exe "%~dp0..\cli_switcher.py" --channel 1

echo.
echo ======================================================================
if %ERRORLEVEL% EQU 0 (
    echo Configuration saved successfully!
    echo.
    echo You can now use the channel switcher shortcuts:
    echo   - switch-channel-1.bat
    echo   - switch-channel-2.bat
    echo   - switch-channel-3.bat
) else (
    echo Configuration failed! 
    echo Please check error messages above.
)
echo ======================================================================
pause
