@echo off
echo ========================================
echo INFLUENCIANDO - Iniciando Backend Local
echo ========================================
echo.

echo Verificando Python...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python em: https://python.org
    pause
    exit
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Inicializando banco de dados...
python init_db.py
python init_config.py

echo.
echo ========================================
echo BACKEND INICIANDO...
echo ========================================
echo.
echo Mantenha esta janela aberta!
echo Para parar o servidor: Ctrl+C
echo.

python src/main.py

pause

