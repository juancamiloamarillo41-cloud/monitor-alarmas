@echo off
rem Monitor de Alarmas: levanta backend y frontend y abre la pagina.
rem Doble clic para iniciar. Para detenerlo, cierra las dos ventanas que abre.

cd /d "%~dp0"

rem --- Primera vez: instala lo que falte -----------------------------------
if not exist "backend\.venv\Scripts\python.exe" (
    echo Creando el entorno de Python e instalando dependencias...
    python -m venv "backend\.venv" || goto :error
    "backend\.venv\Scripts\python" -m pip install -q -r "backend\requirements.txt" || goto :error
)
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul
if not exist "frontend\node_modules" (
    echo Instalando dependencias del frontend...
    pushd frontend
    call npm install || goto :error
    popd
)
if not exist "frontend\.env" copy "frontend\.env.example" "frontend\.env" >nul

rem --- Arranque -------------------------------------------------------------
start "Backend - API de Alarmas (puerto 8000)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python -m uvicorn app.main:app --reload"
start "Frontend - Monitor de Alarmas (puerto 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Iniciando servidores...
timeout /t 6 /nobreak >nul
start "" http://localhost:5173
exit /b 0

:error
echo.
echo No se pudo completar la instalacion. Revisa que Python 3.12+ y Node.js 20+ esten instalados.
pause
exit /b 1
