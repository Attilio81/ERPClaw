@echo off
cd /d "%~dp0"

:: Controlla se uv e' disponibile
where uv >nul 2>&1
if errorlevel 1 (
    echo uv non trovato. Installazione in corso...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo ERRORE: installazione uv fallita.
        pause
        exit /b 1
    )
    :: Aggiorna PATH per questa sessione
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

echo Installazione/aggiornamento dipendenze...
uv sync
if errorlevel 1 (
    echo ERRORE: uv sync fallito.
    pause
    exit /b 1
)

echo Avvio pannello web (admin + shop + chat)...
echo   Admin:  http://localhost:8000/admin
echo   Shop:   http://localhost:8000/shop/register
echo   Chat:   http://localhost:8000/chat
start "ERPClaw Web" cmd /k "uv run uvicorn erpclaw.web:app --reload"
timeout /t 2 /nobreak >nul

echo Avvio bot Telegram...
uv run erpclaw
