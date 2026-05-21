from flask import Blueprint, render_template, request, redirect, url_for, session, Response, jsonify
import os
import sqlite3
import bcrypt
import cv2
from datetime import datetime
import base64

from .services.detection import detect_frame, detect_image
from .services.locker import get_locker_status
from . import database as db

main = Blueprint("main", __name__)

# ------------------ CAMERA, alle camera ip even hieronder zetten later ------------------

CAMERA_SOURCES = [
    "http://192.168.25.27:8080/video",
    0
]

def get_working_camera():
    for source in CAMERA_SOURCES:
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                return cap
        cap.release()
    return None

def gen_frames():
    cap = get_working_camera()

    if cap is None:
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        cap.release()

@main.route('/video-feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ------------------ HELPERS ------------------

def current_user():
    return session.get("username")

def is_current_admin():
    return db.is_admin(session.get("username"))


# ------------------ AUTH ------------------

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("main.login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Gebruiker bestaat al")

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user[0]):
            session["logged_in"] = True
            session["username"] = username
            session["is_admin"] = db.is_admin(username)
            return redirect(url_for("main.home"))
        else:
            return render_template("login.html", error="Verkeerde login")

    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

# ------------------ HOME ------------------

@main.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    return render_template("home.html",
                           username=session.get("username"),
                           is_admin=is_current_admin())

# ------------------ SCAN ------------------

@main.route("/scan-page")
def scan_page():
    return render_template("scan.html")

@main.route("/scan", methods=["POST"])
def scan():
    cap = get_working_camera()
    if cap is None:
        return "Geen camera beschikbaar"

    frames = []
    for _ in range(5):
        ret, frame = cap.read()
        if ret:
            frames.append(frame)

    cap.release()

    if not frames:
        return "Geen beeld"

    
    all_detections = []

    for frame in frames:
        detections = detect_frame(frame)
        all_detections.extend(detections)

    final_detections = list(set(all_detections))

    status = get_locker_status(final_detections)

    return render_template("scan_result.html",
                           status=status,
                           detections=final_detections)


# ------------------ LOCKERS ------------------

lockers_data = [
    {"name": "Locker 1", "status": "available", "user": None, "rented_at": None, "blocked": False},
    {"name": "Locker 2", "status": "available", "user": None, "rented_at": None, "blocked": False},
    {"name": "Locker 3", "status": "available", "user": None, "rented_at": None, "blocked": False},
    {"name": "Locker 4", "status": "available", "user": None, "rented_at": None, "blocked": False},
]

BACKUP_LOCKER = "Locker 4"
admin_alerts = []
condition_reports = {}

# ------------------ CHECK ------------------

@main.route("/check")
def check():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    lockers = {
        "Locker 1": "test.jpg",
        "Locker 2": "test2.jpg",
        "Locker 3": "test3.jpg",
        "Locker 4": "test4.jpg",
    }

    results_data = {}

    for name, filename in lockers.items():
        input_path = os.path.join(BASE_DIR, "input", filename)
        output_path = os.path.join(BASE_DIR, "static", "output", filename)
        print("BASE_DIR:", BASE_DIR)
        print("INPUT PATH:", input_path)

        detections = detect_image(input_path, output_path)
        status = get_locker_status(detections)

        results_data[name] = {
            "status": status,
            "image": filename,
            "detections": detections
        }

    return render_template("index.html", lockers=results_data)

# ------------------ LOCKER DETAIL ------------------

