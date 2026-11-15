import subprocess
import time
import urllib.request

URL = "http://localhost:5000"

# wait until the web app is up
while True:
    try:
        urllib.request.urlopen(URL + "/login", timeout=2)
        break
    except OSError:
        time.sleep(2)

subprocess.run([
    "chromium",
    "--kiosk",
    "--noerrdialogs",
    "--disable-infobars",
    "--no-first-run",
    URL,
])
