import streamlit as st
from admin_tools import add_user, remove_user, change_password, load_users
from utils import logout_button
import pandas as pd
from configuration import HISTORICAL_DATA_PATH

# ==============================================================
#  Funzione riutilizzabile per mostrare un popup di conferma
# ==============================================================

def confirm_action(key, title, message, on_confirm):
    """
    Mostra un popup di conferma se st.session_state[key] è True.
    on_confirm: funzione da chiamare quando l'utente clicca "Confirm".
    """
    if st.session_state.get(key, False):
        @st.dialog(title)
        def _dlg():
            st.write(message)
            col1, col2 = st.columns(2)
            # Pulsante di conferma
            with col1:
                if st.button("✅ Confirm", key=f"{key}_ok"):
                    on_confirm()
                    st.session_state[key] = False  # rimuovo il flag
                    st.rerun()
            # Pulsante di annullamento
            with col2:
                if st.button("❌ Cancel", key=f"{key}_cancel"):
                    st.session_state[key] = False
                    st.rerun()
        _dlg()


# ==============================================================
#  Sezione autenticazione e controllo ruolo
# ==============================================================

logout_button()

# Controllo autenticazione
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("You must login to see this page.")
    st.stop()

# Controllo ruolo
if st.session_state.get("role") != "admin":
    st.error("❌ Access denied: only administrators can access this page.")
    st.stop()


# ==============================================================
#  Layout principale
# ==============================================================

st.title("👨‍💼 Users Management")

tab1, tab2, tab3 = st.tabs(["➕ Add User", "🗑 Remove User", "🔑 Change Password"])


# ==============================================================
# 1️⃣ Add New User
# ==============================================================

with tab1:
    st.subheader("Add New User")

    # 👉 Nota informativa per l'utente
    st.caption("Fields marked with * are required. Email is optional.")

    # Campi del form
    new_user = st.text_input("Username *")
    new_email = st.text_input("Email (optional)")
    new_pass = st.text_input("Password *", type="password")
    new_role = st.selectbox("User role *", ["user", "admin"], key="select_role")
    
    # Bottone che avvia il popup di conferma
    if st.button("Create user"):
        st.session_state["confirm_add_user"] = True

    # Funzione da eseguire dopo la conferma
    def do_add_user():
        ok, msg = add_user(new_user, new_pass, new_email, new_role)
        st.session_state["last_msg_add"] = msg

    confirm_action(
        key="confirm_add_user",
        title="➕ Confirm user creation",
        message=f"Do you want to create user **{new_user}** with role `{new_role}`?",
        on_confirm=do_add_user,
    )

    # Mostra eventuale messaggio dopo la conferma
    if "last_msg_add" in st.session_state:
        st.info(st.session_state.pop("last_msg_add"))


# ==============================================================
# 2️⃣ Remove User
# ==============================================================

with tab2:
    st.subheader("Remove Existing User")

    # Carico tutti gli utenti
    users_dict = load_users()
    all_users = list(users_dict.keys())

    user_to_remove = st.selectbox("Select user to remove", all_users, key="select_user_1")

    if st.button("Remove"):
        # --- LOGICA DI BLOCCO ---
        # Ottengo la lista di tutti gli admin
        admins = [u for u, data in users_dict.items() if data.get("role") == "admin"]

        # Caso: sto cercando di rimuovere l'ultimo admin rimasto
        if user_to_remove in admins and len(admins) == 1:
            st.error("❌ You cannot remove the only admin user.")
        else:
            # Se ok, avvio il popup di conferma
            st.session_state["confirm_remove_user"] = True

    # Funzione eseguita dopo la conferma
    def do_remove_user():
        ok, msg = remove_user(user_to_remove)
        st.session_state["last_msg_remove"] = msg

    confirm_action(
        key="confirm_remove_user",
        title="🗑 Confirm deletion",
        message=f"Are you sure you want to delete user **{user_to_remove}**?",
        on_confirm=do_remove_user,
    )

    if "last_msg_remove" in st.session_state:
        st.warning(st.session_state.pop("last_msg_remove"))


# ==============================================================
# 3️⃣ Change Password
# ==============================================================

with tab3:
    st.subheader("Change Password")

    target_user = st.selectbox("Select user", list(load_users().keys()), key="select_user_2")
    new_pass = st.text_input("New password", type="password")

    if st.button("Update password"):
        st.session_state["confirm_change_pw"] = True

    def do_change_pw():
        ok, msg = change_password(target_user, new_pass)
        st.session_state["last_msg_pw"] = msg

    confirm_action(
        key="confirm_change_pw",
        title="🔑 Confirm password change",
        message=f"Change password for **{target_user}**?",
        on_confirm=do_change_pw,
    )

    if "last_msg_pw" in st.session_state:
        st.success(st.session_state.pop("last_msg_pw"))


# ==============================================================
# 4️⃣ Aggiornamento CSV storico
# ==============================================================

st.divider()
st.title("📄 Update historical data CSV")

uploaded_csv_file = st.file_uploader(
    "Upload the new historical data CSV file",
    type=["csv"],
    key="csv_file_upload",
)

if uploaded_csv_file is not None:
    if st.button("Overwrite old CSV with new CSV"):
        st.session_state["confirm_update_csv"] = True

    def do_update_csv():
        new_data = pd.read_csv(uploaded_csv_file)
        new_data.to_csv(HISTORICAL_DATA_PATH, index=False)
        st.session_state["last_msg_csv"] = "Historical data CSV successfully updated ✅"

    confirm_action(
        key="confirm_update_csv",
        title="📄 Confirm CSV update",
        message="Are you sure you want to overwrite the historical CSV with the new one?",
        on_confirm=do_update_csv,
    )

    if "last_msg_csv" in st.session_state:
        st.success(st.session_state.pop("last_msg_csv"))
