import subprocess
import time
import urllib.request

URL = "http://127.0.0.1:5000"

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
    "--disable-pinch",  # no zooming on the touch screen
    "--overscroll-history-navigation=0",  # no swipe back
    URL + "/display",
])
