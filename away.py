import json
import logging
import math
import os
import threading
import time

STATE_FILE = "state.json"

log = logging.getLogger(__name__)


class AwayMode:
    """Away mode with start delay, saved in state.json to survive a restart."""

    def __init__(self):
        self.delay = int(os.getenv("AWAY_DELAY_SECONDS", "60"))
        self.lock = threading.Lock()
        self.active_from = None  # time when away mode starts, None = off
        self._load()

    def turn_on(self):
        with self.lock:
            if self.active_from is not None:
                return
            self.active_from = time.time() + self.delay
            self._save()
        log.info("Away mode on (active in %d s)", self.delay)

    def turn_off(self):
        with self.lock:
            if self.active_from is None:
                return
            self.active_from = None
            self._save()
        log.info("Away mode off")

    def is_on(self):
        """True as soon as it is switched on, also during the delay."""
        return self.active_from is not None

    def is_active(self):
        """True after the delay. Only then mails are sent."""
        return self.is_on() and time.time() >= self.active_from

    def status(self):
        seconds_left = 0
        if self.is_on() and not self.is_active():
            seconds_left = math.ceil(self.active_from - time.time())
        return {"on": self.is_on(), "active": self.is_active(), "seconds_left": seconds_left}

    def _load(self):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                self.active_from = json.load(f).get("away_active_from")
        except FileNotFoundError:
            return
        except (OSError, ValueError) as error:
            log.error("Could not read %s, away mode off: %s", STATE_FILE, error)
            return

        if self.is_on():
            log.info("Away mode restored after restart")

    def _save(self):
        # write a temp file first, so state.json is never half written
        temp = STATE_FILE + ".tmp"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump({"away_active_from": self.active_from}, f)
            os.replace(temp, STATE_FILE)
        except OSError as error:
            log.error("Could not save %s: %s", STATE_FILE, error)


if __name__ == "__main__":
    # quick test with 3 s delay
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    os.environ["AWAY_DELAY_SECONDS"] = "3"

    away = AwayMode()
    away.turn_on()
    for _ in range(5):
        print(away.status())
        time.sleep(1)
    away.turn_off()
    print(away.status())
