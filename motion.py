import logging
import os
import threading
import time

import cv2

CHECK_FPS = 5  # frames checked per second
SMALL_SIZE = (320, 180)
BACKGROUND_SPEED = 0.02  # how fast the background adapts (~10 s)
LIGHT_COOLDOWN = 2  # seconds without detection after light change

log = logging.getLogger(__name__)


class MotionDetector:
    """Checks camera frames for motion in a background thread."""

    def __init__(self, camera):
        self.camera = camera
        self.threshold = int(os.getenv("MOTION_THRESHOLD", "25"))
        self.min_area = float(os.getenv("MOTION_MIN_AREA", "1.0"))
        self.light_change = float(os.getenv("MOTION_LIGHT_CHANGE", "60"))
        self.end_seconds = float(os.getenv("MOTION_END_SECONDS", "5"))

        self.active = False  # True while a motion event is running
        self.background = None
        self.ignore_until = 0
        self.last_motion = 0
        self.event_start = 0
        self.max_area = 0

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            frame = self.camera.get_frame()
            if frame is not None:
                area = self._measure(frame)
                self._update_event(area)
            time.sleep(1 / CHECK_FPS)

    def _measure(self, frame):
        """Returns the size of the biggest moving area in % of the image."""
        small = cv2.resize(frame, SMALL_SIZE)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.background is None:
            self.background = gray.astype("float")
            return 0

        diff = cv2.absdiff(gray, cv2.convertScaleAbs(self.background))
        mask = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
        mask = cv2.dilate(mask, None, iterations=2)  # close small gaps
        changed = cv2.countNonZero(mask) / mask.size * 100

        # almost whole image changed = light on/off, not motion
        now = time.time()
        if changed > self.light_change:
            if now > self.ignore_until:
                log.info("Light change ignored (%.0f %% changed)", changed)
            self.ignore_until = now + LIGHT_COOLDOWN

        # relearn background while camera adjusts exposure
        if now < self.ignore_until:
            self.background = gray.astype("float")
            return 0

        cv2.accumulateWeighted(gray, self.background, BACKGROUND_SPEED)

        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        biggest = max((cv2.contourArea(c) for c in contours), default=0)
        return biggest / mask.size * 100

    def _update_event(self, area):
        now = time.time()

        if area >= self.min_area:
            self.last_motion = now
            if not self.active:
                self.active = True
                self.event_start = now
                self.max_area = 0
                log.info("Motion started (area %.1f %%)", area)
            self.max_area = max(self.max_area, area)

        elif self.active and now - self.last_motion > self.end_seconds:
            self.active = False
            duration = now - self.event_start
            log.info("Motion ended (%.0f s, max area %.1f %%)", duration, self.max_area)


if __name__ == "__main__":
    # quick test: print motion events to the console
    from dotenv import load_dotenv

    from camera import Camera

    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    cam = Camera(os.getenv("CAMERA_SOURCE", "0"))
    cam.start()
    MotionDetector(cam).start()
    print("Watching for motion, stop with Ctrl+C")

    while True:
        time.sleep(1)
