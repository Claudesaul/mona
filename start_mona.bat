@echo off
cd C:\Mona\backend
C:\Mona\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 3000
