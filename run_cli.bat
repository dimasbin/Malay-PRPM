@echo off
chcp 65001 >nul
cd /d "%~dp0"
python prpm_cli.py %*
if "%~1"=="" pause
