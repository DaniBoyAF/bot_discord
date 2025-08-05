from flask import Flask, render_template, jsonify
import json
from utils.dictionnaries import weather_dictionary
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("painel.html")

@app.route("/pnues")
def pneus():
    return render_template("Tyre_hub.html")
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
        with open("dados_de_voltas.json","r",encoding="utf-8") as f:
           data = json.load(f)
        return jsonify(data)
    except Exception as e :
        return jsonify({"erro": str(e)})
@app.route("/dados_delta")  
def dados_delta():
    try: 
        with open("dados_delta.json","r",encoding="utf-8") as f:
            data =json.load(f)
        return jsonify(data)
    except Exception as e :
        return jsonify({"erro": str(e)})
@app.route("/dados_pra_o_painel")
def dados_pra_o_painel():
    try:
        with open("dados_pra_o_painel.json","r",encoding="utf-8") as f:
          data= json.load(f)
        return jsonify(data)
    except Exception as e :
        return jsonify({"erro": str(e)})
@app.route("/dados_da_SESSION")
def dados_da_SESSION():
    try:
        with open ("dados_da_SESSION.json","r",encoding="utf-8")as f:
             data =json.load(f)
        return jsonify(data)
    except Exception as e :
        return jsonify({"erro": str(e)})

@app.route("/dados_completos")
def dados_completos():
    try:
        # Lê os dados dos pneus
        with open("dados_pra_o_painel.json", "r", encoding="utf-8") as f:
            dados_painel = json.load(f)

        # Lê os dados da sessão
        with open("dados_da_SESSION.json", "r", encoding="utf-8") as f:
            dados_sessao = json.load(f)
        
        # Tradução do código de clima para texto
        if isinstance(dados_sessao.get("clima"), int):
            dados_sessao["clima"] = weather_dictionary.get(dados_sessao["clima"], "Desconhecido")

        # Retorna tudo junto
        return jsonify({
            "sessao": dados_sessao,
            "pilotos": dados_painel
        })

    except Exception as e:
        return jsonify({"erro": str(e)})