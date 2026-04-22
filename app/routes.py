from flask import Blueprint, render_template, request, redirect, url_for, session
import os

from .services.detection import detect_items
from .services.locker import get_locker_status
from datetime import datetime
from .services.yolo_services import detect_image

lockers_data = [
    {"name": "Locker 1", "status": "available", "user": None, "rented_at": None},
    {"name": "Locker 2", "status": "available", "user": None, "rented_at": None},
    {"name": "Locker 3", "status": "available", "user": None, "rented_at": None},
    {"name": "Locker 4", "status": "available", "user": None, "rented_at": None},
]

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
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lockers = {
    "Locker 1": os.path.join(BASE_DIR, "input", "test.jpg"),
    "Locker 2": os.path.join(BASE_DIR, "input", "test2.jpg"),
    "Locker 3": os.path.join(BASE_DIR, "input", "test3.jpg"),
    "Locker 4": os.path.join(BASE_DIR, "input", "test4.jpg"),
}

    results_data = {}

    for locker_name, image_path in lockers.items():
        filename = os.path.basename(image_path)

        input_path = image_path
        output_path = os.path.join(BASE_DIR, "static", "output", filename)

        detections = detect_image(input_path, output_path)

        if not detections:
            status = "FOUT"
        elif "laptop" in detections:
            status = "FOUT"
        else:
            status = "OK"
        
        results_data[locker_name] = {
            "status": status,
            "image": filename,
            "detections": detections
    }

    return render_template("index.html", lockers=results_data)

@main.route("/locker/<name>")
def locker_detail(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lockers = {
        "Locker 1": "test.jpg",
        "Locker 2": "test2.jpg",
        "Locker 3": "test3.jpg",
        "Locker 4": "test4.jpg",
    }

    if name not in lockers:
        return "Locker niet gevonden", 404

    filename = lockers[name]

    input_path = os.path.join(BASE_DIR, "input", filename)
    output_path = os.path.join(BASE_DIR, "static", "output", filename)

    detections = detect_image(input_path, output_path)

    if not detections:
        status = "FOUT"
    elif "laptop" in detections:
        status = "FOUT"
    else:
        status = "OK"

    data = {
        "status": status,
        "image": filename
    }

    return render_template("locker.html", name=name, data=data)

@main.route("/rentals")
def rentals():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    total = len(lockers_data)
    available = sum(1 for l in lockers_data if l["status"] == "available")
    rented = sum(1 for l in lockers_data if l["status"] == "rented")

    return render_template(
        "rentals.html",
        lockers=lockers_data,
        total=total,
        available=available,
        rented=rented
    )


@main.route("/rent/<name>")
def rent_locker(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    for locker in lockers_data:
        if locker["name"] == name:
            locker["status"] = "rented"
            locker["user"] = "Admin"
            locker["rented_at"] = datetime.now().strftime("%H:%M")

    return redirect(url_for("main.rentals"))

@main.route("/free/<name>")
def free_locker(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    for locker in lockers_data:
        if locker["name"] == name:
            locker["status"] = "available"
            locker["user"] = None
            locker["rented_at"] = None

    return redirect(url_for("main.rentals"))