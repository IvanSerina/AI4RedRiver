import streamlit as st

# Config pagina principale 
st.set_page_config(page_title="", page_icon="")

# ----------------------------
# Inizializzazione session_state
# ----------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["role"] = None

# Se non autenticato → manda a Login 
if not st.session_state["authenticated"]: 
    st.switch_page("pages/1_LOGIN.py") 
else: 
    # Se autenticato → manda alla Home 
    st.switch_page("pages/2_HOME.py")