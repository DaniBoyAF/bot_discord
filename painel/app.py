from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("painel.html")
@app.route("/dados_pneus")
def dados_pneus():
    try:
        with open("dados_dos_pneus.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/dados_voltas")
def dados_voltas():
    try:
        with open("dados_de_voltas.json","w",encoding="utf-8") as f:
           data = json.load(f)
        return jsonify(data)
    except Exception as e :
        return jsonify({"erro": str(e)})
    

