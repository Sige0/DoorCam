import logging
import os
import shutil
import threading
import time
from datetime import datetime, timedelta

from recorder import RECORDINGS_DIR, TIME_FORMAT, delete_recording, is_recording_file

CHECK_SECONDS = 60

log = logging.getLogger(__name__)


def _recording_time(name):
    """Start time from the file name, e.g. 2026-11-24_14-02-11.mp4"""
    return datetime.strptime(name[:19], TIME_FORMAT)


def _remove(name, reason):
    try:
        os.remove(os.path.join(RECORDINGS_DIR, name))
        log.info("Deleted %s (%s)", name, reason)
    except OSError as error:
        log.error("Could not delete %s: %s", name, error)


class Cleanup:
    """Deletes old recordings and keeps enough free disk space."""

    def __init__(self):
        self.retention_minutes = int(os.getenv("RETENTION_MINUTES", "1440"))
        self.min_free_gb = float(os.getenv("MIN_FREE_GB", "2"))

    def start(self):
        # call before the recorder starts, so no recording is running yet
        for name in os.listdir(RECORDINGS_DIR):
            if name.endswith(".part"):
                _remove(name, "leftover from restart")

        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            self._delete_old()
            self._free_space()
            time.sleep(CHECK_SECONDS)

    def _delete_old(self):
        limit = datetime.now() - timedelta(minutes=self.retention_minutes)
        names = os.listdir(RECORDINGS_DIR)

        for name in names:
            if not is_recording_file(name) or _recording_time(name) > limit:
                continue

            if name.endswith(".mp4"):
                delete_recording(name, f"older than {self.retention_minutes} min")
            else:
                # snapshot: only if its video is missing and not being recorded
                video = name.replace(".jpg", ".mp4")
                if video not in names and video + ".part" not in names:
                    _remove(name, "snapshot without video")

    def _free_space(self):
        while shutil.disk_usage(RECORDINGS_DIR).free < self.min_free_gb * 1024 ** 3:
            # names start with the time, so sorted = oldest first
            videos = sorted(name for name in os.listdir(RECORDINGS_DIR)
                            if name.endswith(".mp4") and is_recording_file(name))
            if not videos:
                log.warning("Low disk space, no recordings left to delete")
                return
            if not delete_recording(videos[0], "low disk space"):
                return  # could not delete, don't loop forever
