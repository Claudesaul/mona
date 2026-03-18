@echo off
set GIT="C:\Users\MonumentalReporting\AppData\Local\Programs\Git\cmd\git.exe"
set PYTHON=C:\Monumator\venv\Scripts\python.exe

cd C:\Mona
echo Pulling latest from GitHub...
%GIT% pull origin master
if errorlevel 1 (
    echo Pull failed!
    exit /b 1
)

echo Restarting Mona...
schtasks /end /tn "Mona AI" 2>nul
timeout /t 3 /nobreak >nul
schtasks /run /tn "Mona AI"
echo Deploy complete.
