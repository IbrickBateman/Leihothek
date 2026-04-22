from ultralytics import YOLO
import os

model = YOLO("yolov8n.pt")

def detect_image(input_path, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)

    results = model(input_path, conf=0.2)

    detections = []

    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            for box in r.boxes:
                conf = float(box.conf[0])

                if conf > 0.4:
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    detections.append(label)

        r.save(filename=output_path)

    print("DETECTIONS:", detections)
    print("SAVED TO:", output_path)

    return detections