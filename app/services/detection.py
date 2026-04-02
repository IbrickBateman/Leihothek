from ultralytics import YOLO
import cv2
import os

# ======================
# CONFIG
# ======================

MODEL_PATH = "model/yolov8n.pt"
CONF_THRESHOLD = 0.7

# model 1x laden (belangrijk!)
model = YOLO(MODEL_PATH)


# ======================
# FUNCTIE
# ======================

def detect_items(image_path):
    print("Processing:", image_path)

    img = cv2.imread(image_path)

    # ❌ als image niet geladen kan worden
    if img is None:
        print(f"❌ Kon niet laden: {image_path}")
        return [], False

    # YOLO detectie
    results = model(img)

    detected = False

    # check of er iets gedetecteerd is
    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            for box in r.boxes:
                conf = float(box.conf)
                if conf > CONF_THRESHOLD:
                    detected = True

    # ======================
    # AFBEELDING OPSLAAN
    # ======================

    annotated = results[0].plot()

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )

    output_folder = os.path.join(BASE_DIR, "static", "output")
    os.makedirs(output_folder, exist_ok=True)

    output_path = os.path.join(output_folder, os.path.basename(image_path))

    success = cv2.imwrite(output_path, annotated)

    print("Saved to:", output_path)
    print("Saved success:", success)

    # ======================
    # RETURN (ALTIJD ONDERAAN!)
    # ======================

    return results, detected