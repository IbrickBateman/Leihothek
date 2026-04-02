# 🔐 Locker AI Dashboard

Een webapplicatie gebouwd met **Python (Flask)** en **YOLOv8** om lockers automatisch te monitoren via beeldherkenning.

---

## 🚀 Features

- 🔐 Login systeem (admin)
- 🏠 Home pagina met overzicht
- 📦 Dashboard met meerdere lockers
- 🔍 Detailpagina per locker
- 🤖 AI detectie (YOLOv8)
- 🖼️ Output afbeeldingen met bounding boxes
- 🎨 Moderne UI (cards, navbar, Poppins font)

---

## 🧠 Hoe het werkt

1. Een afbeelding van een locker wordt ingeladen
2. YOLO analyseert de afbeelding
3. Objecten worden gedetecteerd
4. De app bepaalt de status (OK / FOUT)
5. Resultaat wordt weergegeven in het dashboard

---

## 🗂️ Project structuur

ai_camera/
│
├── app/
│ ├── routes.py
│ ├── services/
│ │ ├── detection.py
│ │ └── locker.py
│ └── templates/
│
├── static/
│ ├── css/
│ ├── input/
│ └── output/
│
├── run.py
└── README.md
