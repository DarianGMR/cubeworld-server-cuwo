#!/usr/bin/env bash

# Inicia el servidor cuwo (y la interfaz web como script)

cd "$(dirname "$0")"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

# Ejecutar servidor cuwo
python3 -m cuwo.server