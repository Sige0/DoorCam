import threading
import time
from datetime import datetime

import cv2
import numpy as np

WIDTH = 1280
HEIGHT = 720


class Camera:
    """Reads frames in a background thread, so only this process uses the camera."""

    def __init__(self, source):
        self.source = source
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def get_jpeg(self):
        frame = self.get_frame()
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes() if ok else None

    def _open(self):
        # PC: webcam index like "0", Pi: /dev/v4l/by-id/... path
        if self.source.isdigit():
            cap = cv2.VideoCapture(int(self.source))
        else:
            cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)

        # MJPEG, YUYV is too slow at 720p
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        return cap

    def _test_frame(self):
        img = np.full((HEIGHT, WIDTH, 3), 60, dtype=np.uint8)
        text = "TEST " + datetime.now().strftime("%H:%M:%S")
        cv2.putText(img, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        return img

    def _set_frame(self, frame):
        with self.lock:
            self.frame = frame

    def _loop(self):
        if self.source == "test":
            while True:
                self._set_frame(self._test_frame())
                time.sleep(0.1)

        cap = self._open()
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed, reconnecting...")
                cap.release()
                time.sleep(2)
                cap = self._open()
                continue
            self._set_frame(frame)


if __name__ == "__main__":
    # quick test: save one frame as snapshot.jpg
    import os
    from dotenv import load_dotenv

    load_dotenv()
    cam = Camera(os.getenv("CAMERA_SOURCE", "0"))
    cam.start()
    time.sleep(3)

    jpeg = cam.get_jpeg()
    if jpeg:
        with open("snapshot.jpg", "wb") as f:
            f.write(jpeg)
        print("Saved snapshot.jpg")
    else:
        print("No frame received")
