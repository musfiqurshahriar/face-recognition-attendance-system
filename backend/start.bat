@echo off
echo Starting Face Attendance System...
echo.

start "Flask Server" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python app.py"

timeout /t 3 /nobreak > nul

echo.
echo Local Access:    http://localhost:5000
echo.
echo For global access, run in another terminal:
echo ngrok http 5000
echo.
pause