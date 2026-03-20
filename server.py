"""
Railway web shim for the desktop-first repository.

This keeps Railway deployments healthy in a headless environment where the
Tkinter GUI cannot be started.
"""

import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        service="xgenSuite",
        status="ok",
        mode="railway-web-shim",
        message=(
            "This repository's main app is a desktop GUI. "
            "Railway runs this lightweight status service instead."
        ),
    )


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
