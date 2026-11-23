# DoorCam – Kontext für Claude

## Projekt

Vertiefungsarbeit (VA) von Siro Cahenzli, ICT-Fachmann EFZ (Systemtechnik), TBZ, Klasse ICT24d. Unsere Wohnungstür hat weder Guckloch noch Kamera, darum baue ich mit einem Raspberry Pi eine eigene Türkamera. Die VA ist ein Werk mit Begleitdokumentation. Abgabe am 17.12.2026.

## Funktionen (laut verbindlichem Projektbeschrieb)

- Bei Bewegung zeigt ein kleiner Bildschirm in der Wohnung das Kamerabild
- Aufnahmen bleiben 24 Stunden gespeichert und sind über eine lokale Website abrufbar, danach werden sie automatisch gelöscht
- Abwesend-Modus (wird manuell aktiviert): Bei Bewegung kommt eine E-Mail mit Foto
- Die Daten bleiben lokal, es gibt keine Cloud
- Die Website hat einen Login

## Entscheidungen zu den Aufnahmen (23.11.2026)

- Aufnahme bei Bewegung: 5 s Vorlauf (vor der Bewegung) und 5 s Nachlauf (nach der letzten Bewegung)
- Website: Aufnahmen als Galerie, Videos können heruntergeladen werden
- Manueller Clip: Auf dem Display und auf der Website kann man per Knopf die letzten 30 s speichern

## Hardware

- Raspberry Pi 5, Raspberry Pi OS 64-bit mit Desktop, Hostname `doorcam`
- Kamera: Logitech C270 (USB, 720p)
  - Immer den Pfad unter `/dev/v4l/by-id/...-video-index0` verwenden, nie `/dev/video0` (der Pi 5 hat viele eigene Video-Geräte)
  - Format MJPEG mit 1280x720, YUYV ist bei 720p zu langsam
- Display: Raspberry Pi Touch Display 2, 5", auf Querformat gedreht
- Bewegungserkennung per Software (OpenCV), kein PIR-Sensor

## Technik

- Python 3, Flask (Website), OpenCV (Kamera, Bewegung), Flask-Login (Login)
- Passwörter nur als Hash (`werkzeug.security`)
- Geheimnisse (Login, SMTP, SECRET_KEY) in `.env`, geladen mit python-dotenv (`override=True`). Nie ins Repo, im Repo liegt nur `.env.example`. `setup_env.py` erzeugt SECRET_KEY und Passwort-Hash
- Nur ein Prozess öffnet die Kamera. Die Flask-App liest die Bilder in einem eigenen Thread und verteilt sie. Das Display zeigt die Website im Kiosk-Modus von Chromium (mit Login, funktioniert) und öffnet die Kamera nicht selbst
- Website nur im lokalen Netz. Keine Portweiterleitung, kein Zugriff von aussen
- Kein Ton aufnehmen, Mikrofon der C270 wird nicht verwendet (rechtliche Gründe)
- Entwickelt auf dem Windows-PC/Laptop in VS Code, läuft auf dem Pi (`git pull`)
  - Am Laptop gibt es `python` nur im `.venv` (sonst nur `py`)
  - Am PC gibt es keine C270: `CAMERA_SOURCE` in `.env` (`0` = Webcam, `test` = Testbild)
- Später läuft die App als systemd-Dienst

## Code-Stil

- Einfacher, gut lesbarer Code auf dem Niveau eines Lernenden, keine unnötigen Abstraktionen
- Kommentare und Log-Meldungen auf Englisch und sehr kurz. Texte für Benutzer (Website) auf Deutsch
- Imports in drei Gruppen (Standardbibliothek, Fremdpakete, eigene Module), alphabetisch
- Doppelte Anführungszeichen, Konstanten gross, interne Methoden mit `_`
- Klassen nur wo Zustand nötig ist (z.B. `Camera`), Hintergrundarbeit als Thread mit `start()`
- Einstellungen mit `os.getenv(...)` und Standardwert, jede Einstellung auch in `.env.example`
- Modul-Test unten mit `if __name__ == "__main__":`

## Struktur

```text
app.py            # Flask-App, Routen
camera.py         # Kamera-Thread, liefert das aktuelle Bild
auth.py           # Login
motion.py         # Bewegungserkennung (KW47)
recorder.py       # Aufnahmen (KW47), Löschen nach 24h (KW48)
notify.py         # E-Mail im Abwesend-Modus (KW48)
setup_env.py      # erzeugt .env
templates/        # HTML
static/           # CSS
```

## Zeitplan

- [x] KW45: Pi eingerichtet, Kamera und Display angeschlossen, SSH läuft
- [x] KW46: Livebild als MJPEG-Stream, Website mit Login, auf dem Pi getestet
- [ ] KW47: Bewegungserkennung und Aufnahme
- [ ] KW48: Abwesend-Modus mit E-Mail, Aufnahmen nach 24h automatisch löschen
- [ ] KW49: Testen und Fehler beheben (2. Zwischengespräch am 3.12.)
- [ ] KW50/51: Dokumentation, Abgabe am 17.12.2026

## So sollst du mich unterstützen (wichtig!)

Das ist eine Schularbeit. Laut VA-Leitfaden ist KI erlaubt, aber nur als Werkzeug und nicht als Ghostwriter. Jede Nutzung muss deklariert werden. Im Prüfungsgespräch muss ich jede Zeile erklären können.

- Kleine Schritte. Pro Schritt eine Funktion oder ein Feature. Nach jedem Schritt stoppen und auf mein OK warten
- Vor grösseren Änderungen kurz sagen, was du vorhast und warum. Dann warten, bis ich einverstanden bin
- Jede Änderung kurz erklären, auf Deutsch und so, dass ich sie im Prüfungsgespräch selbst erklären kann
- Fehler nicht einfach selbst fixen, wenn ich frage, warum etwas nicht geht. Zuerst die Ursache erklären
- Keine Texte für die Begleitdokumentation oder das Arbeitsprotokoll schreiben. Korrigieren und Feedback geben ist ok
- Kein KI-Protokoll im Repo führen. Das schreibe ich am Schluss selbst
- Nie selbst committen oder pushen. Ich pushe alles selbst. Am Ende jedes Schritts sagen, wie ich pushe (Befehle und Commit-Message, ohne Co-Authored-By oder andere KI-Hinweise)
- Auf Sicherheitsprobleme hinweisen (z.B. offener Stream ohne Login, Passwörter im Code)
