#!/bin/bash
# Launch script for Dashboard Builder Streamlit Application
clear

# Garante que os comandos serão executados na pasta onde ESSE script estiver
# Coloque-o na raiz do projeto
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

lsof -t -i :8501 | xargs kill -9

# Run Streamlit application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
