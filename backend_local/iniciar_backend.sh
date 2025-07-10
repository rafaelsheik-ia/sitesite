#!/bin/bash

echo "========================================"
echo "INFLUENCIANDO - Iniciando Backend Local"
echo "========================================"
echo

echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    echo "Instale Python3:"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "Mac: brew install python3"
    exit 1
fi

python3 --version

echo
echo "Instalando dependências..."
pip3 install -r requirements.txt

echo
echo "Inicializando banco de dados..."
python3 init_db.py
python3 init_config.py

echo
echo "========================================"
echo "BACKEND INICIANDO..."
echo "========================================"
echo
echo "Mantenha este terminal aberto!"
echo "Para parar o servidor: Ctrl+C"
echo

python3 src/main.py

