from ultralytics import YOLO
import cv2
import os

# ======================
# CONFIG
# ======================

MODEL_PATH = "model/yolov8n.pt"
CONF_THRESHOLD = 0.4   # 🔥 lager = beter detecteren

model = YOLO(MODEL_PATH)

# ======================
# IMAGE DETECTIE
# ======================

def detect_image(input_path, output_path):
    img = cv2.imread(input_path)

    if img is None:
        return []

    results = model(img)

    detections = []

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if conf > CONF_THRESHOLD:
                if label not in detections:
                    detections.append(label)

    annotated = results[0].plot()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated)

    return detections

# ======================
# FRAME DETECTIE
# ======================

def detect_frame(frame):
    results = model(frame)

    detections = []

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:
            conf = float(box.conf[0])
            label = model.names[int(box.cls[0])]

            if conf > CONF_THRESHOLD:
                detections.append(label)

    return detections