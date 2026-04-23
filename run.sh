clear

lsof -ti :8501 | xargs kill -9

streamlit run app.py
