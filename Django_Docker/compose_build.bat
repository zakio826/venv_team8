@echo off
chcp 65001
docker --version
pause
echo Dockerfileからコンテナイメージを作成します。
docker compose build --no-cache
rem echo マイグレートします。
call :choiceYN return
if "%return%"=="y" (
    docker compose run --rm web python manage.py migrate
    docker compose down
)
call compose_up.bat
exit /b 0


:choiceYN
    setlocal

    choice /c YN /t 20 /d N /n /m "マイグレートしますか(Y/N)?: "
    if %errorlevel%==1 (
        set ret=y
    ) else (
        set ret=n
    )

    endlocal && set %1=%ret%
    exit /b