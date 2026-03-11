#!/bin/bash
# Launch script for Dashboard Builder Streamlit Application

cd ~/Documents/smart-bi/

# Activate virtual environment
source .venv/bin/activate

lsof -t -i :8501 | xargs kill -9

clear
# Run Streamlit application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
