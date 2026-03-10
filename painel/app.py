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

@app.route('/setup_comparison')
def setup_comparison_page():
    """Página de comparação de setups"""
    return render_template('setup_comparison.html')

@app.route('/listar_sessoes_json')
def listar_sessoes_json():
    """Retorna lista de sessões em JSON para o React"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Lista TODAS as sessões que têm pelo menos 1 setup salvo
        cursor.execute("""
            SELECT sess.id, 
                   sess.nome_pista, 
                   sess.tipo_sessao,
                   sess.total_voltas,
                   COUNT(s.id) as total_setups
            FROM sessoes sess
            INNER JOIN setups s ON s.sessao_id = sess.id
            GROUP BY sess.id
            HAVING total_setups >= 1
            ORDER BY sess.id DESC
        """)
        
        sessoes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"📋 listar_sessoes_json: {len(sessoes)} sessões com setups")
        for s in sessoes:
            print(f"   #{s['id']} - {s['nome_pista']} ({s['tipo_sessao']}) - {s['total_setups']} setups")
        
        return jsonify(sessoes)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erro listar_sessoes_json: {e}")
        return jsonify([])

@app.route('/setup_manual')
def setup_manual_page():
    """Página para criar setups manualmente"""
    return render_template('setup_manual.html')

@app.route("/api/setups_para_comparar")
def setups_para_comparar():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        sessao_id = request.args.get('sessao')
        
        if sessao_id:
            cur.execute("SELECT * FROM setups WHERE sessao_id = ? ORDER BY id DESC", (sessao_id,))
        else:
            cur.execute("SELECT * FROM setups ORDER BY id DESC LIMIT 100")
        
        setups = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return jsonify(setups)
    except Exception as e:
        print(f"Erro setups_para_comparar: {e}")
        return jsonify([])

# ========== ENDPOINTS DE DADOS ==========

@app.route("/historico_sessoes")
def historico_sessoes():
    """Lista todas as sessões do banco"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Verifica colunas existentes
        cur.execute("PRAGMA table_info(sessoes)")
        colunas = [col[1] for col in cur.fetchall()]
        
        # Monta campos dinamicamente
        campos = ["id", "nome_pista", "tipo_sessao", "data_hora", "total_voltas", "velocidade_maxima_geral"]
        
        if "nome_customizado" in colunas:
            campos.append("nome_customizado")
        
        if "clima" in colunas:
            campos.append("clima")
        
        campos_sql = ", ".join(campos)
        
        cur.execute(f"SELECT {campos_sql} FROM sessoes ORDER BY id DESC")
        
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
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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

# ========== ENDPOINTS ==========

