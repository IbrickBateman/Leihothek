from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model("input/test3.jpg", conf=0.25)

results[0].show()

for box in results[0].boxes:
    cls = int(box.cls[0])
    print(model.names[cls])