@main.route("/locker/<name>")
def locker_detail(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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

    if not os.path.exists(input_path):
        return f"Image niet gevonden: {filename}"

    detections = detect_image(input_path, output_path)
    status = get_locker_status(detections)

    return render_template("locker.html", name=name, data={
        "status": status,
        "image": filename,
        "detections": detections
    })

# ------------------ RENTALS ------------------

@main.route("/rentals")
def rentals():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    total = len(lockers_data)
    available = sum(1 for l in lockers_data if l["status"] == "available" and not l["blocked"])
    rented = sum(1 for l in lockers_data if l["status"] == "rented")
    blocked = sum(1 for l in lockers_data if l["blocked"])

    for locker in lockers_data:
        reports = condition_reports.get(locker["name"], [])
        locker["last_report"] = reports[-1] if reports else None

    return render_template("rentals.html",
                           lockers=lockers_data,
                           total=total,
                           available=available,
                           rented=rented,
                           blocked=blocked,
                           alerts=admin_alerts,
                           backup_locker=BACKUP_LOCKER,
                           is_admin=is_current_admin())

# ------------------ PICKUP (alis - DEGISMEDI) ------------------

@main.route("/pickup/<name>")
def pickup(name):
    step = request.args.get("step", "open")
    reports = condition_reports.get(name, [])
    last_report = reports[-1] if reports else None
    return render_template("pickup.html", locker_name=name, step=step, last_report=last_report)


@main.route("/pickup/<name>/ok", methods=["POST"])
def pickup_ok(name):
    for locker in lockers_data:
        if locker["name"] == name and not locker["blocked"]:
            locker["status"] = "rented"
            locker["user"] = session.get("username")
            locker["rented_at"] = datetime.now().strftime("%H:%M")
    return redirect(url_for("main.rentals"))

@main.route("/pickup/<name>/broken", methods=["POST"])
def pickup_broken(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    user = session.get("username", "Admin")

    for locker in lockers_data:
        if locker["name"] == name:
            locker["blocked"] = True
            locker["status"] = "available"

    report = {
        "status": "BROKEN",
        "comment": "Item confirmed not working",
        "user": user,
        "photo": None,
        "timestamp": datetime.now().strftime("%d/%m %H:%M")
    }

    condition_reports.setdefault(name, []).append(report)

    admin_alerts.append({
        "locker": name,
        "user": user,
        "timestamp": datetime.now().strftime("%d/%m %H:%M"),
        "message": f"{name} geblokkeerd - item kapot gemeld door {user}"
    })

    return render_template("backup_locker.html",
                           broken_locker=name,
                           backup_locker=BACKUP_LOCKER)


# ============================================================
# IADE (RETURN) AKISI — RFID ILE
# Sira: 1) RFID okut -> 2) dolap acildi + kamera -> 3) durum formu
# ============================================================

# --- ADIM 1: RFID okutma ekrani ---
@main.route("/return-rfid")
def return_rfid():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    pico_ip = db.get_setting("pico_ip", "")
    return render_template("return_rfid.html", pico_ip=pico_ip)


# --- ADIM 1 API: kart okununca esyayi bul ---
@main.route("/return-rfid/api/scan", methods=["POST"])
def return_rfid_scan():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    rfid = (data.get("rfid") or "").strip().upper()
    if not rfid:
        return jsonify({"error": "rfid required"}), 400

    item = db.find_item_by_rfid(rfid)
    timestamp = datetime.now().strftime("%d/%m %H:%M:%S")

    if item:
        db.add_scan(rfid, item["name"], "OPEN", timestamp, source="client")
        return jsonify({
            "result": "OPEN",
            "rfid": rfid,
            "item_name": item["name"],
            # ADIM 2'ye yonlendir: dolap acildi + kamera
            "next_url": url_for("main.return_camera", name=item["name"]),
            "timestamp": timestamp,
        })
    else:
        db.add_scan(rfid, None, "UNKNOWN", timestamp, source="client")
        return jsonify({
            "result": "UNKNOWN",
            "rfid": rfid,
            "timestamp": timestamp,
        })


# --- ADIM 2: dolap acildi + kamera (YOLO scan) ---
@main.route("/return-camera/<name>")
def return_camera(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    return render_template("return_camera.html", item_name=name)


# --- ADIM 2 ACTION: kamera ile scan calistir, sonra ADIM 3'e gec ---
@main.route("/return-camera/<name>/scan", methods=["POST"])
def return_camera_scan(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))

    cap = get_working_camera()
    detections = []
    status = "FOUT"

    if cap is not None:
        frames = []
        for _ in range(5):
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        cap.release()

        all_detections = []
        for frame in frames:
            all_detections.extend(detect_frame(frame))
        detections = list(set(all_detections))
        status = get_locker_status(detections)

    # Kamera sonucunu ADIM 3 (durum formu) sayfasina tasi
    return render_template("return_camera.html",
                           item_name=name,
                           scan_done=True,
                           scan_status=status,
                           detections=detections)


# --- ADIM 3: urun durumu formu (fotograf + yorum) ---
@main.route("/return-form/<name>", methods=["GET"])
def return_form(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    return render_template("return_form.html", locker_name=name)


# --- ADIM 3 SUBMIT: durum kaydet, bitir ---
@main.route("/return-form/<name>", methods=["POST"])
def return_locker(name):
    status = request.form.get("status", "OK")
    problem_type = request.form.get("problem_type", "")
    comment = request.form.get("comment", "")
    user = session.get("username")

    if status == "DEFECT":
        status = "BROKEN" if problem_type == "BROKEN" else "MINOR"

    photo_filename = None
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    photo_data = request.form.get("photo_data", "")
    if photo_data.startswith("data:image"):
        header, encoded = photo_data.split(",", 1)
        safe_name = name.replace(" ", "_")
        photo_filename = f"{safe_name}_{datetime.now().strftime('%H%M%S')}.jpg"
        with open(os.path.join(upload_folder, photo_filename), "wb") as f:
            f.write(base64.b64decode(encoded))

    report = {
        "status": status,
        "comment": comment,
        "user": user,
        "photo": photo_filename,
        "timestamp": datetime.now().strftime("%d/%m %H:%M")
    }

    condition_reports.setdefault(name, []).append(report)

    # Eger bu isimde bir locker varsa durumunu guncelle (eski Locker 1-4 uyumu)
    for locker in lockers_data:
        if locker["name"] == name:
            locker["user"] = None
            locker["rented_at"] = None
            if status == "BROKEN":
                locker["blocked"] = True
                locker["status"] = "available"
                admin_alerts.append({
                    "locker": name,
                    "user": user,
                    "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                    "message": f"{name} geblokkeerd - item kapot ingeleverd door {user}"
                })
            else:
                locker["status"] = "available"

    return redirect(url_for("main.rentals"))


# ============================================================
# RFID ADMIN PANELI (sadece admin) — obje ekleme/silme
# ============================================================

@main.route("/rfid")
def rfid_page():
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    if not is_current_admin():
        # normal uye buraya giremez
        return redirect(url_for("main.home"))

    items = db.get_all_rfid_items()
    admin_scans = db.get_recent_scans(limit=30, source="admin")
    client_scans = db.get_recent_scans(limit=30, source="client")
    pico_ip = db.get_setting("pico_ip", "")

    return render_template(
        "rfid.html",
        items=items,
        admin_scans=admin_scans,
        client_scans=client_scans,
        pico_ip=pico_ip,
        is_admin=True,
    )


# ----- API: pico IP opslaan (admin) -----
@main.route("/rfid/api/pico-ip", methods=["GET", "POST"])
def rfid_pico_ip():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401

    if request.method == "POST":
        if not is_current_admin():
            return jsonify({"error": "forbidden"}), 403
        data = request.get_json(silent=True) or {}
        ip = (data.get("ip") or "").strip()
        if not ip:
            return jsonify({"error": "ip required"}), 400
        db.set_setting("pico_ip", ip)
        return jsonify({"ok": True, "ip": ip})

    return jsonify({"ip": db.get_setting("pico_ip", "")})


# ----- API: items CRUD (ekleme/silme sadece admin) -----
@main.route("/rfid/api/items", methods=["GET", "POST"])
def rfid_items():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401

    if request.method == "POST":
        if not is_current_admin():
            return jsonify({"error": "forbidden"}), 403

        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        rfid = (data.get("rfid") or "").strip().upper()

        if not name or not rfid:
            return jsonify({"error": "name and rfid required"}), 400

        if db.find_item_by_rfid(rfid):
            return jsonify({"error": "rfid already used"}), 409
        if db.find_item_by_name(name):
            return jsonify({"error": "name already used"}), 409

        item = db.add_rfid_item(name, rfid)
        if item is None:
            return jsonify({"error": "could not add item"}), 500
        return jsonify(item)

    return jsonify(db.get_all_rfid_items())


@main.route("/rfid/api/items/<int:item_id>", methods=["DELETE"])
def rfid_delete_item(item_id):
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    if not is_current_admin():
        return jsonify({"error": "forbidden"}), 403
    db.delete_rfid_item(item_id)
    return jsonify({"ok": True})


# ----- API: admin panelde test okutma (source='admin') -----
@main.route("/rfid/api/test-scan", methods=["POST"])
def rfid_test_scan():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    if not is_current_admin():
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    rfid = (data.get("rfid") or "").strip().upper()
    if not rfid:
        return jsonify({"error": "rfid required"}), 400

    item = db.find_item_by_rfid(rfid)
    timestamp = datetime.now().strftime("%d/%m %H:%M:%S")

    if item:
        db.add_scan(rfid, item["name"], "OPEN", timestamp, source="admin")
        return jsonify({
            "result": "OPEN",
            "rfid": rfid,
            "item_name": item["name"],
            "timestamp": timestamp,
        })
    else:
        db.add_scan(rfid, None, "UNKNOWN", timestamp, source="admin")
        return jsonify({
            "result": "UNKNOWN",
            "rfid": rfid,
            "timestamp": timestamp,
        })


# ----- API: son taramalari getir (source: admin / client) -----
@main.route("/rfid/api/scans", methods=["GET"])
def rfid_scans_list():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    source = request.args.get("source")  # 'admin', 'client' veya None (hepsi)
    return jsonify(db.get_recent_scans(limit=30, source=source))

# ------------------ UNBLOCK ------------------

@main.route("/unblock/<name>")
def unblock_locker(name):
    if not session.get("logged_in"):
        return redirect(url_for("main.login"))
    for locker in lockers_data:
        if locker["name"] == name:
            locker["blocked"] = False
    global admin_alerts
    admin_alerts = [a for a in admin_alerts if a["locker"] != name]
    if name in condition_reports:
        condition_reports[name] = []
    return redirect(url_for("main.rentals"))