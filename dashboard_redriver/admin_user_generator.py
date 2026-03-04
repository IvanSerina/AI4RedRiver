import os
import yaml
from admin_tools import add_user
from configuration import USERS_FILE

new_user = "admin"
new_email = ""
new_pass = "Redriver2025@"
new_role = "admin"

# Se non esiste, lo crea vuoto
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        yaml.dump({}, f)

ok, msg = add_user(new_user, new_pass, new_email, new_role)

print(msg)