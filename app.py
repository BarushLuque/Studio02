from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=["GET"])
def index():
    return jsonify(
        {
            "Estado": True, 
            "Mensaje": "Nueva pagina"
         }
        ), 200

if __name__ == "__main__":
    app.run()