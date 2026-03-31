from flask import Flask, render_template, request
from detect import check_image
import os

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(BASE_DIR, "input", "test.jpg")

    result = check_image(image_path)

    status = "OK" if result else "FOUT"
    return render_template("index.html", status=status)

if __name__ == "__main__":
    app.run(debug=True)