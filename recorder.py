import logging
import os
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from datetime import datetime
from functools import lru_cache

import cv2

RECORD_FPS = 15
RECORDINGS_DIR = "recordings"
TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
FILE_NAME = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_manual)?\.(mp4|jpg)")

log = logging.getLogger(__name__)


def _timestamp():
    return datetime.now().strftime(TIME_FORMAT)


def is_recording_file(name):
    return FILE_NAME.fullmatch(name) is not None


@lru_cache(maxsize=512)  # finished videos never change
def _video_seconds(path):
    video = cv2.VideoCapture(path)
    frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    return round(frames / fps) if fps else 0


def list_recordings():
    """Returns all finished videos, newest first."""
    recordings = []
    for name in sorted(os.listdir(RECORDINGS_DIR), reverse=True):
        if not name.endswith(".mp4") or not is_recording_file(name):
            continue

        seconds = _video_seconds(os.path.join(RECORDINGS_DIR, name))
        date = datetime.strptime(name[:19], TIME_FORMAT)
        recordings.append({
            "video": name,
            "image": name.replace(".mp4", ".jpg"),
            "date": date.strftime("%d.%m.%Y %H:%M:%S"),
            "length": f"{seconds // 60}:{seconds % 60:02d}",
            "manual": name.endswith("_manual.mp4"),
        })
    return recordings


def _start_ffmpeg(path):
    """Starts ffmpeg, which turns JPEGs from stdin into a browser-ready MP4."""
    cmd = [
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "mjpeg", "-framerate", str(RECORD_FPS), "-i", "-",  # JPEGs from pipe
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",  # H.264, fast
        "-pix_fmt", "yuv420p",  # needed by browsers
        "-movflags", "+faststart",  # video starts before fully loaded
        "-threads", "2",  # leave CPU for stream and motion
        "-f", "mp4", path + ".part",
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _write(process, jpeg):
    try:
        process.stdin.write(jpeg)
    except OSError:
        pass  # ffmpeg crashed, _finish_ffmpeg reports it


def _finish_ffmpeg(process, path):
    try:
        process.stdin.close()  # tells ffmpeg the video is complete
    except OSError:
        pass
    process.wait()
    if process.returncode == 0:
        os.replace(path + ".part", path)  # only finished files get .mp4
        log.info("Saved %s", path)
    else:
        log.error("ffmpeg failed for %s", path)


def _save_snapshot(path, jpeg):
    with open(path.replace(".mp4", ".jpg"), "wb") as f:
        f.write(jpeg)


class Recorder:
    """Records videos on motion. Keeps the last seconds in a ring buffer."""

    def __init__(self, camera, motion):
        self.camera = camera
        self.motion = motion
        self.pre_seconds = float(os.getenv("RECORD_PRE_SECONDS", "5"))
        self.max_seconds = float(os.getenv("RECORD_MAX_SECONDS", "120"))
        clip_seconds = float(os.getenv("CLIP_SECONDS", "30"))

        # ring buffer: oldest frame drops out when full
        self.buffer = deque(maxlen=int(clip_seconds * RECORD_FPS))
        self.lock = threading.Lock()
        self.ffmpeg = None  # running ffmpeg while recording
        self.path = None
        self.start_time = 0
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

    def start(self):
        if shutil.which("ffmpeg") is None:
            log.error("ffmpeg not found, recording disabled")
            return
        threading.Thread(target=self._loop, daemon=True).start()

    def save_clip(self):
        """Saves the whole buffer (last CLIP_SECONDS) as a video."""
        with self.lock:
            frames = list(self.buffer)
        if frames:
            threading.Thread(target=self._write_clip, args=(frames,), daemon=True).start()

    def _loop(self):
        next_time = time.time()
        while True:
            jpeg = self.camera.get_jpeg()
            if jpeg is not None:
                with self.lock:
                    self.buffer.append(jpeg)
                self._update(jpeg)

            # steady frame rate, otherwise the video plays too fast or slow
            next_time += 1 / RECORD_FPS
            delay = next_time - time.time()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.time()  # too slow, don't try to catch up

    def _update(self, jpeg):
        if self.ffmpeg is None:
            if self.motion.active:
                self._start_recording()
            return

        _write(self.ffmpeg, jpeg)
        too_long = time.time() - self.start_time > self.max_seconds
        if not self.motion.active or too_long:
            self._stop_recording()

    def _start_recording(self):
        self.path = os.path.join(RECORDINGS_DIR, _timestamp() + ".mp4")
        self.start_time = time.time()
        self.ffmpeg = _start_ffmpeg(self.path)
        _save_snapshot(self.path, self.buffer[-1])
        log.info("Recording started")

        # pre-roll: last seconds before the motion
        pre_frames = int(self.pre_seconds * RECORD_FPS)
        for jpeg in list(self.buffer)[-pre_frames:]:
            _write(self.ffmpeg, jpeg)

    def _stop_recording(self):
        # finish in own thread, so the buffer keeps running
        threading.Thread(target=_finish_ffmpeg, args=(self.ffmpeg, self.path), daemon=True).start()
        self.ffmpeg = None

    def _write_clip(self, frames):
        path = os.path.join(RECORDINGS_DIR, _timestamp() + "_manual.mp4")
        _save_snapshot(path, frames[-1])
        process = _start_ffmpeg(path)
        for jpeg in frames:
            _write(process, jpeg)
        _finish_ffmpeg(process, path)


if __name__ == "__main__":
    # quick test: record on motion, Enter saves a manual clip
    from dotenv import load_dotenv

    from camera import Camera
    from motion import MotionDetector

    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    cam = Camera(os.getenv("CAMERA_SOURCE", "0"))
    cam.start()
    motion = MotionDetector(cam)
    motion.start()
    rec = Recorder(cam, motion)
    rec.start()

    while True:
        input("Recording on motion. Enter = save last 30 s, Ctrl+C = stop\n")
        rec.save_clip()
