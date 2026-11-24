import logging
import os
import time
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, Response, abort, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from auth import bp as auth_bp, login_manager
from away import AwayMode
from camera import Camera
from cleanup import Cleanup
from motion import MotionDetector
from recorder import (RECORDINGS_DIR, Recorder, delete_recording, is_recording_file,
                      list_recordings, storage_info)

load_dotenv(override=True)  # .env wins over old terminal variables

# log to console and file, with date and time
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler("doorcam.log", encoding="utf-8")],
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # hide request lines

secret = os.getenv("SECRET_KEY")
if not secret or secret == "change-me":
    raise RuntimeError("Set a real SECRET_KEY in .env")

app = Flask(__name__)
app.config["SECRET_KEY"] = secret
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)
app.config["REMEMBER_COOKIE_REFRESH_EACH_REQUEST"] = True
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

login_manager.init_app(app)
app.register_blueprint(auth_bp)

camera = Camera(os.getenv("CAMERA_SOURCE", "0"))
camera.start()

motion = MotionDetector(camera)
motion.start()

recorder = Recorder(camera, motion)

cleanup = Cleanup()
cleanup.start()  # before recorder.start(), removes leftovers of old recordings

recorder.start()

away = AwayMode()


def generate_frames():
    while True:
        jpeg = camera.get_jpeg()
        if jpeg is None:
            time.sleep(0.1)
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
        time.sleep(1 / 15)  # ~15 fps is enough


def stream_response():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


def is_kiosk():
    """True for the browser on the Pi itself, the display has no login."""
    local = request.remote_addr == "127.0.0.1"
    own_host = request.host.split(":")[0] == "127.0.0.1"  # blocks DNS rebinding
    fetch_site = request.headers.get("Sec-Fetch-Site", "none")
    same_site = fetch_site in ("none", "same-origin")  # blocks other websites
    return local and own_host and same_site


def local_only():
    if not is_kiosk():
        abort(403)


def login_or_kiosk(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if is_kiosk() or current_user.is_authenticated:
            return view(*args, **kwargs)
        return login_manager.unauthorized()
    return wrapper


@app.after_request
def security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"  # no embedding in other sites
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html", clip_seconds=recorder.clip_seconds, away_on=away.is_on())


@app.route("/stream")
@login_required
def stream():
    return stream_response()


@app.route("/status")
@login_or_kiosk
def status():
    return jsonify(motion=motion.active, away=away.status())


@app.route("/away", methods=["POST"])
@login_required  # only the website, not the display
def set_away():
    if request.form.get("on") == "1":
        away.turn_on()
        flash(f"Abwesend-Modus startet in {away.delay} s")
    else:
        away.turn_off()
        flash("Abwesend-Modus ausgeschaltet")
    return redirect(url_for("index"))


@app.route("/recordings")
@login_or_kiosk
def recordings():
    return render_template("recordings.html", recordings=list_recordings(),
                           storage=storage_info(), kiosk=is_kiosk(),
                           retention_minutes=cleanup.retention_minutes)


@app.route("/recordings/<name>")
@login_or_kiosk
def recording_file(name):
    # only our own file names, blocks path traversal
    if not is_recording_file(name):
        abort(404)

    download = request.args.get("download") == "1"
    return send_from_directory(os.path.abspath(RECORDINGS_DIR), name, as_attachment=download)


@app.route("/recordings/<name>/delete", methods=["POST"])
@login_or_kiosk
def delete_file(name):
    if delete_recording(name):
        flash("Aufnahme gelöscht")
    else:
        flash("Aufnahme konnte nicht gelöscht werden")
    return redirect(url_for("recordings"))


@app.route("/clip", methods=["POST"])
@login_or_kiosk
def save_clip():
    if recorder.save_clip():
        flash("Wird gespeichert, erscheint gleich unter Aufnahmen")
    else:
        flash("Speichern ist gerade nicht möglich")
    return redirect(url_for("display" if is_kiosk() else "index"))


@app.route("/display")
def display():
    local_only()
    return render_template("display.html", clip_seconds=recorder.clip_seconds)


@app.route("/display/stream")
def display_stream():
    local_only()
    return stream_response()


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=5000, threaded=True)
