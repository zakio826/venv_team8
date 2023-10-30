@echo off
chcp 65001
docker --version
call :choiceYN return
if "%return%"=="n" goto :finish
rem docker compose up -d
rem start "" http://127.0.0.1:8000/
docker compose run web python manage.py runserver
set /p input="アプリを終了するには、Enterを入力してください: "
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