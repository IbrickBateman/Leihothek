from flask import Blueprint, render_template, request, redirect, url_for, session
import os

from .services.detection import detect_items
from .services.locker import get_locker_status

main = Blueprint("main", __name__)


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["logged_in"] = True
            return redirect(url_for("main.home"))

    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@main.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    username = "Admin"  

    return render_template("home.html", username=username)


@main.route("/check", methods=["GET", "POST"])
def check():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lockers = {
        "Locker 1": os.path.join(BASE_DIR, "input", "test.jpg"),
        "Locker 2": os.path.join(BASE_DIR, "input", "test2.jpg"),
    }

    results_data = {}

    for locker_name, image_path in lockers.items():
        _, detected = detect_items(image_path)
        status = get_locker_status(detected)

        filename = os.path.basename(image_path)

        results_data[locker_name] = {
            "status": status,
            "image": filename
        }

    return render_template("index.html", lockers=results_data)

@main.route("/locker/<name>")
def locker_detail(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lockers = {
        "Locker 1": "test.jpg",
        "Locker 2": "test2.jpg"
    }

    if name not in lockers:
        return "Locker niet gevonden", 404

    image_path = os.path.join(BASE_DIR, "input", lockers[name])

    results, detected = detect_items(image_path)
    status = get_locker_status(detected)

    data = {
        "status": status,
        "image": lockers[name]
    }

    return render_template("locker.html", name=name, data=data)
