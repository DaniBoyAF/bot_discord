from flask import Flask, render_template, jsonify
import json
import os
import sqlite3

app = Flask(__name__)
STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "f1_telemetry.db"))

def carregar_json(arquivo):
    caminho = os.path.join(STATIC_PATH, arquivo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# ========== ROTAS DE PÁGINAS ==========
@app.route("/")
def home():
    return render_template("selecionar_sessao.html")

@app.route("/g")
def g_page():
    return render_template("Race_Pace.html")

@app.route("/graf")
def graf_page():
    return render_template("Media_lap.html")

@app.route("/pit")
def pit_page():
    return render_template("pit_stop.html")

@app.route("/painel")
def painel():
    return render_template("painel.html")

# ========== ENDPOINTS DE DADOS ==========

@app.route("/historico_sessoes")
def historico_sessoes():
    """Lista todas as sessões disponíveis"""
    dados = carregar_json("sessoes.json")
    if dados:
        return jsonify(dados.get("sessoes", []))
    return jsonify([])

@app.route("/dados_voltas/<int:sessao_id>")
def dados_voltas(sessao_id):
    """JSON 1: Voltas e setores"""
    dados = carregar_json(f"sessao_{sessao_id}_voltas.json")
    if dados:
        return jsonify(dados.get("pilotos", []))
    return jsonify([])

@app.route("/dados_pneus/<int:sessao_id>")
def dados_pneus(sessao_id):
    """JSON 2: Pneus e stints"""
    dados = carregar_json(f"sessao_{sessao_id}_pneus.json")
    if dados:
        return jsonify(dados.get("pilotos", []))
    return jsonify([])

@app.route("/dados_danos/<int:sessao_id>")
def dados_danos(sessao_id):
    """JSON 3: Danos e velocidade"""
    dados = carregar_json(f"sessao_{sessao_id}_danos.json")
    if dados:
        return jsonify(dados.get("pilotos", []))
    return jsonify([])

@app.route("/dados_completos/<int:sessao_id>")
def dados_completos(sessao_id):
    """Retorna os 3 JSONs juntos"""
    voltas = carregar_json(f"sessao_{sessao_id}_voltas.json")
    pneus = carregar_json(f"sessao_{sessao_id}_pneus.json")
    danos = carregar_json(f"sessao_{sessao_id}_danos.json")
    
    return jsonify({
        "voltas": voltas.get("pilotos", []) if voltas else [],
        "pneus": pneus.get("pilotos", []) if pneus else [],
        "danos": danos.get("pilotos", []) if danos else [],
        "sessao": voltas.get("sessao", {}) if voltas else {}
    })

# ========== ENDPOINTS LIVE (sem sessao_id) ==========

@app.route("/dados_voltas")
def dados_voltas_live():
    """Retorna última sessão disponível"""
    sessoes = carregar_json("sessoes.json")
    if sessoes and sessoes.get("sessoes"):
        ultimo_id = sessoes["sessoes"][0]["id"]
        return dados_voltas(ultimo_id)
    return jsonify([])

@app.route("/dados_pneus_live")
def dados_pneus_live():
    sessoes = carregar_json("sessoes.json")
    if sessoes and sessoes.get("sessoes"):
        ultimo_id = sessoes["sessoes"][0]["id"]
        return dados_pneus(ultimo_id)
    return jsonify([])

@app.route("/dados_pra_o_painel")
def dados_pra_o_painel():
    sessoes = carregar_json("sessoes.json")
    if sessoes and sessoes.get("sessoes"):
        ultimo_id = sessoes["sessoes"][0]["id"]
        return dados_pneus(ultimo_id)
    return jsonify([])

@app.route("/apagar_sessao/<int:sessao_id>", methods=["POST"])
def apagar_sessao(sessao_id):
    """Exclui uma sessão específica e todos os dados relacionados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Busca pilotos da sessão para excluir dados relacionados
        cur.execute("SELECT id FROM pilotos WHERE sessao_id = ?", (sessao_id,))
        piloto_ids = [r[0] for r in cur.fetchall()]
        
        if piloto_ids:
            placeholders = ",".join("?" * len(piloto_ids))
            # Exclui dados relacionados aos pilotos
            cur.execute(f"DELETE FROM voltas WHERE piloto_id IN ({placeholders})", piloto_ids)
            cur.execute(f"DELETE FROM pneus WHERE piloto_id IN ({placeholders})", piloto_ids)
            cur.execute(f"DELETE FROM danos WHERE piloto_id IN ({placeholders})", piloto_ids)
            cur.execute(f"DELETE FROM telemetria WHERE piloto_id IN ({placeholders})", piloto_ids)
            cur.execute(f"DELETE FROM pneu_stints WHERE piloto_id IN ({placeholders})", piloto_ids)
        
        # Exclui voltas e pilotos da sessão
        cur.execute("DELETE FROM voltas WHERE sessao_id = ?", (sessao_id,))
        cur.execute("DELETE FROM pilotos WHERE sessao_id = ?", (sessao_id,))
        cur.execute("DELETE FROM sessoes WHERE id = ?", (sessao_id,))
        
        conn.commit()
        conn.close()
        
        # Remove JSONs da sessão se existirem
        for suffix in ["_voltas.json", "_pneus.json", "_danos.json"]:
            json_path = os.path.join(STATIC_PATH, f"sessao_{sessao_id}{suffix}")
            if os.path.exists(json_path):
                os.remove(json_path)
        
        return jsonify({"ok": True, "mensagem": f"Sessão {sessao_id} excluída"})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/apagar_db", methods=["POST"])
def apagar_db():
    """Apaga todo o banco de dados"""
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        
        # Remove todos os JSONs de sessão
        for f in os.listdir(STATIC_PATH):
            if f.startswith("sessao_") and f.endswith(".json"):
                os.remove(os.path.join(STATIC_PATH, f))
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

if __name__ == "__main__":
    print(f"[INFO] STATIC_PATH: {STATIC_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
