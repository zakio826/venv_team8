@echo off
chcp 65001

docker --version
pause

echo Dockerfileからコンテナイメージを作成します。
set repository=fki2266287
set image_name=tool-keeper-web
set tag=latest
docker build --no-cache ./ -t %image_name%
set error_message="コンテナイメージの作成に失敗しました。"
call :error_check error_message
echo コンテナイメージを作成しました。

call :choiceYN return
if "%return%"=="n" goto :finish
echo Docker Hubにログインします。
docker login -u %repository%
echo Docker Hubにログインしました。

echo コンテナイメージをpushします。
docker tag %image_name% %repository%/%image_name%:%tag%
docker push %repository%/%image_name%:%tag%
set error_message="コンテナイメージのpushに失敗しました。"
call :error_check error_message
echo コンテナイメージをpushしました。

echo Docker Hubからログアウトします。
docker logout
echo Docker Hubからログアウトしました。

:finish
echo コンテナイメージ一覧：
docker images
echo 終了します。
exit /b 0


:error_check
    if not errorlevel 0 (
        echo %1
        echo errorlevel: %errorlevel%
        goto :finish
    )
    exit /b


:choiceYN
    setlocal

    choice /c YN /t 20 /d N /n /m "Docker Hubにpushしますか(Y/N)?: "
    if errorlevel 1 (
        set ret=y
    ) else (
        set ret=n
    )

    endlocal && set %1=%ret%
    exit /b