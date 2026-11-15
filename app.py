import os
import time
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, Response, abort, render_template, request
from flask_login import login_required

from auth import bp as auth_bp, login_manager
from camera import Camera

load_dotenv(override=True)  # .env wins over old terminal variables

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


def local_only():
    # display pages have no login, so only the Pi itself may open them
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)


@app.after_request
def security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"  # no embedding in other sites
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/stream")
@login_required
def stream():
    return stream_response()


@app.route("/display")
def display():
    local_only()
    return render_template("display.html")


@app.route("/display/stream")
def display_stream():
    local_only()
    return stream_response()


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=5000, threaded=True)
