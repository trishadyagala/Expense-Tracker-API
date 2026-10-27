@echo off
cd /d "%~dp0"
echo Installing Flask (first time only)...
python -m pip install -r requirements.txt
echo.
echo Starting server at http://127.0.0.1:5000  (keep this window open, press Ctrl+C to stop)
echo.
python app.py
pause
