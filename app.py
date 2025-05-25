from flask import Flask, request, jsonify 
from flask.helpers import send_file
import numpy as np
import onnxruntime
import cv2
import json

app = Flask(__name__,
            static_url_path='/', 
            static_folder='web')

# Beide Modelle laden
sessions = {
    "EfficientNet-Lite4": onnxruntime.InferenceSession("efficientnet-lite4-11.onnx"),
    "MobileNetV2": onnxruntime.InferenceSession("mobilenetv2-7.onnx")
}

# Labels laden
labels = json.load(open("labels_map.txt", "r"))

# Softmax
def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

# Bildvorverarbeitung
def pre_process(img, dims):
    output_height, output_width, _ = dims
    img = resize_with_aspectratio(img, output_height, output_width, inter_pol=cv2.INTER_LINEAR)
    img = center_crop(img, output_height, output_width)
    img = np.asarray(img, dtype='float32')
    img -= [127.0, 127.0, 127.0]
    img /= [128.0, 128.0, 128.0]
    return img

def resize_with_aspectratio(img, out_height, out_width, scale=87.5, inter_pol=cv2.INTER_LINEAR):
    height, width, _ = img.shape
    new_height = int(100. * out_height / scale)
    new_width = int(100. * out_width / scale)
    if height > width:
        w = new_width
        h = int(new_height * height / width)
    else:
        h = new_height
        w = int(new_width * width / height)
    return cv2.resize(img, (w, h), interpolation=inter_pol)

def center_crop(img, out_height, out_width):
    height, width, _ = img.shape
    left = int((width - out_width) / 2)
    right = int((width + out_width) / 2)
    top = int((height - out_height) / 2)
    bottom = int((height + out_height) / 2)
    return img[top:bottom, left:right]

@app.route("/")
def indexPage():
    return send_file("web/index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    content = request.files.get('0', '').read()
    img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = pre_process(img, (224, 224, 3))
    img_batch = np.expand_dims(img, axis=0)

    all_results = {}
    for name, session in sessions.items():
        input_name = session.get_inputs()[0].name
        try:
            output = session.run(None, {input_name: img_batch})[0][0]
        except:
            nchw_batch = img_batch.transpose(0, 3, 1, 2)
            output = session.run(None, {input_name: nchw_batch})[0][0]

        # ✅ Nur für MobileNetV2: Softmax anwenden
        if name == "MobileNetV2":
            output = softmax(output)

        # Top-5 auswählen
        top_indices = output.argsort()[-5:][::-1]
        all_results[name] = [{"class": labels[str(i)], "value": float(output[i])} for i in top_indices]

    return jsonify(all_results)


# Lokales Starten ermöglichen
if __name__ == "__main__":
    app.run(debug=True)
