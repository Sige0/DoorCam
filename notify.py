import logging
import os
import smtplib
import ssl
import threading
import time
from datetime import datetime
from email.message import EmailMessage

CHECK_SECONDS = 0.5

log = logging.getLogger(__name__)


def send_mail(subject, text, jpeg=None):
    """Sends a mail with an optional JPEG. Raises an error if it fails."""
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    receivers = [address.strip() for address in os.getenv("MAIL_TO", "").split(",")
                 if address.strip()]
    if not host or not user or not receivers:
        raise ValueError("SMTP_HOST, SMTP_USER or MAIL_TO missing in .env")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = user
    message["To"] = ", ".join(receivers)
    message.set_content(text)
    if jpeg:
        message.add_attachment(jpeg, maintype="image", subtype="jpeg", filename="doorcam.jpg")

    # STARTTLS: connection is encrypted before the password is sent
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(user, password)
        smtp.send_message(message)


class Notifier:
    """Sends a mail with photo when motion starts while away mode is active."""

    def __init__(self, camera, motion, away):
        self.camera = camera
        self.motion = motion
        self.away = away
        self.cooldown = float(os.getenv("MAIL_COOLDOWN_MINUTES", "5")) * 60
        self.photo_delay = float(os.getenv("MAIL_PHOTO_DELAY_SECONDS", "1"))
        self.last_mail = 0
        self.was_active = False

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            active = self.motion.active
            if active and not self.was_active and self.away.is_active():
                self._alarm()
            self.was_active = active
            time.sleep(CHECK_SECONDS)

    def _alarm(self):
        now = time.time()
        if now - self.last_mail < self.cooldown:
            log.info("Motion while away, mail skipped (cooldown)")
            return

        self.last_mail = now
        time_text = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        # own thread, a slow or failing mail never stops camera or recording
        threading.Thread(target=self._send, args=(time_text,), daemon=True).start()

    def _send(self, time_text):
        # wait a moment, so the person is fully in the picture
        time.sleep(self.photo_delay)
        jpeg = self.camera.get_jpeg()

        subject = f"DoorCam: Bewegung am {time_text}"
        text = (f"Die DoorCam hat am {time_text} eine Bewegung erkannt, "
                "während der Abwesend-Modus aktiv war.\n\n"
                "Das Video findest du im Heimnetz unter http://doorcam.local:5000/recordings")
        try:
            send_mail(subject, text, jpeg)
            log.info("Alarm mail sent")
        except (smtplib.SMTPException, OSError, ValueError) as error:
            log.error("Alarm mail failed: %s", error)


if __name__ == "__main__":
    # quick test: sends a mail with a test image, does not open the camera
    import cv2
    import numpy as np
    from dotenv import load_dotenv

    load_dotenv(override=True)

    image = np.full((360, 640, 3), 60, dtype=np.uint8)
    cv2.putText(image, "DoorCam Test", (40, 190), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    jpeg = cv2.imencode(".jpg", image)[1].tobytes()

    try:
        send_mail("DoorCam Testmail", "Das ist eine Testmail von der DoorCam.", jpeg)
        print("Mail sent to", os.getenv("MAIL_TO"))
    except (smtplib.SMTPException, OSError, ValueError) as error:
        print("Mail failed:", error)
