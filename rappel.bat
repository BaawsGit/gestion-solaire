@echo off
echo ========================================= >> log_rappel.txt
echo EXECUTION: %date% %time% >> log_rappel.txt
echo ========================================= >> log_rappel.txt

cd /d "C:\Users\USER\PycharmProjects\solar_maintenance"
call .venv\Scripts\activate.bat
python manage.py envoyer_rappels >> log_rappel.txt 2>&1

echo FIN EXECUTION: %time% >> log_rappel.txt
echo. >> log_rappel.txt
pause