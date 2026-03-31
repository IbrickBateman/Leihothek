from ultralytics import YOLO
import cv2
import os
import time

# ======================
# CONFIG
# ======================

MODEL_PATH = "yolov8n.pt"   # tijdelijk model (werkt zonder Roboflow)
INPUT_FOLDER = "input/"
OUTPUT_FOLDER = "output/"
CONF_THRESHOLD = 0.7

# maak output map als die niet bestaat
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# laad model
model = YOLO(MODEL_PATH)

# ======================
# FUNCTIES
# ======================

def check_image(image_path):
    img = cv2.imread(image_path)

    if img is None:
        print(f"❌ Kon niet laden: {image_path}")
        return False

    results = model(img)

    detected = False

    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            for box in r.boxes:
                conf = float(box.conf)
                if conf > CONF_THRESHOLD:
                    detected = True

    status = "OK" if detected else "FOUT"

    print(f"{os.path.basename(image_path)} -> {status}")

    # logging
    with open("../log.txt", "a", encoding="utf-8") as f:
        f.write(f"{image_path} -> {status}\n")

    # afbeelding opslaan
    annotated = results[0].plot()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(BASE_DIR, "static", "output", os.path.basename(image_path))

    os.makedirs(os.path.join(BASE_DIR, "static", "output"), exist_ok=True)

    success = cv2.imwrite(output_path, annotated)

    print("Saving to:", output_path)
    print("Saved:", success)

    return detected


def run_batch():
    print("🔄 Batch check gestart...\n")

    for file in os.listdir(INPUT_FOLDER):
        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        path = os.path.join(INPUT_FOLDER, file)
        check_image(path)

    print("\n✅ Batch klaar")


def run_live_simulation():
    print("📡 Live monitoring gestart...\n")

    while True:
        for file in os.listdir(INPUT_FOLDER):
            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(INPUT_FOLDER, file)
            result = check_image(path)

            if result:
                print("🔓 Locker OK")
            else:
                print("🚨 Locker probleem!")

        print("⏳ Wachten...\n")
        time.sleep(5)


def manual_trigger():
    input("📦 Druk op ENTER om locker te checken...")
    run_batch()


# ======================
# MAIN MENU
# ======================

if __name__ == "__main__":
    print("==== LOCKER AI SYSTEEM ====")
    print("1. Batch check")
    print("2. Live monitoring")
    print("3. Handmatige check")

    choice = input("Kies optie: ")

    if choice == "1":
        run_batch()
    elif choice == "2":
        run_live_simulation()
    elif choice == "3":
        manual_trigger()
    else:
        print("❌ Ongeldige keuze")