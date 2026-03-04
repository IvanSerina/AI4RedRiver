import bcrypt
import yaml
import os
from datetime import datetime

from configuration import USERS_FILE

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        data = yaml.safe_load(f)
    if not data or "users" not in data:
        return {}
    return data["users"]

def save_users(users):
    with open(USERS_FILE, "w") as f:
        yaml.safe_dump({"users": users}, f, sort_keys=False)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def add_user(username, password, email, role="user"):
    users = load_users()
    if username in users:
        return False, "⚠️ User already existing."
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    save_users(users)
    return True, f"✅ User {username} succesfully added."

def remove_user(username):
    users = load_users()
    if username not in users:
        return False, "⚠️ User not found."
    del users[username]
    save_users(users)
    return True, f"🗑 Utente {username} succesfully removed."

def change_password(username, new_password):
    users = load_users()
    if username not in users:
        return False, "⚠️ User not found."
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True, f"🔑 {username}'s password updated."
