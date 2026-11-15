# KI-Nutzung

Verwendetes Werkzeug: Claude Code (Claude Opus 5.5) in VS Code

| Datum | Was ich gefragt habe (Prompt kurz) | Was die KI gemacht hat | Was ich selbst angepasst habe |
|---|---|---|---|
| 12.11.2026 | Projektkontext gegeben, gefragt welche Dateien ich erstellen soll und welcher Code | Plan für KW46 erstellt, Inhalt für .gitignore, requirements.txt und .env.example vorgeschlagen | |
| 12.11.2026 | Nächster Schritt: Kamera | Code für camera.py (Kamera-Thread, Testbild, Reconnect) vorgeschlagen und erklärt | |
| 12.11.2026 | Fehler "No module named cv2" | Ursache erklärt (Pakete nicht in .venv installiert), Befehle zur Behebung gezeigt | |
| 12.11.2026 | Nächster Schritt: Livestream | Code für app.py (MJPEG-Stream), templates/index.html und static/style.css vorgeschlagen und erklärt | |
| 12.11.2026 | Nächster Schritt: Login | Fehler gefunden (static-Ordner am falschen Ort), Code für auth.py, login.html, Anpassungen app.py/CSS vorgeschlagen, Befehle für SECRET_KEY und Passwort-Hash gezeigt | |
| 12.11.2026 | Pushen | snapshot.jpg aus Git entfernt und in .gitignore ergänzt, Commit und Push ausgeführt | |
| 13.11.2026 | Repo anschauen und nächste Schritte vorschlagen | Stand analysiert, Fehler gefunden (CSS-Regeln beim Verschieben verloren, kein Logout-Link, HOST fehlt in .env.example), Plan für KW47 vorgeschlagen | |
| 13.11.2026 | Gefundene Fehler beheben, Design verbessern, Sicherheit prüfen | style.css neu gestaltet (dunkel, passt sich der Bildschirmgrösse an), Kopfzeile mit Logout in index.html, login.html angepasst, HOST in .env.example, Logout nur noch per POST, 1 s Wartezeit bei falschem Login, Sicherheits-Header in app.py | |
| 13.11.2026 | Problems in VS Code, Einrichtung am Laptop, Fehler beim Erstellen der .env | Ursachen erklärt (kein .venv, Execution Policy, Werte ins Terminal statt in .env eingefügt), setup_env.py geschrieben (erzeugt SECRET_KEY und Passwort-Hash), load_dotenv(override=True) in app.py | |
| 15.11.2026 | Gelöschte Dateien wiederherstellen | Befehle gezeigt, um .env.example und ki-nutzung.md aus altem Commit zurückzuholen | |
| 15.11.2026 | Pi: "No module named dotenv", Zugriff über Hostname, Autostart | Ursache erklärt (keine .venv auf dem Pi), mDNS/doorcam.local erklärt, Code für doorcam.service, kiosk.py, Kiosk-Autostart und "Angemeldet bleiben" vorgeschlagen und erklärt | |
| 15.11.2026 | doorcam.service nicht gefunden | Ursache erklärt (Dateien nie committet, ki-nutzung.md mitgelöscht), Dateien aus der Anleitung erstellt (deploy/, kiosk.py, Remember-Me), ki-nutzung.md wiederhergestellt, Commit und Push | |
| 15.11.2026 | Display ohne Login, nur Bild, für 5"-Bildschirm optimieren | Plan vorgeschlagen, /display und /display/stream (nur vom Pi selbst erreichbar) in app.py, display.html, display.css, kiosk.py öffnet /display, getestet (lokal 200, aus dem Netz 403) | |
