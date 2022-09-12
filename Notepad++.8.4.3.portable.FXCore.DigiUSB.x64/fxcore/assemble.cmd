@echo off
"%~dp0FXCoreCmdAsm.exe" %1 %2 %3 %4 %5
if %errorlevel% EQU 0 (echo. & echo NO ERRORS ) Else ( echo. & echo ERROR FAILED &color CF )
pause