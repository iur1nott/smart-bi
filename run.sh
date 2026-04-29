clear

cd ~/Documents/smart-bi
source .venv/bin/activate

lsof -ti :8501 | xargs kill -9

streamlit run app.py
