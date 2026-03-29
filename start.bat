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
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

echo Installazione/aggiornamento dipendenze...
uv sync
if errorlevel 1 (
    echo AVVISO: uv sync fallito. Le dipendenze esistenti verranno usate.
)

echo Avvio pannello web...
start "ERPClaw Web" cmd /k "cd /d %~dp0 && uv run uvicorn erpclaw.web:app --reload"

:: Attendi che FastAPI sia pronto prima di avviare il frontend
echo Attendo avvio backend (5s)...
timeout /t 5 /nobreak >nul

:: Avvia frontend React in dev (installa npm se necessario)
if exist "frontend\package.json" (
    if not exist "frontend\node_modules\" (
        echo Installazione dipendenze frontend...
        cd /d "%~dp0frontend"
        npm install
        cd /d "%~dp0"
    )
    echo Avvio frontend React...
    start "ERPClaw Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
)

echo.
echo   React SPA: http://localhost:5173/         (Home, Dashboard, Config, Chat)
echo   Admin:     http://localhost:8000/admin
echo   Shop:      http://localhost:8000/shop/register
echo.

echo Avvio bot Telegram...
uv run erpclaw

echo.
echo Bot terminato. Premi un tasto per chiudere.
pause
