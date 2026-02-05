from flask import Flask, render_template, jsonify, request
import os
import json
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

def _get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]

def _pick(row, keys, default=None):
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default

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
@app.route("/tyres")
def tyres_page():
    return render_template("Tyre_hub.html")

# ========== ENDPOINTS DE DADOS ==========

@app.route("/historico_sessoes")
def historico_sessoes():
    """Lista todas as sessões do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Verifica se coluna nome_customizado existe
        cur.execute("PRAGMA table_info(sessoes)")
        colunas = [col[1] for col in cur.fetchall()]
        
        if "nome_customizado" in colunas:
            cur.execute("""
                SELECT id, nome_pista, nome_customizado, tipo_sessao, data_hora, 
                       total_voltas, velocidade_maxima_geral
                FROM sessoes 
                ORDER BY id DESC
            """)
        else:
            cur.execute("""
                SELECT id, nome_pista, NULL as nome_customizado, tipo_sessao, data_hora, 
                       total_voltas, velocidade_maxima_geral
                FROM sessoes 
                ORDER BY id DESC
            """)
        
        sessoes = [dict(r) for r in cur.fetchall()]
        conn.close()
        
        return jsonify(sessoes)
    except Exception as e:
        print(f"Erro historico_sessoes: {e}")
        return jsonify([])

@app.route("/dados_voltas/<int:sessao_id>")
def dados_voltas(sessao_id):
    """JSON: Voltas e setores - direto do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Busca info da sessão (total_voltas)
        cur.execute("SELECT total_voltas FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cur.fetchone()
        total_voltas_sessao = sessao_row["total_voltas"] if sessao_row else 0

        # Busca pilotos ÚNICOS da sessão
        cur.execute("""
            SELECT MIN(id) as id, nome, numero, MAX(posicao) as posicao
            FROM pilotos 
            WHERE sessao_id = ?
            GROUP BY nome
            ORDER BY posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]

        dados = []
        for p in pilotos:
            piloto_id = p.get("id")
            nome = p.get("nome", "Desconhecido")
            numero = p.get("numero")
            posicao = p.get("posicao")

            # Busca voltas do piloto (agrupadas por numero_volta para evitar duplicatas)
            cur.execute("""
                SELECT numero_volta, 
                       AVG(tempo_volta) as tempo_volta,
                       AVG(setor1) as setor1, 
                       AVG(setor2) as setor2, 
                       AVG(setor3) as setor3
                FROM voltas
                WHERE sessao_id = ? AND piloto_id = ?
                GROUP BY numero_volta
                ORDER BY numero_volta
            """, (sessao_id, piloto_id))

            voltas = []
            for v in cur.fetchall():
                voltas.append({
                    "numero_volta": v["numero_volta"],
                    "tempo_total": v["tempo_volta"],
                    "setor1": v["setor1"],
                    "setor2": v["setor2"],
                    "setor3": v["setor3"]
                })

            # CORRIGIDO: Pega o número da última volta (não a quantidade de registros)
            cur.execute("""
                SELECT MAX(numero_volta) as max_volta
                FROM voltas
                WHERE sessao_id = ? AND piloto_id = ?
            """, (sessao_id, piloto_id))
            max_row = cur.fetchone()
            total_voltas_piloto = max_row["max_volta"] if max_row and max_row["max_volta"] else len(voltas)

            dados.append({
                "nome": nome,
                "numero": numero,
                "posicao": posicao,
                "voltas": voltas,
                "total_voltas_piloto": total_voltas_piloto  # ← Agora é a última volta real
            })

        conn.close()
        
        return jsonify({
            "total_voltas_sessao": total_voltas_sessao,
            "pilotos": dados
        })
    except Exception as e:
        print(f"Erro ao buscar dados_voltas: {e}")
        return jsonify({"total_voltas_sessao": 0, "pilotos": []})

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
    """Pega a última sessão do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id FROM sessoes ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify([])
        return dados_voltas(row["id"])
    except Exception as e:
        print(f"Erro ao buscar dados_voltas_live: {e}")
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
    """JSON: Dados de pit stops/stints - AO VIVO do parser"""
    try:
        from Bot.jogadores import JOGADORES
        from utils.dictionnaries import tyres_dictionnary
        
        dados = []
        for idx, piloto in enumerate(JOGADORES):
            nome = getattr(piloto, 'name', '')
            if not nome or nome.strip() == '':
                continue
            
            # Pega stints do piloto
            pneu_stints = getattr(piloto, 'pneu_stints', [])
            
            # Converte stints para formato esperado pelo frontend
            stints = []
            for stint in pneu_stints:
                stints.append({
                    "tipo_pneu": stint.get("composto", "MEDIUM"),
                    "volta_inicio": stint.get("volta_inicio", 1),
                    "volta_fim": stint.get("volta_fim", 0),
                    "total_voltas": stint.get("total_voltas", 0)
                })
            
            # Composto atual
            tyres_code = getattr(piloto, 'tyres', 17)
            tyres_name = tyres_dictionnary.get(tyres_code, "MEDIUM")
            
            # Voltas completadas
            num_laps = getattr(piloto, 'num_laps', 0) or getattr(piloto, 'currentLapNum', 0)
            
            dados.append({
                "nome": nome,
                "numero": getattr(piloto, 'numero', idx),
                "position": getattr(piloto, 'position', idx + 1),
                "tyres": tyres_name,
                "num_laps": num_laps,
                "stints": stints
            })
        
        # Ordena por posição
        dados.sort(key=lambda x: x.get('position', 99))
        
        return jsonify(dados)
    except Exception as e:
        print(f"Erro dados_pra_o_painel: {e}")
        # Fallback: tenta pegar do banco
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("SELECT id FROM sessoes ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                conn.close()
                return jsonify([])
            
            sessao_id = row["id"]
            
            cur.execute("""
                SELECT MIN(id) as id, nome, numero, MAX(posicao) as posicao, pneu_atual
                FROM pilotos 
                WHERE sessao_id = ?
                GROUP BY nome
                ORDER BY posicao
            """, (sessao_id,))
            pilotos = [dict(r) for r in cur.fetchall()]
            
            dados = []
            for p in pilotos:
                dados.append({
                    "nome": p.get("nome", "Desconhecido"),
                    "numero": p.get("numero"),
                    "position": p.get("posicao", 99),
                    "tyres": p.get("pneu_atual", "MEDIUM"),
                    "num_laps": 0,
                    "stints": []
                })
            
            conn.close()
            return jsonify(dados)
        except:
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

@app.route("/dados_completos_live")
def dados_completos_live():
    """JSON: Dados completos da sessão atual - direto do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Pega a última sessão
        cur.execute("SELECT * FROM sessoes ORDER BY id DESC LIMIT 1")
        sessao = cur.fetchone()
        if not sessao:
            conn.close()
            return jsonify({"pilotos": [], "clima": {}, "sessao": {}})
        
        sessao_id = sessao["id"]
        sessao_dict = dict(sessao)
        
        # Busca pilotos ÚNICOS da sessão (pega o registro mais recente de cada)
        cur.execute("""
            SELECT p.*
            FROM pilotos p
            INNER JOIN (
                SELECT nome, MAX(id) as max_id
                FROM pilotos
                WHERE sessao_id = ?
                GROUP BY nome
            ) latest ON p.id = latest.max_id
            ORDER BY p.posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]
        
        # Busca clima (se existir tabela)
        clima = {}
        try:
            cur.execute("PRAGMA table_info(clima)")
            if cur.fetchall():
                cur.execute("SELECT * FROM clima WHERE sessao_id = ? ORDER BY id DESC LIMIT 1", (sessao_id,))
                clima_row = cur.fetchone()
                if clima_row:
                    clima = dict(clima_row)
        except:
            pass
        
        conn.close()
        
        return jsonify({
            "pilotos": pilotos,
            "clima": clima,
            "sessao": sessao_dict
        })
    except Exception as e:
        print(f"Erro ao buscar dados_completos_live: {e}")
        return jsonify({"pilotos": [], "clima": {}, "sessao": {}})

@app.route("/dados_stints_ultimo")
def dados_stints_ultimo():
    """JSON: Stints da última sessão do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Busca última sessão
        cur.execute("SELECT id, nome_pista, tipo_sessao, total_voltas FROM sessoes ORDER BY id DESC LIMIT 1")
        sessao = cur.fetchone()
        
        if not sessao:
            conn.close()
            return jsonify({"sessao": {}, "pilotos": []})
        
        sessao_id = sessao["id"]
        
        return _dados_stints_por_sessao(cur, sessao_id, dict(sessao))
        
    except Exception as e:
        print(f"Erro dados_stints_ultimo: {e}")
        return jsonify({"sessao": {}, "pilotos": []})


@app.route("/dados_stints/<int:sessao_id>")
def dados_stints(sessao_id):
    """JSON: Stints de uma sessão específica do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Busca info da sessão
        cur.execute("SELECT id, nome_pista, tipo_sessao, total_voltas FROM sessoes WHERE id = ?", (sessao_id,))
        sessao = cur.fetchone()
        
        if not sessao:
            conn.close()
            return jsonify({"sessao": {}, "pilotos": []})
        
        return _dados_stints_por_sessao(cur, sessao_id, dict(sessao))
        
    except Exception as e:
        print(f"Erro dados_stints/{sessao_id}: {e}")
        return jsonify({"sessao": {}, "pilotos": []})


def _dados_stints_por_sessao(cur, sessao_id, sessao_info):
    """Função auxiliar: busca stints de uma sessão"""
    try:
        # Busca pilotos únicos
        cur.execute("""
            SELECT MIN(id) as id, nome, numero, MAX(posicao) as posicao
            FROM pilotos 
            WHERE sessao_id = ?
            GROUP BY nome
            ORDER BY posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]
        
        dados = []
        for p in pilotos:
            piloto_id = p.get("id")
            nome = p.get("nome", "Desconhecido")
            
            # Busca stints do piloto
            cur.execute("""
                SELECT stint_numero, tipo_pneu, volta_inicio, volta_fim, total_voltas
                FROM pneu_stints
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY stint_numero
            """, (sessao_id, piloto_id))
            
            stints = []
            for s in cur.fetchall():
                stints.append({
                    "stint_numero": s["stint_numero"],
                    "tipo_pneu": s["tipo_pneu"],
                    "volta_inicio": s["volta_inicio"],
                    "volta_fim": s["volta_fim"],
                    "total_voltas": s["total_voltas"]
                })
            
            dados.append({
                "nome": nome,
                "numero": p.get("numero"),
                "posicao": p.get("posicao"),
                "stints": stints
            })
        
        cur.connection.close()
        
        return jsonify({
            "sessao": sessao_info,
            "pilotos": dados
        })
        
    except Exception as e:
        print(f"Erro _dados_stints_por_sessao: {e}")
        return jsonify({"sessao": {}, "pilotos": []})

if __name__ == "__main__":
    print(f"[INFO] STATIC_PATH: {STATIC_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
