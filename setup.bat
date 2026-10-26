@echo off
where py >nul 2>nul && (py -3 setup.py & exit /b %errorlevel%)
where python >nul 2>nul && (python setup.py & exit /b %errorlevel%)
echo Python 3.11 oder neuer wurde nicht gefunden.
exit /b 1
