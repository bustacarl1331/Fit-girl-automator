@echo off
echo Building FitGirl Automator...
pyinstaller --noconsole --name "FitGirlAutomator" --onefile --clean --collect-all playwright gui.py
echo Build Complete! Check the 'dist' folder.
pause
