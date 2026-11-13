"""Creates .env with a new SECRET_KEY and password hash."""
import getpass
import os
import secrets

from werkzeug.security import generate_password_hash

# keep existing settings (HOST, CAMERA_SOURCE) if .env already exists
template = ".env" if os.path.exists(".env") else ".env.example"
with open(template, encoding="utf-8") as f:
    lines = f.read().splitlines()

password = getpass.getpass("Neues Passwort: ")
if len(password) < 8:
    raise SystemExit("Passwort zu kurz (mindestens 8 Zeichen)")
if getpass.getpass("Passwort wiederholen: ") != password:
    raise SystemExit("Passwörter stimmen nicht überein")

new_values = {
    "SECRET_KEY": secrets.token_hex(32),
    "LOGIN_PASSWORD_HASH": "'" + generate_password_hash(password) + "'",  # quotes because of $
}

for i, line in enumerate(lines):
    key = line.split("=")[0].strip()
    if key in new_values:
        lines[i] = key + "=" + new_values[key]

with open(".env", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(".env gespeichert. Jetzt mit 'python app.py' starten.")
