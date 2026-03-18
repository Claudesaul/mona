@echo off
set GIT="C:\Users\MonumentalReporting\AppData\Local\Programs\Git\cmd\git.exe"
cd C:\Mona

%GIT% fetch origin master >nul 2>&1
for /f %%i in ('%GIT% rev-parse HEAD') do set LOCAL=%%i
for /f %%i in ('%GIT% rev-parse origin/master') do set REMOTE=%%i

if not "%LOCAL%"=="%REMOTE%" (
    echo New commits found, deploying...
    %GIT% pull origin master
    schtasks /end /tn "Mona AI" 2>nul
    timeout /t 3 /nobreak >nul
    schtasks /run /tn "Mona AI"
    echo Deploy complete.
)
