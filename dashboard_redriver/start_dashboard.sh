#!/bin/bash
# Vai nella cartella del progetto
cd "$(dirname "$0")/dashboard_redriver"
# Attiva l'ambiente virtuale
source venv/bin/activate
# Avvia Streamlit
streamlit run app.py
