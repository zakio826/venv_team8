@echo off
chcp 65001

docker --version
call :choiceYN return
if "%return%"=="n" goto :finish

echo アプリを終了するには、Enterを入力してください。
rem timeout /t 2 /nobreak > nul 2>&1
start /b docker compose up

timeout /t 10 /nobreak > nul 2>&1
start "" http://localhost:8088/admin
start "" http://localhost:8088

pause > nul
docker compose down

:finish
echo 終了します。

exit /b 0


:choiceYN
    setlocal

    choice /c YN /t 20 /d N /n /m "アプリを開始しますか(Y/N)?: "
    if %errorlevel%==1 (
        set ret=y
    ) else (
        set ret=n
    )

    endlocal && set %1=%ret%
    exit /b