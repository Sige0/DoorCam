import os
import time

from dotenv import load_dotenv
from flask import Flask, Response, render_template

from camera import Camera

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream")
def stream():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # localhost only until login is done
    app.run(host="127.0.0.1", port=5000, threaded=True)
