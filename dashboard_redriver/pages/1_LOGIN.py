import streamlit as st
import yaml
import bcrypt
import time

from configuration import USERS_FILE
from utils import logout_button

# ----------------------------
# Config pagina
# ----------------------------
st.set_page_config(page_title="Login Page", page_icon="🔐")
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
# ----------------------------
# Redirect se già autenticato
# ----------------------------
if st.session_state["authenticated"]:
    st.switch_page("pages/2_HOME.py")

# ----------------------------
# Funzioni di supporto
# ----------------------------
def load_users():
    with open(USERS_FILE, "r") as f:
        data = yaml.safe_load(f)
    return data["users"]

def check_password(username, password, users):
    if username in users:
        stored_hash = users[username]["password"].encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
    return False

# ----------------------------
# UI login
# ----------------------------
logout_button()
st.title("🔐 Login Page")

users = load_users()

with st.form("login_form", clear_on_submit=False):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # questo bottone si può attivare anche con Invio
    submit = st.form_submit_button("Login")

if submit:
    if check_password(username, password, users):
        st.session_state["authenticated"] = True
        st.session_state["user"] = username
        st.session_state["role"] = users[username]["role"]
        st.success(f"Welcome {username}!")
        time.sleep(1.5)
        st.switch_page("pages/2_HOME.py")
    else:
        st.error("Invalid username or password")