@app.route("/dados_voltas")
def dados_voltas_live():
    """Pega a última sessão do banco"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
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
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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
    """Limpa todo o banco sem apagar o arquivo físico"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()

        tabelas = [
            "voltas",
            "pneus",
            "danos",
            "telemetria",
            "pneu_stints",
            "setups",
            "pilotos",
            "sessoes"
        ]

        for tabela in tabelas:
            try:
                cur.execute(f"DELETE FROM {tabela}")
            except Exception:
                pass

        conn.commit()
        conn.close()

        for f in os.listdir(STATIC_PATH):
            if f.startswith("sessao_") and f.endswith(".json"):
                try:
                    os.remove(os.path.join(STATIC_PATH, f))
                except Exception:
                    pass

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/dados_completos_live")
def dados_completos_live():
    """JSON: Dados completos da sessão atual - direto do banco"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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

        # Busca pilotos únicos com JOIN em pneus e danos para dados ao vivo
        cur.execute("""
            SELECT
                p.id, p.nome, p.numero, p.posicao,
                pn.tipo_pneu       AS pneu_atual,
                pn.idade_voltas    AS idade_pneu,
                d.delta_to_leader,
                d.combustivel_restante
            FROM pilotos p
            INNER JOIN (
                SELECT nome, MAX(id) as max_id
                FROM pilotos
                WHERE sessao_id = ?
                GROUP BY nome
            ) latest ON p.id = latest.max_id
            -- pneu mais recente do piloto
            LEFT JOIN pneus pn ON pn.id = (
                SELECT id FROM pneus
                WHERE sessao_id = ? AND piloto_id = p.id
                ORDER BY timestamp DESC LIMIT 1
            )
            -- dano/delta mais recente do piloto
            LEFT JOIN danos d ON d.id = (
                SELECT id FROM danos
                WHERE sessao_id = ? AND piloto_id = p.id
                ORDER BY timestamp DESC LIMIT 1
            )
            ORDER BY p.posicao
        """, (sessao_id, sessao_id, sessao_id))
        pilotos = [dict(r) for r in cur.fetchall()]

        # Volta atual = maior numero_volta registrado na sessão
        cur.execute("""
            SELECT MAX(numero_volta) as volta_atual
            FROM voltas
            WHERE sessao_id = ?
        """, (sessao_id,))
        row_volta = cur.fetchone()
        sessao_dict["volta_atual"] = row_volta["volta_atual"] if row_volta and row_volta["volta_atual"] else "-"

        # Campos de clima da tabela sessoes
        sessao_dict["temp_pista"] = sessao_dict.get("temperatura_pista") or sessao_dict.get("temp_pista") or "-"
        sessao_dict["temp_ar"]    = sessao_dict.get("temperatura_ar")   or sessao_dict.get("temp_ar")    or "-"
        sessao_dict["chance_chuva"] = sessao_dict.get("porcentagem_chuva") or sessao_dict.get("chance_chuva") or "-"
        sessao_dict["bandeira"]   = sessao_dict.get("flag") or "Verde"

        # Busca clima (se existir tabela separada)
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
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
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
    
@app.route("/dados_setups/<int:sessao_id>")
def dados_setups(sessao_id):
    """Retorna todos os setups de uma sessão para comparação"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Info da sessão
        cursor.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cursor.fetchone()
        sessao_info = dict(sessao_row) if sessao_row else {
            "id": sessao_id, "nome_pista": "Desconhecida", "tipo_sessao": "Manual"
        }
        
        # Busca todos os setups desta sessão
        cursor.execute("SELECT * FROM setups WHERE sessao_id = ? ORDER BY id", (sessao_id,))
        setups_rows = [dict(row) for row in cursor.fetchall()]
        
        print(f"📊 dados_setups/{sessao_id}: encontrou {len(setups_rows)} setups")
        
        # Transforma cada setup em um "piloto" para o frontend
        pilotos = []
        for i, s in enumerate(setups_rows):
            piloto = {
                "nome": s.get("piloto_nome") or f"Piloto {i+1}",
                "posicao": i + 1,
                "setup": {
                    "asa_dianteira": s.get("asa_dianteira") or 0,
                    "asa_traseira": s.get("asa_traseira") or 0,
                    "diff_on": s.get("diff_on_throttle") or 50,
                    "diff_off": s.get("diff_off_throttle") or 50,
                    "freio_pressao": s.get("freio_pressao") or 100,
                    "freio_balanco": s.get("freio_balanco") or 56,
                    "freio_motor": s.get("freio_motor") or 100,
                    "suspensao_d": s.get("suspensao_diant") or 15,
                    "suspensao_t": s.get("suspensao_tras") or 10,
                    "barra_anti_d": s.get("barra_antirrolagem_diant") or 8,
                    "barra_anti_t": s.get("barra_antirrolagem_tras") or 7,
                    "altura_d": s.get("altura_diant") or 20,
                    "altura_t": s.get("altura_tras") or 50,
                    "front_camber": s.get("front_camber") or -3.0,
                    "rear_camber": s.get("rear_camber") or -1.5,
                    "front_toe": s.get("front_toe") or 0.05,
                    "rear_toe": s.get("rear_toe") or 0.20,
                    "pressao_fl": s.get("pressao_pneu_fl") or 23.5,
                    "pressao_fr": s.get("pressao_pneu_fr") or 23.5,
                    "pressao_rl": s.get("pressao_pneu_rl") or 22.0,
                    "pressao_rr": s.get("pressao_pneu_rr") or 22.0,
                    "combustivel": s.get("combustivel_inicial") or 50,
                },
                "performance": {
                    "melhor_volta": s.get("melhor_volta") or 0,
                    "media_volta": s.get("media_volta") or 0,
                    "avg_s1": s.get("avg_setor1") or 0,
                    "avg_s2": s.get("avg_setor2") or 0,
                    "avg_s3": s.get("avg_setor3") or 0,
                    "top_speed": s.get("top_speed") or 0,
                    "degradacao": s.get("degradacao_media") or 0,
                    "consistencia": s.get("consistencia") or 0,
                    "total_voltas": s.get("total_voltas") or 0,
                    "tipo_setup": s.get("tipo_setup") or "RACE",
                    "estilo": s.get("estilo_pilotagem") or "MANUAL",
                }
            }
            pilotos.append(piloto)
            print(f"   Piloto: {piloto['nome']} | Asas: {piloto['setup']['asa_dianteira']}/{piloto['setup']['asa_traseira']}")
        
        conn.close()
        
        return jsonify({
            "sessao": sessao_info,
            "pilotos": pilotos
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erro dados_setups/{sessao_id}: {e}")
        return jsonify({"sessao": {}, "pilotos": [], "erro": str(e)}), 500


@app.route("/salvar_setup_manual", methods=["POST"])
def salvar_setup_manual():
    """Salva um setup digitado manualmente pelo usuário"""
    try:
        data = request.json
        if not data:
            return jsonify({"ok": False, "erro": "Dados inválidos"}), 400
        
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()
        
        # Descobre colunas existentes
        cur.execute("PRAGMA table_info(setups)")
        colunas_existentes = [col[1] for col in cur.fetchall()]
        
        # Usa sessao_id existente OU cria nova
        # Nota: por padrão não vinculamos setups manuais à sessão de corrida atual
        # a menos que o front-end envie 'attach_to_session': True
        sessao_id = data.get('sessao_id')
        attach_to_session = bool(data.get('attach_to_session', False))
        if sessao_id and not attach_to_session:
            # ignora sessao_id se não for para anexar ao evento atual
            sessao_id = None
        pista = data.get('pista', 'Custom')
        categoria = data.get('categoria', 'F1')
        
        if sessao_id:
            # Verifica se a sessão realmente existe
            cur.execute("SELECT id FROM sessoes WHERE id = ?", (sessao_id,))
            if not cur.fetchone():
                sessao_id = None
        
        if not sessao_id:
            # Procura sessão existente com mesma pista e categoria (setup manual)
            cur.execute("""
                SELECT id FROM sessoes 
                WHERE nome_pista = ? AND tipo_sessao = ? AND clima = 'Manual'
                ORDER BY id DESC LIMIT 1
            """, (pista, categoria + ' - Setup Manual'))
            row = cur.fetchone()
            
            if row:
                sessao_id = row[0]
                print(f"📌 Reutilizando sessão existente: #{sessao_id}")
            else:
                cur.execute("""
                    INSERT INTO sessoes (nome_pista, tipo_sessao, total_voltas, clima)
                    VALUES (?, ?, 0, 'Manual')
                """, (pista, categoria + ' - Setup Manual'))
                sessao_id = cur.lastrowid
                print(f"📌 Nova sessão criada: #{sessao_id}")
        
        # Cria piloto
        cur.execute("""
            INSERT INTO pilotos (sessao_id, nome, numero, posicao)
            VALUES (?, ?, ?, 1)
        """, (sessao_id, data.get('piloto_nome', 'Piloto'), data.get('numero', 0)))
        piloto_id = cur.lastrowid
        
        # Todos os campos possíveis
        todos_campos = {
            'sessao_id': sessao_id,
            'piloto_id': piloto_id,
            'piloto_nome': data.get('piloto_nome', 'Piloto'),
            'pista': pista,
            # mantém tipo_sessao consistente com sessão manual
            'tipo_sessao': categoria + ' - Setup Manual',
            'asa_dianteira': int(data.get('asa_dianteira', 0)),
            'asa_traseira': int(data.get('asa_traseira', 0)),
            'diff_on_throttle': int(data.get('diff_on', 50)),
            'diff_off_throttle': int(data.get('diff_off', 50)),
            'freio_pressao': int(data.get('freio_pressao', 100)),
            'freio_balanco': int(data.get('freio_balanco', 56)),
            'freio_motor': int(data.get('freio_motor', 100)),
            'suspensao_diant': int(data.get('suspensao_diant', 15)),
            'suspensao_tras': int(data.get('suspensao_tras', 10)),
            'barra_antirrolagem_diant': int(data.get('barra_anti_diant', 8)),
            'barra_antirrolagem_tras': int(data.get('barra_anti_tras', 7)),
            'altura_diant': int(data.get('altura_diant', 20)),
            'altura_tras': int(data.get('altura_tras', 50)),
            'front_camber': float(data.get('front_camber', -3.00)),
            'rear_camber': float(data.get('rear_camber', -1.50)),
            'front_toe': float(data.get('front_toe', 0.05)),
            'rear_toe': float(data.get('rear_toe', 0.20)),
            'pressao_pneu_fl': float(data.get('pressao_fl', 23.5)),
            'pressao_pneu_fr': float(data.get('pressao_fr', 23.5)),
            'pressao_pneu_rl': float(data.get('pressao_rl', 22.0)),
            'pressao_pneu_rr': float(data.get('pressao_rr', 22.0)),
            'combustivel_inicial': float(data.get('combustivel', 50)),
            'tipo_setup': data.get('tipo_setup', 'RACE'),
            'estilo_pilotagem': data.get('estilo', 'MANUAL'),
        }
        
        # Filtra campos que existem no banco
        campos_ok = {k: v for k, v in todos_campos.items() if k in colunas_existentes}
        
        colunas_sql = ', '.join(campos_ok.keys())
        placeholders = ', '.join(['?'] * len(campos_ok))
        valores = tuple(campos_ok.values())
        
        cur.execute(f"INSERT INTO setups ({colunas_sql}) VALUES ({placeholders})", valores)
        
        # Conta quantos setups tem na sessão
        cur.execute("SELECT COUNT(*) FROM setups WHERE sessao_id = ?", (sessao_id,))
        total = cur.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"✅ Setup salvo! sessao={sessao_id}, piloto={piloto_id}, total_na_sessao={total}")
        return jsonify({
            "ok": True, 
            "sessao_id": sessao_id, 
            "piloto_id": piloto_id, 
            "msg": f"Setup salvo! ({total} setups na sessão #{sessao_id})"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erro salvar_setup_manual: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/listar_setups_manuais")
def listar_setups_manuais():
    """Lista todos os setups salvos manualmente"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Pega colunas existentes para montar query segura
        cur.execute("PRAGMA table_info(setups)")
        colunas = [col[1] for col in cur.fetchall()]
        
        # Campos que queremos (se existirem)
        campos_desejados = [
            'id', 'sessao_id', 'piloto_nome', 'pista', 'tipo_sessao',
            'asa_dianteira', 'asa_traseira', 'tipo_setup',
            'suspensao_diant', 'suspensao_tras',
            'combustivel_inicial', 'freio_motor', 'data_registro'
        ]
        
        campos_ok = [c for c in campos_desejados if c in colunas]
        campos_sql = ', '.join(campos_ok)
        
        cur.execute(f"""
            SELECT {campos_sql}
            FROM setups
            WHERE tipo_sessao LIKE '%Setup Manual%' 
               OR estilo_pilotagem = 'MANUAL'
               OR tipo_sessao LIKE '%F1 -%'
               OR tipo_sessao LIKE '%F2 -%'
            ORDER BY id DESC
            LIMIT 50
        """)
        
        setups = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return jsonify(setups)
    except Exception as e:
        print(f"Erro listar_setups_manuais: {e}")
        return jsonify([])

@app.route("/deletar_setup/<int:setup_id>", methods=["POST"])
def deletar_setup(setup_id):
    """Deleta um setup manual"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        
        # Pega sessao_id antes de deletar
        cur.execute("SELECT sessao_id FROM setups WHERE id = ?", (setup_id,))
        row = cur.fetchone()
        
        cur.execute("DELETE FROM setups WHERE id = ?", (setup_id,))
        
        # Se a sessão ficou sem setups e é manual, deleta a sessão também
        if row:
            sessao_id = row[0]
            cur.execute("SELECT COUNT(*) FROM setups WHERE sessao_id = ?", (sessao_id,))
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("DELETE FROM sessoes WHERE id = ? AND clima = 'Manual'", (sessao_id,))
                cur.execute("DELETE FROM pilotos WHERE sessao_id = ?", (sessao_id,))
        
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route('/setup_editor')
def setup_editor_page():
    """Página para criar/editar setups manualmente"""
    return render_template('setup_editor.html')


@app.route("/api/telemetry_insights/<int:sessao_id>")
def telemetry_insights(sessao_id):
    """Retorna dados para a página Telemetry Insights - comparação entre dois pilotos"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Info sessão
        cur.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cur.fetchone()
        sessao = dict(sessao_row) if sessao_row else {}

        if not sessao:
            conn.close()
            return jsonify({"erro": "Sessão não encontrada", "sessao": {}, "pilotos": []})

        # Pilotos únicos da sessão ordenados por posição
        cur.execute("""
            SELECT p.id, p.nome, p.numero, p.posicao
            FROM pilotos p
            INNER JOIN (
                SELECT nome, MAX(id) as max_id FROM pilotos WHERE sessao_id = ? GROUP BY nome
            ) latest ON p.id = latest.max_id
            ORDER BY p.posicao
        """, (sessao_id,))
        pilotos_raw = [dict(r) for r in cur.fetchall()]

        if not pilotos_raw:
            conn.close()
            return jsonify({"sessao": sessao, "pilotos": []})

        # Verifica colunas disponíveis nas tabelas
        cur.execute("PRAGMA table_info(voltas)")
        voltas_cols = [col[1] for col in cur.fetchall()]

        cur.execute("PRAGMA table_info(pneus)")
        pneus_cols = [col[1] for col in cur.fetchall()]

        # Verifica se tabela telemetria existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetria'")
        tem_telemetria = cur.fetchone() is not None

        # Verifica se tabela danos existe (para velocidade)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='danos'")
        tem_danos = cur.fetchone() is not None

        import math

        resultado = []
        for p in pilotos_raw:
            pid = p["id"]
            nome = p["nome"]

            # ── VOLTAS ──
            # Busca todas as voltas do piloto (por sessao_id E piloto_id, OU só sessao_id + nome)
            cur.execute("""
                SELECT numero_volta, tempo_volta, setor1, setor2, setor3
                FROM voltas
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY numero_volta
            """, (sessao_id, pid))
            voltas_raw = [dict(r) for r in cur.fetchall()]

            # Se não achou por piloto_id, tenta por todos os piloto_ids com mesmo nome
            if not voltas_raw:
                cur.execute("""
                    SELECT id FROM pilotos WHERE sessao_id = ? AND nome = ?
                """, (sessao_id, nome))
                all_pids = [r[0] for r in cur.fetchall()]
                if all_pids:
                    placeholders = ",".join("?" * len(all_pids))
                    cur.execute(f"""
                        SELECT numero_volta, tempo_volta, setor1, setor2, setor3
                        FROM voltas
                        WHERE sessao_id = ? AND piloto_id IN ({placeholders})
                        ORDER BY numero_volta
                    """, [sessao_id] + all_pids)
                    voltas_raw = [dict(r) for r in cur.fetchall()]

            # Filtra voltas válidas (tempo > 10s, ignora outlap/inlap)
            voltas = []
            for v in voltas_raw:
                t = v.get("tempo_volta")
                if t is not None and t > 10:
                    voltas.append(v)

            tempos = [v["tempo_volta"] for v in voltas if v["tempo_volta"]]
            s1_list = [v["setor1"] for v in voltas if v["setor1"] and v["setor1"] > 0]
            s2_list = [v["setor2"] for v in voltas if v["setor2"] and v["setor2"] > 0]
            s3_list = [v["setor3"] for v in voltas if v["setor3"] and v["setor3"] > 0]

            melhor = min(tempos) if tempos else 0
            media = sum(tempos) / len(tempos) if tempos else 0

            # Remove outliers (> media * 1.08)
            limpo = [t for t in tempos if t < media * 1.08] if media else tempos
            media_limpa = sum(limpo) / len(limpo) if limpo else media

            # Consistência
            if len(limpo) > 1:
                dp = math.sqrt(sum((t - media_limpa) ** 2 for t in limpo) / len(limpo))
                consistencia = max(0, round(100 - (dp / media_limpa * 100), 1))
            else:
                consistencia = 0.0

            # Degradação (slope)
            degradacao = 0.0
            if len(limpo) >= 3:
                n = len(limpo)
                x_mean = (n - 1) / 2
                y_mean = sum(limpo) / n
                num = sum((i - x_mean) * (limpo[i] - y_mean) for i in range(n))
                den = sum((i - x_mean) ** 2 for i in range(n))
                degradacao = round(num / den, 4) if den else 0.0

            # ── TOP SPEED ──
            top_speed = 0
            # Tenta telemetria
            if tem_telemetria:
                try:
                    cur.execute("PRAGMA table_info(telemetria)")
                    tel_cols = [c[1] for c in cur.fetchall()]
                    speed_col = None
                    for candidate in ['velocidade', 'speed', 'top_speed', 'velocidade_maxima']:
                        if candidate in tel_cols:
                            speed_col = candidate
                            break
                    if speed_col:
                        cur.execute(f"""
                            SELECT MAX({speed_col}) as max_speed
                            FROM telemetria
                            WHERE sessao_id = ? AND piloto_id = ?
                        """, (sessao_id, pid))
                        row = cur.fetchone()
                        if row and row["max_speed"]:
                            top_speed = float(row["max_speed"])
                except Exception:
                    pass

            # Fallback: tenta danos (alguns projetos gravam velocidade lá)
            if top_speed == 0 and tem_danos:
                try:
                    cur.execute("PRAGMA table_info(danos)")
                    danos_cols = [c[1] for c in cur.fetchall()]
                    for candidate in ['velocidade', 'speed', 'top_speed']:
                        if candidate in danos_cols:
                            cur.execute(f"""
                                SELECT MAX({candidate}) as max_speed
                                FROM danos
                                WHERE sessao_id = ? AND piloto_id = ?
                            """, (sessao_id, pid))
                            row = cur.fetchone()
                            if row and row["max_speed"]:
                                top_speed = float(row["max_speed"])
                                break
                except Exception:
                    pass

            # Fallback: sessão velocidade_maxima_geral
            if top_speed == 0:
                top_speed = float(sessao.get("velocidade_maxima_geral") or 0)

            # ── SETORES MÉDIOS ──
            avg_s1 = round(sum(s1_list) / len(s1_list), 3) if s1_list else 0
            avg_s2 = round(sum(s2_list) / len(s2_list), 3) if s2_list else 0
            avg_s3 = round(sum(s3_list) / len(s3_list), 3) if s3_list else 0
            best_s1 = round(min(s1_list), 3) if s1_list else 0
            best_s2 = round(min(s2_list), 3) if s2_list else 0
            best_s3 = round(min(s3_list), 3) if s3_list else 0

            # ── PNEU ──
            pneu = {}
            try:
                cur.execute("""
                    SELECT * FROM pneus
                    WHERE sessao_id = ? AND piloto_id = ?
                    ORDER BY id DESC LIMIT 1
                """, (sessao_id, pid))
                pneu_row = cur.fetchone()
                if pneu_row:
                    pneu = dict(pneu_row)
            except Exception:
                pass

            # ── MONTA VOLTAS PARA FRONTEND ──
            voltas_frontend = []
            for v in voltas:
                voltas_frontend.append({
                    "n": v["numero_volta"],
                    "t": v["tempo_volta"],
                    "s1": v["setor1"] if v["setor1"] and v["setor1"] > 0 else None,
                    "s2": v["setor2"] if v["setor2"] and v["setor2"] > 0 else None,
                    "s3": v["setor3"] if v["setor3"] and v["setor3"] > 0 else None,
                })

            resultado.append({
                "id": pid,
                "nome": nome,
                "numero": p["numero"],
                "posicao": p["posicao"],
                "melhor_volta": round(melhor, 3),
                "media_volta": round(media_limpa, 3),
                "consistencia": consistencia,
                "degradacao": degradacao,
                "top_speed": round(top_speed, 1),
                "avg_s1": avg_s1,
                "avg_s2": avg_s2,
                "avg_s3": avg_s3,
                "best_s1": best_s1,
                "best_s2": best_s2,
                "best_s3": best_s3,
                "total_voltas": len(tempos),
                "voltas": voltas_frontend,
                "pneu": pneu,
            })

        conn.close()

        # Debug
        for r in resultado:
            print(f"📊 {r['nome']}: {r['total_voltas']} voltas, best={r['melhor_volta']}, avg={r['media_volta']}, s1={r['avg_s1']}, s2={r['avg_s2']}, s3={r['avg_s3']}")

        return jsonify({"sessao": sessao, "pilotos": resultado})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"erro": str(e), "sessao": {}, "pilotos": []}), 500


@app.route("/Comparar")
def telemetry_insights_page():
    return render_template("Comparar.html")

if __name__ == "__main__":
    print(f"[INFO] STATIC_PATH: {STATIC_PATH}")
    print()
    print("🚀 Servidor rodando!")
    print("Acesse: http://localhost:5000/")
    print("=" * 50)
    print()
    app.run(host="0.0.0.0", port=5000, debug=True)