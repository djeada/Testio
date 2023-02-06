import requests
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout, QApplication
from flask import Flask, render_template
from threading import Thread
import sys

TEMPLATE_FOLDER = "."


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        widget = QWidget()
        self.label = QLabel("Loading...")
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def update_label(self, text):
        self.label.setText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app_ = Flask(__name__, template_folder=TEMPLATE_FOLDER)

    @app_.route("/")
    def index():
        return render_template("index.html")

    kwargs = {
        "host": "127.0.0.1",
        "port": 5000,
        "threaded": True,
        "use_reloader": False,
        "debug": False,
    }

    flaskThread = Thread(target=app_.run, daemon=True, kwargs=kwargs).start()

    # Make the request to the Flask server
    response = requests.get("http://127.0.0.1:5000/")
    window.update_label(response.text)

    app.exec()
