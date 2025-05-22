chcp 65001
.venv\Scripts\activate.bat
python start.py
IF %ERRORLEVEL% NEQ 0 echo Python script failed with an error.
pause