from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")

@app.route('/servicios', methods=["GET"])
def servicios():
    return render_template("servicios.html")

@app.route('/calendario', methods=["GET"])
def calendario():
    return render_template("calendario.html")

if __name__ == "__main__":
    app.run()