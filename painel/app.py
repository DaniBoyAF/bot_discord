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
    conn = sqlite3.connect('f1_telemetry.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessoes ORDER BY id DESC LIMIT 20")
    sessoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sessoes)

@app.route('/setup_manual')
def setup_manual_page():
    """Página para criar setups manualmente"""
    return render_template('setup_manual.html')

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

# ========== ENDPOINTS ==========

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
    
@app.route("/dados_setups/<int:sessao_id>")
def dados_setups(sessao_id):
    """Retorna todos os setups de uma sessão para comparação"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Seleciona todos os campos. O SQLite retornará apenas o que existir na tabela.
        cursor.execute("SELECT * FROM setups WHERE sessao_id = ?", (sessao_id,))
        setups = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
        sessao = dict(cursor.fetchone()) if cursor.rowcount != 0 else {}
        
        # Voltas por piloto (para cálculo de setores)
        cursor.execute("""
            SELECT v.piloto_id, p.nome as piloto_nome,
                   AVG(v.setor1) as avg_s1,
                   AVG(v.setor2) as avg_s2,
                   AVG(v.setor3) as avg_s3,
                   MIN(v.tempo_volta) as melhor_volta,
                   AVG(v.tempo_volta) as media_volta,
                   MAX(v.velocidade_max) as top_speed,
                   COUNT(v.id) as total_voltas
            FROM voltas v
            JOIN pilotos p ON v.piloto_id = p.id
            WHERE v.sessao_id = ? AND v.tempo_volta > 0
            GROUP BY v.piloto_id
            ORDER BY media_volta
        """, (sessao_id,))
        performance = cursor.fetchall()
        
        conn.close()
        
        pilotos = []
        for perf in performance:
            # Encontra o setup correspondente
            setup_data = next((dict(s) for s in setups if s['piloto_id'] == perf['piloto_id']), {})
            
            # Calcula consistência (desvio padrão)
            conn2 = sqlite3.connect('f1_telemetry.db')
            cur2 = conn2.cursor()
            cur2.execute("""
                SELECT tempo_volta FROM voltas 
                WHERE sessao_id = ? AND piloto_id = ? AND tempo_volta > 0
            """, (sessao_id, perf['piloto_id']))
            tempos = [r[0] for r in cur2.fetchall()]
            conn2.close()
            
            avg = perf['media_volta'] or 0
            if len(tempos) > 1 and avg > 0:
                import math
                std = math.sqrt(sum((t - avg) ** 2 for t in tempos) / len(tempos))
                consistencia = max(0, 100 - (std / avg) * 100)
            else:
                consistencia = 0
            
            # Calcula degradação
            if len(tempos) >= 3:
                n = len(tempos)
                x = list(range(n))
                x_mean = sum(x) / n
                y_mean = sum(tempos) / n
                num = sum((x[i] - x_mean) * (tempos[i] - y_mean) for i in range(n))
                den = sum((x[i] - x_mean) ** 2 for i in range(n))
                degradacao = num / den if den != 0 else 0
            else:
                degradacao = 0
            
            # Classifica tipo de setup
            combustivel = setup_data.get('combustivel_inicial', 50)
            if combustivel and combustivel < 15:
                tipo_setup = 'QUALIFYING'
            elif combustivel and combustivel < 30:
                tipo_setup = 'SHORT RUN'
            else:
                tipo_setup = 'RACE'
            
            # Classifica estilo
            if consistencia > 97:
                estilo = 'METRONOMICO'
            elif consistencia > 93:
                estilo = 'CONSISTENTE'
            elif degradacao > 0.08:
                estilo = 'AGRESSIVO'
            else:
                estilo = 'EQUILIBRADO'
            
            pilotos.append({
                'piloto_id': perf['piloto_id'],
                'nome': perf['piloto_nome'],
                'posicao': setup_data.get('posicao', 99),
                'setup': {
                    'asa_dianteira': setup_data.get('asa_dianteira', 0),
                    'asa_traseira': setup_data.get('asa_traseira', 0),
                    'diff_on': setup_data.get('diff_on_throttle', 0),
                    'diff_off': setup_data.get('diff_off_throttle', 0),
                    'freio_pressao': setup_data.get('freio_pressao', 0),
                    'freio_balanco': setup_data.get('freio_balanco', 0),
                    'suspensao_d': setup_data.get('suspensao_diant', 0),
                    'suspensao_t': setup_data.get('suspensao_tras', 0),
                    'altura_d': setup_data.get('altura_diant', 0),
                    'altura_t': setup_data.get('altura_tras', 0),
                    'pressao_fl': setup_data.get('pressao_pneu_fl', 0),
                    'pressao_fr': setup_data.get('pressao_pneu_fr', 0),
                    'pressao_rl': setup_data.get('pressao_pneu_rl', 0),
                    'pressao_rr': setup_data.get('pressao_pneu_rr', 0),
                    'combustivel': combustivel
                },
                'performance': {
                    'melhor_volta': perf['melhor_volta'],
                    'media_volta': perf['media_volta'],
                    'avg_s1': perf['avg_s1'],
                    'avg_s2': perf['avg_s2'],
                    'avg_s3': perf['avg_s3'],
                    'top_speed': perf['top_speed'],
                    'total_voltas': perf['total_voltas'],
                    'degradacao': round(degradacao, 4),
                    'consistencia': round(consistencia, 1),
                    'tipo_setup': tipo_setup,
                    'estilo': estilo
                }
            })
        
        return jsonify({
            'sessao': dict(sessao) if sessao else {},
            'pilotos': pilotos
        })
        
    except Exception as e:
        print(f"Erro dados_setups/{sessao_id}: {e}")
        return jsonify({"sessao": {}, "pilotos": []})


@app.route("/salvar_setup_manual", methods=["POST"])
def salvar_setup_manual():
    """Salva um setup digitado manualmente pelo usuário"""
    try:
        data = request.json
        if not data:
            return jsonify({"ok": False, "erro": "Dados inválidos"}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Verifica se existe uma sessão "manual" ou cria uma
        sessao_id = data.get('sessao_id')
        if not sessao_id:
            cur.execute("""
                INSERT INTO sessoes (nome_pista, tipo_sessao, total_voltas, clima)
                VALUES (?, ?, 0, 'Manual')
            """, (data.get('pista', 'Custom'), data.get('categoria', 'F1') + ' - Setup Manual'))
            sessao_id = cur.lastrowid
        
        # Cria um piloto para o setup
        cur.execute("""
            INSERT INTO pilotos (sessao_id, nome, numero, posicao)
            VALUES (?, ?, ?, 1)
        """, (sessao_id, data.get('piloto_nome', 'Piloto'), data.get('numero', 0)))
        piloto_id = cur.lastrowid
        
        # Verifica quais colunas existem na tabela setups
        cur.execute("PRAGMA table_info(setups)")
        colunas_existentes = [col[1] for col in cur.fetchall()]
        
        # Colunas base (sempre presentes)
        colunas = [
            'sessao_id', 'piloto_id', 'piloto_nome', 'pista', 'tipo_sessao',
            'asa_dianteira', 'asa_traseira',
            'diff_on_throttle', 'diff_off_throttle',
            'freio_pressao', 'freio_balanco',
            'suspensao_diant', 'suspensao_tras',
            'barra_antirrolagem_diant', 'barra_antirrolagem_tras',
            'altura_diant', 'altura_tras',
            'pressao_pneu_fl', 'pressao_pneu_fr',
            'pressao_pneu_rl', 'pressao_pneu_rr',
            'combustivel_inicial',
            'tipo_setup', 'estilo_pilotagem'
        ]
        valores = [
            sessao_id, piloto_id,
            data.get('piloto_nome', 'Piloto'),
            data.get('pista', 'Custom'),
            data.get('categoria', 'F1') + ' - ' + data.get('tipo_setup', 'RACE'),
            data.get('asa_dianteira', 0),
            data.get('asa_traseira', 0),
            data.get('diff_on', 50),
            data.get('diff_off', 50),
            data.get('freio_pressao', 100),
            data.get('freio_balanco', 50),
            data.get('suspensao_diant', 5),
            data.get('suspensao_tras', 5),
            data.get('barra_anti_diant', 5),
            data.get('barra_anti_tras', 5),
            data.get('altura_diant', 3),
            data.get('altura_tras', 5),
            data.get('pressao_fl', 23.5),
            data.get('pressao_fr', 23.5),
            data.get('pressao_rl', 22.0),
            data.get('pressao_rr', 22.0),
            data.get('combustivel', 50),
            data.get('tipo_setup', 'RACE'),
            data.get('estilo', 'EQUILIBRADO')
        ]
        
        # Adiciona campos novos se existirem no banco
        campos_novos = {
            'freio_motor': data.get('freio_motor', 100),
            'front_camber': data.get('front_camber', -3.00),
            'rear_camber': data.get('rear_camber', -1.50),
            'front_toe': data.get('front_toe', 0.05),
            'rear_toe': data.get('rear_toe', 0.20),
        }
        
        for col, val in campos_novos.items():
            if col in colunas_existentes:
                colunas.append(col)
                valores.append(val)
        
        placeholders = ', '.join(['?'] * len(colunas))
        colunas_sql = ', '.join(colunas)
        
        cur.execute(f"""
            INSERT INTO setups ({colunas_sql})
            VALUES ({placeholders})
        """, tuple(valores))
        
        conn.commit()
        conn.close()
        
        return jsonify({"ok": True, "sessao_id": sessao_id, "piloto_id": piloto_id, "msg": "Setup salvo!"})
    except Exception as e:
        print(f"Erro salvar_setup_manual: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/listar_setups_manuais")
def listar_setups_manuais():
    """Lista todos os setups salvos manualmente"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.*, se.nome_pista, se.tipo_sessao as sessao_tipo
            FROM setups s
            LEFT JOIN sessoes se ON s.sessao_id = se.id
            ORDER BY s.data_registro DESC
        """)
        setups = [dict(r) for r in cur.fetchall()]
        conn.close()
        
        return jsonify(setups)
    except Exception as e:
        print(f"Erro listar_setups_manuais: {e}")
        return jsonify([])


@app.route("/deletar_setup/<int:setup_id>", methods=["POST"])
def deletar_setup(setup_id):
    """Deleta um setup manual"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM setups WHERE id = ?", (setup_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route('/setup_editor')
def setup_editor_page():
    """Página para criar/editar setups manualmente"""
    return render_template('setup_editor.html')

if __name__ == "__main__":
    print(f"[INFO] STATIC_PATH: {STATIC_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
