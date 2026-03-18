@echo off
cd C:\Projects\Mona
git push
echo.
echo Deploying to server...
ssh sshuser@10.7.6.146 "C:\Mona\deploy.bat"
