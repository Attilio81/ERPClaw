@echo off
cd /d "%~dp0"

echo ⚠️  Questo script CANCELLA e rigenera erp.db e agent.db
echo.
set /p confirm=Sei sicuro? (s/N):
if /i not "%confirm%"=="s" (
    echo Operazione annullata.
    pause
    exit /b 0
)

echo.
echo Eliminazione database...
if exist erp.db del erp.db && echo   erp.db eliminato.
if exist agent.db del agent.db && echo   agent.db eliminato.

echo.
echo Rigenerazione erp.db...
uv run --no-sync python -c "from erpclaw.erp_db import init_db; init_db(); print('  erp.db rigenerato.')"
if errorlevel 1 (
    echo ERRORE: rigenerazione erp.db fallita.
    pause
    exit /b 1
)

echo.
echo ✅ Database rigenerati con successo.
pause
