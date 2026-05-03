#!/bin/bash
# Launch script for Dashboard Builder Streamlit Application

# Limpa o terminal
clear

# Garante que os comandos serão executados na pasta onde ESSE script estiver
# Mantenha-o na raiz do projeto
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

# Ativa o ambiente virtual
source .venv/bin/activate

# Remove processos que estejam obstruindo a porta
lsof -t -i :8501 | xargs kill -9

# Roda a aplicação Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
