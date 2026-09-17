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

@app.route("/surpresa")
def surpresa_page():
    return render_template("surpresa.html")

@app.route("/painel")
def painel():
    return render_template("painel.html")

@app.route("/tyres")
def tyres_page():
    return render_template("Tyre_hub.html")

@app.route("/mapa")
def mapa_page():
    return render_template("mapa.html")

@app.route('/setup_comparison')
def setup_comparison_page():
    return render_template('setup_comparison.html')

@app.route('/listar_sessoes_json')
def listar_sessoes_json():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(sessoes)")
        colunas = [col[1] for col in cur.fetchall()]

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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(sessoes)")
        _cols_sess = [c[1] for c in cur.fetchall()]

        _campos_sess = ["total_voltas"]
        for _c in ("delta_lider", "nome_pista", "tipo_sessao", "clima"):
            if _c in _cols_sess:
                _campos_sess.append(_c)
        cur.execute(
            f"SELECT {', '.join(_campos_sess)} FROM sessoes WHERE id = ?",
            (sessao_id,)
        )
        sessao_row = cur.fetchone()
        total_voltas_sessao = sessao_row["total_voltas"] if sessao_row else 0

        sessao_extra = {}
        if sessao_row:
            for _k in sessao_row.keys():
                sessao_extra[_k] = sessao_row[_k]

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
                "total_voltas_piloto": total_voltas_piloto
            })

        conn.close()

        return jsonify({
            "total_voltas_sessao": total_voltas_sessao,
            "sessao": sessao_extra,  
            "pilotos": dados
        })
    except Exception as e:
        print(f"Erro ao buscar dados_voltas: {e}")
        return jsonify({"total_voltas_sessao": 0, "sessao": {}, "pilotos": []})

@app.route("/dados_pneus/<int:sessao_id>")
def dados_pneus(sessao_id):
    dados = carregar_json(f"sessao_{sessao_id}_pneus.json")
    if dados:
        return jsonify(dados.get("pilotos", []))
    return jsonify([])

@app.route("/dados_danos/<int:sessao_id>")
def dados_danos(sessao_id):
    dados = carregar_json(f"sessao_{sessao_id}_danos.json")
    if dados:
        return jsonify(dados.get("pilotos", []))
    return jsonify([])

@app.route("/dados_completos/<int:sessao_id>")
def dados_completos(sessao_id):
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
    try:
        from Bot.jogadores import JOGADORES
        from utils.dictionnaries import tyres_dictionnary

        dados = []
        for idx, piloto in enumerate(JOGADORES):
            nome = getattr(piloto, 'name', '')
            if not nome or nome.strip() == '':
                continue

            pneu_stints = getattr(piloto, 'pneu_stints', [])

            stints = []
            for stint in pneu_stints:
                stints.append({
                    "tipo_pneu": stint.get("composto", "MEDIUM"),
                    "volta_inicio": stint.get("volta_inicio", 1),
                    "volta_fim": stint.get("volta_fim", 0),
                    "total_voltas": stint.get("total_voltas", 0)
                })

            tyres_code = getattr(piloto, 'tyres', 17)
            tyres_name = tyres_dictionnary.get(tyres_code, "MEDIUM")

            num_laps = getattr(piloto, 'num_laps', 0) or getattr(piloto, 'currentLapNum', 0)

            dados.append({
                "nome": nome,
                "numero": getattr(piloto, 'numero', idx),
                "position": getattr(piloto, 'position', idx + 1),
                "tyres": tyres_name,
                "num_laps": num_laps,
                "stints": stints
            })

        dados.sort(key=lambda x: x.get('position', 99))

        return jsonify(dados)
    except Exception as e:
        print(f"Erro dados_pra_o_painel: {e}")
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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()

        tabelas_com_sessao = ["voltas", "pneus", "danos", "telemetria", "pneu_stints", "setups", "pilotos"]

        for tabela in tabelas_com_sessao:
            try:
                cur.execute(f"DELETE FROM {tabela} WHERE sessao_id = ?", (sessao_id,))
            except Exception as e:
                print(f"⚠️ Erro ao limpar {tabela}: {e}")

        cur.execute("DELETE FROM sessoes WHERE id = ?", (sessao_id,))

        conn.commit()
        conn.close()

        for suffix in ["_voltas.json", "_pneus.json", "_danos.json"]:
            json_path = os.path.join(STATIC_PATH, f"sessao_{sessao_id}{suffix}")
            if os.path.exists(json_path):
                try:
                    os.remove(json_path)
                except Exception:
                    pass

        return jsonify({"ok": True, "mensagem": f"Sessão {sessao_id} excluída"})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/apagar_db", methods=["POST"])
def apagar_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()

        tabelas = ["voltas", "pneus", "danos", "telemetria", "pneu_stints", "setups", "pilotos", "sessoes"]

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
    """
    JSON unificado da sessão atual.
    Tenta primeiro os dados AO VIVO (Bot.jogadores.JOGADORES + SESSION).
    Se não houver parser rodando, cai no último snapshot do banco.
    """
    live_ok = False
    pilotos_live = []
    sessao_live = {}
    lideres_live = {}
    session_bests = {"lap": None, "s1": None, "s2": None, "s3": None}

    try:
        from Bot.jogadores import JOGADORES
        from Bot.Session import SESSION
        from utils.dictionnaries import (
            tyres_dictionnary, teams_name_dictionary, teams_color_dictionary,
            session_dictionary,
        )

        def _fmt(t):
            if t is None or t == 0:
                return None
            try:
                return round(float(t), 3)
            except Exception:
                return None

        def _get_weather_sample():
            amostras = getattr(SESSION, "m_weatherForecastSamples", None)
            if amostras is None:
                amostras = getattr(SESSION, "m_weather_forecast_samples", None)
            if not amostras:
                return None
            try:
                return amostras[0]
            except (IndexError, TypeError):
                return None

        def _get_rain_percent():
            amostra = _get_weather_sample()
            if amostra is None:
                return 0
            return getattr(amostra, "m_rainPercentage",
                    getattr(amostra, "m_rain_percentage", 0)) or 0

        max_lap = 0
        for _p in JOGADORES:
            _n = getattr(_p, 'current_lap_num', 0) or 0
            if _n > max_lap:
                max_lap = _n

        # ── Bandeira ─────────────────────────────────────────
        _zonas = getattr(SESSION, "m_marshalZones", None)
        if _zonas is None:
            _zonas = getattr(SESSION, "m_marshal_zones", None)

        _flag_id = -1
        if _zonas:
            try:
                _zona = _zonas[0]
                _flag_id = getattr(_zona, "m_zoneFlag",
                            getattr(_zona, "m_zone_flag", -1))
            except (IndexError, TypeError):
                _flag_id = -1

        _flag_map = {
            -1: "Desconhecida",
             0: "Nenhuma",
             1: "Verde",
             2: "Azul",
             3: "Amarela",
             4: "Vermelha",
        }
        _flag_raw = _flag_map.get(_flag_id, "Verde")

        # ── Tipo de sessão ────────────────────────────────────
        _stype_code = getattr(SESSION, 'm_session_type', None)
        if _stype_code is None:
            _stype_code = -1
        try:
            _stype_code = int(_stype_code)
        except (TypeError, ValueError):
            _stype_code = -1
        _stype_name = session_dictionary.get(_stype_code, "Sessão")

        # ── Fórmula (F1 / F2) ─────────────────────────────────
        try:
            _formula_code = int(getattr(SESSION, 'm_formula', 0) or 0)
        except Exception:
            _formula_code = 0
        _formula_name = "F2" if _formula_code == 2 else "F1"

        _track = getattr(SESSION, 'track_name', None)
        if not _track or str(_track).strip() in ("", "—", "Desconhecida", "DESCONHECIDA"):
            _track = "—"

        _total_laps = getattr(SESSION, 'm_total_laps', 0) or 0

        _amostra = _get_weather_sample()

        _temp_pista = (getattr(_amostra, 'm_track_temperature', None)
                       if _amostra is not None else None)
        if _temp_pista in (None, 0, ""):
            _temp_pista = getattr(SESSION, 'm_track_temperature', None) or "—"

        _temp_ar = (getattr(_amostra, 'm_air_temperature', None)
                    if _amostra is not None else None)
        if _temp_ar in (None, 0, ""):
            _temp_ar = getattr(SESSION, 'm_air_temperature', None) or "—"

        sessao_live = {
            "id":            getattr(SESSION, 'id', None),
            "nome_pista":    _track,
            "tipo_sessao":   _stype_name,
            "total_voltas":  _total_laps,
            "volta_atual":   max_lap,
            "temp_pista":    _temp_pista,
            "temp_ar":       _temp_ar,
            "chance_chuva":  _get_rain_percent(),
            "bandeira":      _flag_raw,
            "clima":         getattr(SESSION, 'weather', '—') or "—",
            "sc_status":     getattr(SESSION, 'SafetyCarStatus', 'Nenhum') or "Nenhum",
            "flag":          _flag_raw,
            "formula":       _formula_code,
            "formula_name":  _formula_name,
        }

        for idx, p in enumerate(JOGADORES):
            nome = (getattr(p, 'name', '') or '').strip()
            if not nome:
                continue

            voltas_all = getattr(p, 'todas_voltas_setores', []) or []
            validas = [v for v in voltas_all
                       if v.get('tempo_total') and v['tempo_total'] > 10]

            best_lap_p = None
            best_s1_p = best_s2_p = best_s3_p = None
            if validas:
                best_lap_p = min(v['tempo_total'] for v in validas)
                s1s = [v['setores'][0] for v in validas
                       if v.get('setores') and v['setores'][0] and v['setores'][0] > 5]
                s2s = [v['setores'][1] for v in validas
                       if v.get('setores') and v['setores'][1] and v['setores'][1] > 5]
                s3s = [v['setores'][2] for v in validas
                       if v.get('setores') and v['setores'][2] and v['setores'][2] > 5]
                best_s1_p = min(s1s) if s1s else None
                best_s2_p = min(s2s) if s2s else None
                best_s3_p = min(s3s) if s3s else None

            ultima_com_setores = None
            for v in reversed(voltas_all):
                setores = v.get('setores') or []
                if any(s is not None and s > 0 for s in setores):
                    ultima_com_setores = v
                    break

            last = validas[-1] if validas else None

            best_lap_calc = _fmt(best_lap_p) or _fmt(getattr(p, 'bestLapTime', None))
            last_lap = _fmt(last['tempo_total']) if last else _fmt(getattr(p, 'lastLapTime', None))

            last_s1 = None
            last_s2 = None
            last_s3 = None
            if ultima_com_setores and ultima_com_setores.get('setores'):
                _set = ultima_com_setores['setores']
                last_s1 = _fmt(_set[0]) if len(_set) > 0 else None
                last_s2 = _fmt(_set[1]) if len(_set) > 1 else None
                last_s3 = _fmt(_set[2]) if len(_set) > 2 else None

            tyre = getattr(p, 'tyre_type', None)
            if not tyre:
                tyre_code = getattr(p, 'tyres', 17)
                try:
                    tyre_code = int(tyre_code)
                except Exception:
                    tyre_code = 17
                tyre = tyres_dictionnary.get(tyre_code, "Médio")
            else:
                try:
                    tyre_code = int(getattr(p, 'tyres', 17))
                except Exception:
                    tyre_code = 17

            tyre_age = int(getattr(p, 'tyresAgeLaps', 0) or 0)

            team_id = getattr(p, 'm_team_id', -1)
            team_name = getattr(p, 'team_name', None) or teams_name_dictionary.get(team_id, "?")
            team_color = teams_color_dictionary.get(team_id, "#888888")

            try:
                speed = int(getattr(p, 'speed_trap', 0) or 0)
            except Exception:
                speed = 0

            delta = getattr(p, 'delta_to_leader', None)
            if isinstance(delta, str):
                delta = None

            # ── Desgaste / temperaturas / danos / combustível ──
            tyre_wear_raw = getattr(p, 'tyre_wear', [0, 0, 0, 0]) or [0, 0, 0, 0]
            if isinstance(tyre_wear_raw, tuple):
                tyre_wear_raw = list(tyre_wear_raw)
            while len(tyre_wear_raw) < 4:
                tyre_wear_raw.append(0)
            tw = [float(x or 0) for x in tyre_wear_raw[:4]]

            ti = list(getattr(p, 'tyres_temp_inner', [0,0,0,0]) or [0,0,0,0])
            ts = list(getattr(p, 'tyres_temp_surface', [0,0,0,0]) or [0,0,0,0])
            while len(ti) < 4: ti.append(0)
            while len(ts) < 4: ts.append(0)

            dano_asa_e = float(getattr(p, 'FrontLeftWingDamage',  0) or 0)
            dano_asa_d = float(getattr(p, 'FrontRightWingDamage', 0) or 0)
            dano_asa_t = float(getattr(p, 'rearWingDamage',       0) or 0)
            dano_assoa = float(getattr(p, 'floorDamage',          0) or 0)
            dano_difus = float(getattr(p, 'diffuserDamage',       0) or 0)
            dano_sidep = float(getattr(p, 'sidepodDamage',        0) or 0)

            try:
                fuel_kg   = float(getattr(p, 'fuel_in_tank', 0) or 0)
                fuel_cap  = float(getattr(p, 'fuel_capacity', 0) or 0)
                fuel_laps = float(getattr(p, 'fuel_remaining_laps', 0) or 0)
            except Exception:
                fuel_kg = fuel_cap = fuel_laps = 0.0

            try:
                ers_j  = float(getattr(p, 'ers_store_energy', 0) or 0)
                ers_pct = min(100.0, max(0.0, round(ers_j / 4_000_000 * 100, 1)))
            except Exception:
                ers_pct = 0.0

            # ── 🆕 DRS — 3 estados ─────────────────────────────
            drs_ativo      = bool(getattr(p, 'drs', 0))                     # aberto agora
            drs_disponivel = bool(getattr(p, 'drs_allowed', 0))             # dentro da zona
            drs_distancia  = int(getattr(p, 'drs_activation_distance', 0) or 0)

            pilotos_live.append({
                "idx":         idx,
                "nome":        nome,
                "numero":      getattr(p, 'numero', None),
                "posicao":     getattr(p, 'position', None),
                "equipe":      team_name,
                "team_id":     team_id,
                "team_color":  team_color,

                "best_lap":    best_lap_calc,
                "last_lap":    last_lap,
                "s1":          last_s1,
                "s2":          last_s2,
                "s3":          last_s3,
                "best_s1":     _fmt(best_s1_p),
                "best_s2":     _fmt(best_s2_p),
                "best_s3":     _fmt(best_s3_p),

                "speed":       speed,
                "tyre":        tyre,
                "tyre_code":   tyre_code,
                "tyre_age":    tyre_age,
                "is_pit":      bool(getattr(p, 'pit', False)),

                "delta_to_leader": delta,

                "pneu_atual":  tyre,
                "idade_pneu":  tyre_age,

                "s1_atual":    last_s1,
                "s2_atual":    last_s2,
                "s3_atual":    last_s3,

                "tyre_wear":          tw,
                "tyre_temp_inner":    [float(x) for x in ti[:4]],
                "tyre_temp_surface":  [float(x) for x in ts[:4]],
                "dano_asa_esquerda":  dano_asa_e,
                "dano_asa_direita":   dano_asa_d,
                "dano_asa_traseira":  dano_asa_t,
                "dano_assoalho":      dano_assoa,
                "dano_difusor":       dano_difus,
                "dano_sidepods":      dano_sidep,
                "fuel":               fuel_kg,
                "fuel_capacity":      fuel_cap,
                "fuel_laps":          fuel_laps,
                "ers_pct":            ers_pct,

                # 🆕 DRS — 3 campos
                "drs":                     drs_ativo,
                "drs_allowed":             drs_disponivel,
                "drs_activation_distance": drs_distancia,

                "current_lap":        int(getattr(p, 'current_lap_num', 0) or 0),
            })

        if pilotos_live:
            bl  = [x['best_lap'] for x in pilotos_live if x['best_lap']]
            bs1 = [x['best_s1']  for x in pilotos_live if x['best_s1']]
            bs2 = [x['best_s2']  for x in pilotos_live if x['best_s2']]
            bs3 = [x['best_s3']  for x in pilotos_live if x['best_s3']]
            sb_lap = min(bl)  if bl  else None
            sb_s1  = min(bs1) if bs1 else None
            sb_s2  = min(bs2) if bs2 else None
            sb_s3  = min(bs3) if bs3 else None
            session_bests = {"lap": sb_lap, "s1": sb_s1, "s2": sb_s2, "s3": sb_s3}

            pilotos_live.sort(key=lambda x: (x['posicao'] is None,
                                             x['posicao'] if x['posicao'] else 999))

            for i, x in enumerate(pilotos_live):
                d = x['delta_to_leader']
                if isinstance(d, (int, float)) and d > 0:
                    x['gap'] = round(float(d), 3)
                elif x['best_lap'] and sb_lap:
                    x['gap'] = round(x['best_lap'] - sb_lap, 3)
                else:
                    x['gap'] = None

                if i == 0:
                    x['interval'] = 0.0
                else:
                    prev = pilotos_live[i-1]
                    if x['gap'] is not None and prev['gap'] is not None:
                        x['interval'] = round(x['gap'] - prev['gap'], 3)
                    else:
                        x['interval'] = None

            for x in pilotos_live:
                x['is_sb_lap'] = bool(sb_lap and x['best_lap'] and abs(x['best_lap'] - sb_lap) < 0.001)
                x['is_sb_s1']  = bool(sb_s1  and x['best_s1']  and abs(x['best_s1']  - sb_s1)  < 0.001)
                x['is_sb_s2']  = bool(sb_s2  and x['best_s2']  and abs(x['best_s2']  - sb_s2)  < 0.001)
                x['is_sb_s3']  = bool(sb_s3  and x['best_s3']  and abs(x['best_s3']  - sb_s3)  < 0.001)

            for key, sbest in (("s1", sb_s1), ("s2", sb_s2), ("s3", sb_s3)):
                if sbest is None:
                    continue
                for x in pilotos_live:
                    if x[f"best_{key}"] and abs(x[f"best_{key}"] - sbest) < 0.001:
                        lideres_live[key] = {
                            "nome":       x['nome'],
                            "numero":     x['numero'],
                            "pos":        x['posicao'],
                            "tempo":      x[f"best_{key}"],
                            "team_color": x['team_color'],
                        }
                        break

            live_ok = True

    except Exception as e:
        print(f"⚠️ live_timing indisponível ({e}) — caindo no banco")

    if not live_ok:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT * FROM sessoes ORDER BY id DESC LIMIT 1")
            sessao = cur.fetchone()
            if not sessao:
                conn.close()
                return jsonify({
                    "pilotos": [], "clima": {}, "sessao": {},
                    "lideres_setor": lideres_live,
                    "session_bests": session_bests,
                    "fonte": "vazio",
                })

            sessao_id = sessao["id"]
            sessao_dict = dict(sessao)
            sessao_dict["formula_name"] = "F1"   # fallback

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
                LEFT JOIN pneus pn ON pn.id = (
                    SELECT id FROM pneus
                    WHERE sessao_id = ? AND piloto_id = p.id
                    ORDER BY timestamp DESC LIMIT 1
                )
                LEFT JOIN danos d ON d.id = (
                    SELECT id FROM danos
                    WHERE sessao_id = ? AND piloto_id = p.id
                    ORDER BY timestamp DESC LIMIT 1
                )
                ORDER BY p.posicao
            """, (sessao_id, sessao_id, sessao_id))
            pilotos_db = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT MAX(numero_volta) as v FROM voltas WHERE sessao_id = ?", (sessao_id,))
            r = cur.fetchone()
            sessao_dict["volta_atual"] = r["v"] if r and r["v"] else 0

            sessao_dict["temp_pista"]   = sessao_dict.get("temperatura_pista") or sessao_dict.get("temp_pista") or "—"
            sessao_dict["temp_ar"]      = sessao_dict.get("temperatura_ar")   or sessao_dict.get("temp_ar")    or "—"
            sessao_dict["chance_chuva"] = sessao_dict.get("porcentagem_chuva") or sessao_dict.get("chance_chuva") or 0
            sessao_dict["bandeira"]     = sessao_dict.get("flag") or "Verde"

            for p in pilotos_db:
                p["best_lap"]   = None
                p["last_lap"]   = None
                p["s1"] = p["s2"] = p["s3"] = None
                p["best_s1"] = p["best_s2"] = p["best_s3"] = None
                p["s1_atual"] = p["s2_atual"] = p["s3_atual"] = None
                p["speed"]      = 0
                p["tyre"]       = p.get("pneu_atual") or "Médio"
                p["tyre_age"]   = p.get("idade_pneu") or 0
                p["gap"]        = None
                p["interval"]   = None
                p["is_sb_lap"]  = False
                p["is_sb_s1"]   = False
                p["is_sb_s2"]   = False
                p["is_sb_s3"]   = False
                p["is_pit"]     = False
                p["team_color"] = "#666666"
                p["tyre_wear"]         = [0, 0, 0, 0]
                p["tyre_temp_inner"]   = [0, 0, 0, 0]
                p["tyre_temp_surface"] = [0, 0, 0, 0]
                p["dano_asa_esquerda"] = 0
                p["dano_asa_direita"]  = 0
                p["dano_asa_traseira"] = 0
                p["dano_assoalho"]     = 0
                p["dano_difusor"]      = 0
                p["dano_sidepods"]     = 0
                p["fuel"]              = 0
                p["fuel_capacity"]     = 0
                p["fuel_laps"]         = 0
                p["ers_pct"]           = 0

                # 🆕 DRS — 3 campos no fallback também
                p["drs"]                     = False
                p["drs_allowed"]             = False
                p["drs_activation_distance"] = 0

            clima = {}
            try:
                cur.execute("PRAGMA table_info(clima)")
                if cur.fetchall():
                    cur.execute("SELECT * FROM clima WHERE sessao_id = ? ORDER BY id DESC LIMIT 1", (sessao_id,))
                    cr = cur.fetchone()
                    if cr:
                        clima = dict(cr)
            except Exception:
                pass

            conn.close()

            return jsonify({
                "pilotos":       pilotos_db,
                "clima":         clima,
                "sessao":        sessao_dict,
                "lideres_setor": lideres_live,
                "session_bests": session_bests,
                "fonte":         "banco",
            })

        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({
                "pilotos": [], "clima": {}, "sessao": {},
                "lideres_setor": lideres_live,
                "session_bests": session_bests,
                "erro": str(e),
                "fonte": "erro",
            }), 500

    clima_live = {"condicao": sessao_live.get("clima", "—")}

    return jsonify({
        "pilotos":       pilotos_live,
        "clima":         clima_live,
        "sessao":        sessao_live,
        "lideres_setor": lideres_live,
        "session_bests": session_bests,
        "fonte":         "live",
    })

@app.route("/api/mapa_posicoes")
def api_mapa_posicoes():
    try:
        from Bot.jogadores import JOGADORES
        from Bot.Session import SESSION
        from utils.dictionnaries import (
            teams_color_dictionary, teams_name_dictionary,
            tyres_dictionnary, session_dictionary, track_dictionary, pit_dictionary
        )
        from dados.map_performance import carros_dados

        # ── Bandeira: hex → nome ──────────────────────────────
        flag_raw = getattr(SESSION, 'flag', 'Verde')
        if isinstance(flag_raw, str) and flag_raw.startswith('#'):
            flag_map = {
                "#FFFFFF": "Nenhuma", "#00FF00": "Verde",
                "#0000FF": "Azul",    "#FFD700": "Amarela",
                "#FF0000": "Vermelha",
            }
            flag_raw = flag_map.get(flag_raw.upper(), "Verde")

        # ── Tipo de sessão ─────────────────────────────────────
        sess_type_code = getattr(SESSION, 'm_session_type', None)
        sess_type_code = -1 if sess_type_code is None else sess_type_code
        try:
            sess_type_code = int(sess_type_code)
        except (TypeError, ValueError):
            sess_type_code = -1
        sess_type_name = session_dictionary.get(sess_type_code, "Sessão")

        # ── Volta atual ───────────────────────────────────────
        max_lap = 0
        for p in JOGADORES:
            n = getattr(p, 'current_lap_num', 0) or 0
            if n > max_lap:
                max_lap = n

        total_laps = getattr(SESSION, 'm_total_laps', 0) or 0
        session_time_left = int(getattr(SESSION, 'm_session_time_left', 0) or 0)
        formula_code = int(getattr(SESSION, 'm_formula', 0) or 0)
        formula_name = "F2" if formula_code == 2 else "F1"

        # ── Nome da pista ──────────────────────────────────────
        track = getattr(SESSION, 'track_name', None)
        if not track or str(track).strip().lower() in ("", "unknown", "desconhecida", "—"):
            try:
                tid = getattr(SESSION, 'm_track_id', -1)
                if tid is not None and tid in track_dictionary:
                    track = str(track_dictionary[tid][0]).replace('_', ' ').title()
            except Exception:
                pass
        if not track or str(track).strip().lower() in ("", "unknown", "desconhecida", "—"):
            track = "—"

        # ── Clima ─────────────────────────────────────────────
        _amostra = None
        amostras = getattr(SESSION, "m_weatherForecastSamples", None)
        if amostras is None:
            amostras = getattr(SESSION, "m_weather_forecast_samples", None)
        if amostras:
            try:
                _amostra = amostras[0]
            except (IndexError, TypeError):
                _amostra = None

        def _samp(attr, fallback=None):
            if _amostra is not None:
                v = getattr(_amostra, attr, None)
                if v not in (None, ""):
                    return v
            return fallback

        temp_pista = _samp("m_track_temperature") or getattr(SESSION, 'm_track_temperature', None) or "—"
        temp_ar    = _samp("m_air_temperature")   or getattr(SESSION, 'm_air_temperature', None)   or "—"
        clima      = getattr(SESSION, 'weather', '—') or "—"
        sc_status  = getattr(SESSION, 'SafetyCarStatus', 'Nenhum') or "Nenhum"

        def _get_rain_percent():
            rp = getattr(SESSION, 'rainPercentage', None)
            if rp is not None and rp != "":
                try:
                    return int(rp)
                except (TypeError, ValueError):
                    pass
            amostras = (getattr(SESSION, "m_weatherForecastSamples", None)
                        or getattr(SESSION, "m_weather_forecast_samples", None))
            if amostras:
                try:
                    amostra = amostras[0]
                    v = (getattr(amostra, "m_rain_percentage", None)
                         if getattr(amostra, "m_rain_percentage", None) is not None
                         else getattr(amostra, "m_rainPercentage", None))
                    if v is not None:
                        return int(v)
                except (IndexError, TypeError, ValueError):
                    pass
            return 0

        # ── Loop dos pilotos ──────────────────────────────────
        pilotos_raw = []
        for idx, p in enumerate(JOGADORES):
            nome = (getattr(p, 'name', '') or '').strip()
            if not nome:
                continue

            # Posição no mapa
            x, z, has_pos = 0.0, 0.0, False
            pos_list = carros_dados.get(idx)
            if pos_list:
                try:
                    ultimo = pos_list[-1]
                    if isinstance(ultimo, (list, tuple)) and len(ultimo) >= 3:
                        x = float(ultimo[0])
                        z = float(ultimo[1])
                        has_pos = True
                except (TypeError, ValueError, IndexError):
                    pass

            team_id = getattr(p, 'm_team_id', -1)

            # ── Pneu ──
            tyre_name = getattr(p, 'tyre_type', None)
            if not tyre_name:
                code = getattr(p, 'tyres', None)
                try:
                    code = int(code) if code is not None else None
                except Exception:
                    code = None
                tyre_name = tyres_dictionnary.get(code, "Médio") if code is not None else "Médio"

            # ── Desgaste ──
            tw = list(getattr(p, 'tyre_wear', [0, 0, 0, 0]) or [0, 0, 0, 0])
            while len(tw) < 4:
                tw.append(0)
            tw = [float(v or 0) for v in tw[:4]]

            # ── Temperaturas ──
            ti = list(getattr(p, 'tyres_temp_inner',   [0, 0, 0, 0]) or [0, 0, 0, 0])
            ts = list(getattr(p, 'tyres_temp_surface', [0, 0, 0, 0]) or [0, 0, 0, 0])
            while len(ti) < 4: ti.append(0)
            while len(ts) < 4: ts.append(0)
            ti = [float(v or 0) for v in ti[:4]]
            ts = [float(v or 0) for v in ts[:4]]

            # ── Freios ──
            try:
                bt = list(getattr(p, 'brakes_temperature', [0, 0, 0, 0]) or [0, 0, 0, 0])
                while len(bt) < 4: bt.append(0)
                bt = [float(v or 0) for v in bt[:4]]
            except Exception:
                bt = [0, 0, 0, 0]

            # ── Danos ──
            dano_e = float(getattr(p, 'FrontLeftWingDamage',  0) or 0)
            dano_d = float(getattr(p, 'FrontRightWingDamage', 0) or 0)
            dano_t = float(getattr(p, 'rearWingDamage',       0) or 0)
            dano_a = float(getattr(p, 'floorDamage',          0) or 0)
            dano_f = float(getattr(p, 'diffuserDamage',       0) or 0)
            dano_s = float(getattr(p, 'sidepodDamage',        0) or 0)

            # ── Fuel / ERS ──
            try:
                fuel_kg   = float(getattr(p, 'fuel_in_tank', 0) or 0)
                fuel_cap  = float(getattr(p, 'fuel_capacity', 0) or 0)
                fuel_laps = float(getattr(p, 'fuel_remaining_laps', 0) or 0)
            except Exception:
                fuel_kg = fuel_cap = fuel_laps = 0.0

            try:
                ers_j   = float(getattr(p, 'ers_store_energy', 0) or 0)
                ers_pct = min(100.0, max(0.0, round(ers_j / 4_000_000 * 100, 1)))
            except Exception:
                ers_pct = 0.0

            drs_ativo      = bool(getattr(p, 'drs', 0))
            drs_disponivel = bool(getattr(p, 'drs_allowed', 0))
            drs_distancia  = int(getattr(p, 'drs_activation_distance', 0) or 0)
            pit_on         = bool(getattr(p, 'pit', 0))

            # ── Laps + Setores ──────────────────────────────────
            voltas = getattr(p, 'todas_voltas_setores', []) or []
            validas = [v for v in voltas
                       if v.get('tempo_total') and v['tempo_total'] > 10]

            best_lap_p = min((v['tempo_total'] for v in validas), default=None)
            last_lap_p = getattr(p, 'lastLapTime', 0) or 0
            if not last_lap_p and validas:
                last_lap_p = validas[-1].get('tempo_total')

            # Última volta com setores preenchidos
            _ultima_com_setores = None
            for _v in reversed(voltas):
                _set = _v.get('setores') or []
                if any(s is not None and s > 0 for s in _set):
                    _ultima_com_setores = _v
                    break

            _last_s1 = _last_s2 = _last_s3 = None
            if _ultima_com_setores and _ultima_com_setores.get('setores'):
                _set = _ultima_com_setores['setores']
                _last_s1 = _set[0] if len(_set) > 0 and _set[0] and _set[0] > 0 else None
                _last_s2 = _set[1] if len(_set) > 1 and _set[1] and _set[1] > 0 else None
                _last_s3 = _set[2] if len(_set) > 2 and _set[2] and _set[2] > 0 else None

            # Melhores setores pessoais
            _s1s = [v['setores'][0] for v in validas
                    if v.get('setores') and v['setores'][0] and v['setores'][0] > 5]
            _s2s = [v['setores'][1] for v in validas
                    if v.get('setores') and v['setores'][1] and v['setores'][1] > 5]
            _s3s = [v['setores'][2] for v in validas
                    if v.get('setores') and v['setores'][2] and v['setores'][2] > 5]

            _best_s1_p = min(_s1s) if _s1s else None
            _best_s2_p = min(_s2s) if _s2s else None
            _best_s3_p = min(_s3s) if _s3s else None

            try:
                speed = int(getattr(p, 'speed_trap', 0) or 0)
            except Exception:
                speed = 0

            delta = getattr(p, 'delta_to_leader', None)
            if isinstance(delta, str):
                delta = None

            pilotos_raw.append({
                "idx":      idx,
                "nome":     nome,
                "numero":   getattr(p, 'numero', None),
                "posicao":  getattr(p, 'position', None),
                "x":        x,
                "z":        z,
                "has_pos":  has_pos,
                "speed":    speed,
                "cor": teams_color_dictionary.get(team_id, "#888888"),
                "equipe":   teams_name_dictionary.get(team_id, "?"),
                "pit_on":   bool(getattr(p, 'pit', 0)),
                "pit":      bool(getattr(p, 'pit', False)),
                "is_pit":   bool(getattr(p, 'pit', False)),
                "tyre":     tyre_name,
                "tyre_age": int(getattr(p, 'tyresAgeLaps', 0) or 0),
                "best_lap": round(best_lap_p, 3) if best_lap_p else None,
                "last_lap": round(last_lap_p, 3) if last_lap_p else None,

                # Setores já fechados (última volta completa)
                "s1":      round(_last_s1, 3) if _last_s1 else None,
                "s2":      round(_last_s2, 3) if _last_s2 else None,
                "s3":      round(_last_s3, 3) if _last_s3 else None,
                "best_s1": round(_best_s1_p, 3) if _best_s1_p else None,
                "best_s2": round(_best_s2_p, 3) if _best_s2_p else None,
                "best_s3": round(_best_s3_p, 3) if _best_s3_p else None,

                "delta_to_leader": delta,
                "gap":      None,
                "interval": None,

                # detalhes
                "tyre_wear":         tw,
                "tyre_temp_inner":   ti,
                "tyre_temp_surface": ts,
                "brakes_temp":       bt,
                "dano_asa_esquerda": dano_e,
                "dano_asa_direita":  dano_d,
                "dano_asa_traseira": dano_t,
                "dano_assoalho":     dano_a,
                "dano_difusor":      dano_f,
                "dano_sidepods":     dano_s,
                "fuel":              fuel_kg,
                "fuel_capacity":     fuel_cap,
                "fuel_laps":         fuel_laps,
                "ers_pct":           ers_pct,
                "drs_ativo":         drs_ativo,
                "drs_disponivel":    drs_disponivel,
                "drs_distancia":     drs_distancia,
                "pit_on":            pit_on,
                "current_lap":       int(getattr(p, 'current_lap_num', 0) or 0),

                # Motor / Powertrain
                "engine_damage":  float(getattr(p, 'engineDamage', 0) or 0),
                "engine_ice":     float(getattr(p, 'engine_icewear', 0) or 0),
                "engine_mguk":    float(getattr(p, 'engine_mgukwear', 0) or 0),
                "engine_mguh":    float(getattr(p, 'engine_mguhwear', 0) or 0),
                "engine_es":      float(getattr(p, 'engine_eswear', 0) or 0),
                "engine_ce":      float(getattr(p, 'engine_cewear', 0) or 0),
                "engine_tc":      float(getattr(p, 'engine_tcwear', 0) or 0),
                "gearbox_damage": float(getattr(p, 'gearBoxDamage', 0) or 0),
                "drs_fault":      float(getattr(p, 'drsFault', 0) or 0),
                "ers_fault":      float(getattr(p, 'ersFault', 0) or 0),
                "tyre_blisters":  list(getattr(p, 'tyre_blisters', [0,0,0,0]) or [0,0,0,0]),
            })

        # ── Ordena por posição ──
        pilotos_raw.sort(key=lambda y: (y['posicao'] is None,
                                        y['posicao'] if y['posicao'] else 999))

        # ── Gap + Interval ──
        for i, y in enumerate(pilotos_raw):
            d = y.get('delta_to_leader')
            if isinstance(d, (int, float)) and d >= 0:
                y['gap'] = round(float(d), 3)
            else:
                y['gap'] = None

            if i == 0:
                y['interval'] = 0.0 if y.get('gap') == 0 else None
            else:
                prev = pilotos_raw[i-1]
                if y.get('gap') is not None and prev.get('gap') is not None:
                    y['interval'] = round(y['gap'] - prev['gap'], 3)
                else:
                    y['interval'] = None

        # Melhores setores da SESSÃO
        _sb_s1  = [y['best_s1']  for y in pilotos_raw if y.get('best_s1')]
        _sb_s2  = [y['best_s2']  for y in pilotos_raw if y.get('best_s2')]
        _sb_s3  = [y['best_s3']  for y in pilotos_raw if y.get('best_s3')]
        _sb_lap = [y['best_lap'] for y in pilotos_raw if y.get('best_lap')]
        _session_bests = {
            "s1":  min(_sb_s1)  if _sb_s1  else None,
            "s2":  min(_sb_s2)  if _sb_s2  else None,
            "s3":  min(_sb_s3)  if _sb_s3  else None,
            "lap": min(_sb_lap) if _sb_lap else None,
        }

        time_of_day = int(getattr(SESSION, 'm_time_of_day', 0) or 0)
        return jsonify({
            "track": track,
            "sessao": {
                "nome_pista":        track,
                "tipo_sessao":       sess_type_name,
                "volta_atual":       max_lap,
                "total_voltas":      total_laps,
                "session_time_left": session_time_left,
                "bandeira":          flag_raw,
                "sc_status":         sc_status,
                "time_of_day":       time_of_day,
                "temp_pista":        temp_pista,
                "temp_ar":           temp_ar,
                "chance_chuva":      _get_rain_percent(),
                "clima":             clima,
                "formula":           formula_code,
                "formula_name":      formula_name,
                "pit_ideal_lap":  int(getattr(SESSION, 'm_pit_stop_window_ideal_lap', 0) or 0),
                "pit_latest_lap": int(getattr(SESSION, 'm_pit_stop_window_latest_lap', 0) or 0),
                "pit_rejoin_pos": int(getattr(SESSION, 'm_pit_stop_rejoin_position', 0) or 0),
            },
            "pilotos": pilotos_raw,
            "session_bests": _session_bests,
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({
            "track": "—",
            "sessao": {
                "nome_pista": "—", "tipo_sessao": "—",
                "volta_atual": 0, "total_voltas": 0,
                "session_time_left": 0,
                "time_of_day": 0,
                "formula": 0,
                "formula_name": "F1",
                "bandeira": "—", "sc_status": "Nenhum",
                "temp_pista": "—", "temp_ar": "—",
                "chance_chuva": 0, "clima": "—",
                "pit_ideal_lap":  0,
                "pit_latest_lap": 0,
                "pit_rejoin_pos": 0,
            },
            "pilotos": [],
            "session_bests": {},
            "erro": str(e),
        })
@app.route("/debug_map")
def debug_map():
    import dados.map_performance as m
    info = {
        "atributos": [x for x in dir(m) if not x.startswith('__')],
        "tipos":     {x: type(getattr(m, x)).__name__ for x in dir(m) if not x.startswith('__')},
    }
    for nome in ("MAP_POSITIONS", "POSICOES", "POSITIONS", "MAPA", "coordenadas", "dados"):
        if hasattr(m, nome):
            v = getattr(m, nome)
            try:
                info[f"preview_{nome}"] = str(v)[:500]
            except Exception:
                pass
    return jsonify(info)

@app.route("/dados_stints_ultimo")
def dados_stints_ultimo():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

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
    try:
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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cursor.fetchone()
        sessao_info = dict(sessao_row) if sessao_row else {
            "id": sessao_id, "nome_pista": "Desconhecida", "tipo_sessao": "Manual"
        }

        cursor.execute("SELECT * FROM setups WHERE sessao_id = ? ORDER BY id", (sessao_id,))
        setups_rows = [dict(row) for row in cursor.fetchall()]

        print(f"📊 dados_setups/{sessao_id}: encontrou {len(setups_rows)} setups")

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
    try:
        data = request.json
        if not data:
            return jsonify({"ok": False, "erro": "Dados inválidos"}), 400
        
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()
        
        cur.execute("PRAGMA table_info(setups)")
        colunas_existentes = [col[1] for col in cur.fetchall()]
        
        sessao_id = data.get('sessao_id')
        attach_to_session = bool(data.get('attach_to_session', False))
        if sessao_id and not attach_to_session:
            sessao_id = None
        pista = data.get('pista', 'Custom')
        categoria = data.get('categoria', 'F1')
        
        if sessao_id:
            cur.execute("SELECT id FROM sessoes WHERE id = ?", (sessao_id,))
            if not cur.fetchone():
                sessao_id = None
        
        if not sessao_id:
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
        
        cur.execute("""
            INSERT INTO pilotos (sessao_id, nome, numero, posicao)
            VALUES (?, ?, ?, 1)
        """, (sessao_id, data.get('piloto_nome', 'Piloto'), data.get('numero', 0)))
        piloto_id = cur.lastrowid
        
        todos_campos = {
            'sessao_id': sessao_id,
            'piloto_id': piloto_id,
            'piloto_nome': data.get('piloto_nome', 'Piloto'),
            'pista': pista,
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
        
        campos_ok = {k: v for k, v in todos_campos.items() if k in colunas_existentes}
        
        colunas_sql = ', '.join(campos_ok.keys())
        placeholders = ', '.join(['?'] * len(campos_ok))
        valores = tuple(campos_ok.values())
        
        cur.execute(f"INSERT INTO setups ({colunas_sql}) VALUES ({placeholders})", valores)
        
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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("PRAGMA table_info(setups)")
        colunas = [col[1] for col in cur.fetchall()]
        
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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        
        cur.execute("SELECT sessao_id FROM setups WHERE id = ?", (setup_id,))
        row = cur.fetchone()
        
        cur.execute("DELETE FROM setups WHERE id = ?", (setup_id,))
        
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
    return render_template('setup_editor.html')


@app.route("/api/telemetry_insights/<int:sessao_id>")
def telemetry_insights(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cur.fetchone()
        sessao = dict(sessao_row) if sessao_row else {}

        if not sessao:
            conn.close()
            return jsonify({"erro": "Sessão não encontrada", "sessao": {}, "pilotos": []})

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

        cur.execute("PRAGMA table_info(voltas)")
        voltas_cols = [col[1] for col in cur.fetchall()]

        cur.execute("PRAGMA table_info(pneus)")
        pneus_cols = [col[1] for col in cur.fetchall()]

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetria'")
        tem_telemetria = cur.fetchone() is not None

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='danos'")
        tem_danos = cur.fetchone() is not None

        import math

        resultado = []
        for p in pilotos_raw:
            pid = p["id"]
            nome = p["nome"]

            cur.execute("""
                SELECT numero_volta, tempo_volta, setor1, setor2, setor3
                FROM voltas
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY numero_volta
            """, (sessao_id, pid))
            voltas_raw = [dict(r) for r in cur.fetchall()]

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

            limpo = [t for t in tempos if t < media * 1.08] if media else tempos
            media_limpa = sum(limpo) / len(limpo) if limpo else media

            if len(limpo) > 1:
                dp = math.sqrt(sum((t - media_limpa) ** 2 for t in limpo) / len(limpo))
                consistencia = max(0, round(100 - (dp / media_limpa * 100), 1))
            else:
                consistencia = 0.0

            degradacao = 0.0
            if len(limpo) >= 3:
                n = len(limpo)
                x_mean = (n - 1) / 2
                y_mean = sum(limpo) / n
                num = sum((i - x_mean) * (limpo[i] - y_mean) for i in range(n))
                den = sum((i - x_mean) ** 2 for i in range(n))
                degradacao = round(num / den, 4) if den else 0.0

            top_speed = 0
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

            if top_speed == 0:
                top_speed = float(sessao.get("velocidade_maxima_geral") or 0)

            avg_s1 = round(sum(s1_list) / len(s1_list), 3) if s1_list else 0
            avg_s2 = round(sum(s2_list) / len(s2_list), 3) if s2_list else 0
            avg_s3 = round(sum(s3_list) / len(s3_list), 3) if s3_list else 0
            best_s1 = round(min(s1_list), 3) if s1_list else 0
            best_s2 = round(min(s2_list), 3) if s2_list else 0
            best_s3 = round(min(s3_list), 3) if s3_list else 0

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

        for r in resultado:
            print(f"📊 {r['nome']}: {r['total_voltas']} voltas, best={r['melhor_volta']}, avg={r['media_volta']}, s1={r['avg_s1']}, s2={r['avg_s2']}, s3={r['avg_s3']}")

        return jsonify({"sessao": sessao, "pilotos": resultado})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"erro": str(e), "sessao": {}, "pilotos": []}), 500


@app.route("/renomear_sessao/<int:sessao_id>", methods=["POST"])
def renomear_sessao(sessao_id):
    try:
        data = request.get_json()
        novo_nome = data.get("nome", "").strip()
        
        if not novo_nome:
            return jsonify({"ok": False, "erro": "Nome vazio"}), 400

        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(sessoes)")
        colunas = [col[1] for col in cur.fetchall()]

        if "nome_customizado" not in colunas:
            cur.execute("ALTER TABLE sessoes ADD COLUMN nome_customizado TEXT DEFAULT NULL")

        cur.execute("UPDATE sessoes SET nome_customizado = ? WHERE id = ?", (novo_nome, sessao_id))
        conn.commit()
        conn.close()

        return jsonify({"ok": True, "mensagem": f"Sessão #{sessao_id} renomeada para: {novo_nome}"})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/Comparar")
def telemetry_insights_page():
    return render_template("Comparar.html")


@app.route("/api/race_positions/<int:sessao_id>")
def race_positions(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT nome_pista, tipo_sessao, total_voltas FROM sessoes WHERE id = ?", (sessao_id,))
        row = cur.fetchone()
        sessao = dict(row) if row else {}

        cur.execute("""
            SELECT
                MIN(p.id)                                        AS pid,
                p.nome,
                p.numero,
                p.nome_equipe,
                p.team_id,
                MAX(p.grid_position)                             AS grid_position,
                COALESCE(MAX(p.posicao_final), MIN(p.posicao))   AS pos_final
            FROM pilotos p
            WHERE p.sessao_id = ?
            GROUP BY p.nome
            ORDER BY COALESCE(MAX(p.posicao_final), MIN(p.posicao))
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]

        resultado = []
        max_volta = 0

        for p in pilotos:
            cur.execute("SELECT id FROM pilotos WHERE sessao_id = ? AND nome = ?", (sessao_id, p["nome"]))
            ids = [r[0] for r in cur.fetchall()]
            ph  = ",".join("?" * len(ids))

            cur.execute(f"""
                SELECT numero_volta, posicao
                FROM voltas
                WHERE sessao_id = ? AND piloto_id IN ({ph})
                  AND numero_volta IS NOT NULL AND numero_volta > 0
                ORDER BY numero_volta
            """, (sessao_id, *ids))
            voltas = [dict(r) for r in cur.fetchall()]

            if not voltas:
                continue

            pos_por_volta = {}
            for v in voltas:
                pos = v["posicao"]
                nv  = int(v["numero_volta"])
                if pos and pos > 0:
                    pos_por_volta[nv] = int(pos)
                if nv > max_volta:
                    max_volta = nv

            grid = p.get("grid_position")
            if grid and grid > 0:
                pos_por_volta[0] = int(grid)

            resultado.append({
                "nome":         p["nome"],
                "numero":       p["numero"],
                "equipe":       p.get("nome_equipe") or "?",
                "team_id":      p.get("team_id"),
                "grid_position":grid,
                "pos_final":    p["pos_final"],
                "posicoes":     pos_por_volta,
            })

        conn.close()
        return jsonify({"sessao": sessao, "pilotos": resultado, "max_volta": max_volta})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"erro": str(e), "pilotos": [], "max_volta": 0}), 500


@app.route("/race_positions")
def race_positions_page():
    return render_template("race_positions.html")


@app.route("/api/race_positions/<int:sessao_id>/ultrapassagens")
def race_ultrapassagens(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT volta, ultrapassou_nome, ultrapassado_nome,
                   pos_ultrapassou, pos_ultrapassado, timestamp
            FROM ultrapassagens WHERE sessao_id = ?
            ORDER BY volta, timestamp
        """, (sessao_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify([])


@app.route("/api/pit_stops/<int:sessao_id>")
def api_pit_stops(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT nome_pista, tipo_sessao, total_voltas FROM sessoes WHERE id = ?", (sessao_id,))
        sessao_row = cur.fetchone()
        sessao = dict(sessao_row) if sessao_row else {}

        cur.execute("""
            SELECT MIN(id) as id, nome, numero, MAX(posicao) as posicao
            FROM pilotos WHERE sessao_id = ?
            GROUP BY nome ORDER BY posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]

        resultado = []
        for p in pilotos:
            pid = p["id"]

            cur.execute("""
                SELECT stint_numero, tipo_pneu, volta_inicio, volta_fim, total_voltas
                FROM pneu_stints
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY stint_numero
            """, (sessao_id, pid))
            stints = [dict(r) for r in cur.fetchall()]

            pit_stops = []
            for s in stints:
                if s["stint_numero"] > 1:
                    pit_stops.append({
                        "volta": s["volta_inicio"],
                        "pneu_novo": s["tipo_pneu"],
                        "stint": s["stint_numero"]
                    })

            resultado.append({
                "nome": p["nome"],
                "numero": p["numero"],
                "posicao": p["posicao"],
                "total_pits": len(pit_stops),
                "pit_stops": pit_stops
            })

        conn.close()
        return jsonify({"sessao": sessao, "pilotos": resultado})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"sessao": {}, "pilotos": [], "erro": str(e)}), 500


@app.route("/api/bandeiras/<int:sessao_id>")
def api_bandeiras(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bandeiras'")
        if not cur.fetchone():
            conn.close()
            return jsonify({"bandeiras": [], "aviso": "Tabela bandeiras ainda não existe. Reinicie o main.py."})

        cur.execute("""
            SELECT tipo, volta_inicio, volta_fim, carro_idx, carro_nome, timestamp
            FROM bandeiras
            WHERE sessao_id = ?
            ORDER BY volta_inicio, timestamp
        """, (sessao_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        resumo = {}
        for r in rows:
            t = r["tipo"]
            if t not in resumo:
                resumo[t] = 0
            resumo[t] += 1

        return jsonify({"bandeiras": rows, "resumo": resumo})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"bandeiras": [], "erro": str(e)}), 500


@app.route("/api/danos_carro/<int:sessao_id>")
def api_danos_carro(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT MIN(id) as id, nome, numero, MAX(posicao) as posicao
            FROM pilotos WHERE sessao_id = ?
            GROUP BY nome ORDER BY posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]

        cur.execute("PRAGMA table_info(danos)")
        danos_cols = [c[1] for c in cur.fetchall()]

        resultado = []
        for p in pilotos:
            pid = p["id"]

            cur.execute("""
                SELECT * FROM danos
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (sessao_id, pid))
            d = cur.fetchone()
            dano_dict = dict(d) if d else {}

            def _get(key, fallback=0):
                return float(dano_dict.get(key) or fallback)

            asa_e  = _get("dano_asa_esquerda")
            asa_d  = _get("dano_asa_direita")
            asa_t  = _get("dano_asa_traseira")
            assoal = _get("dano_assoalho")
            difus  = _get("dano_difusor")
            sidep  = _get("dano_sidepods")

            total = (asa_e + asa_d) * 0.35 + asa_t * 0.15 + assoal * 0.2 + difus * 0.15 + sidep * 0.15

            def nivel(v):
                if v >= 67: return "vermelho"
                if v >= 34: return "amarelo"
                return "verde"

            resultado.append({
                "nome": p["nome"],
                "numero": p["numero"],
                "posicao": p["posicao"],
                "danos": {
                    "asa_esquerda":  asa_e,
                    "asa_direita":   asa_d,
                    "asa_traseira":  asa_t,
                    "assoalho":      assoal,
                    "difusor":       difus,
                    "sidepods":      sidep,
                    "total":         round(total, 1),
                    "nivel":         nivel(total),
                    "nivel_asa_e":   nivel(asa_e),
                    "nivel_asa_d":   nivel(asa_d),
                    "nivel_asa_t":   nivel(asa_t),
                    "nivel_assoalho":nivel(assoal),
                    "nivel_difusor": nivel(difus),
                    "nivel_sidepods":nivel(sidep),
                }
            })

        conn.close()
        return jsonify({"pilotos": resultado})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"pilotos": [], "erro": str(e)}), 500

@app.route("/api/danos_por_volta/<int:sessao_id>")
def api_danos_por_volta(sessao_id):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='danos_por_volta'")
        if not cur.fetchone():
            conn.close()
            return jsonify({"pilotos": [], "aviso": "Tabela danos_por_volta ainda não existe. Reinicie o main.py."})

        cur.execute("""
            SELECT MIN(p.id) as pid, p.nome, MAX(p.posicao) as posicao
            FROM pilotos p WHERE p.sessao_id = ?
            GROUP BY p.nome ORDER BY posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]

        resultado = []
        for p in pilotos:
            cur.execute("""
                SELECT numero_volta,
                       asa_esquerda, asa_direita, asa_traseira,
                       assoalho, difusor, sidepods
                FROM danos_por_volta
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY numero_volta
            """, (sessao_id, p["pid"]))
            voltas = [dict(r) for r in cur.fetchall()]

            resultado.append({
                "nome":    p["nome"],
                "posicao": p["posicao"],
                "voltas":  voltas
            })

        conn.close()
        return jsonify({"pilotos": resultado})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"pilotos": [], "erro": str(e)}), 500

def _garantir_tabela_tracados():
    """
    Cria a tabela `tracados` se não existir.
    Retorna True se OK, False se falhou.
    """
    try:
        # Garante que o diretório pai do DB existe e é gravável
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 diretório criado: {db_dir}")

        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tracados (
                track_key   TEXT PRIMARY KEY,
                nome_pista  TEXT,
                segmentos   TEXT NOT NULL,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        print(f"✅ tabela 'tracados' pronta em {DB_PATH}")
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ _garantir_tabela_tracados falhou: {e}")
        print(f"   DB_PATH = {DB_PATH}")
        print(f"   dir pai existe? {os.path.exists(os.path.dirname(DB_PATH))}")
        print(f"   dir pai gravável? {os.access(os.path.dirname(DB_PATH), os.W_OK) if os.path.exists(os.path.dirname(DB_PATH)) else 'N/A'}")
        return False


# Roda no startup e guarda o resultado numa flag global
TRACADOS_OK = _garantir_tabela_tracados()
@app.route("/api/tracados", methods=["GET"])
def listar_tracados():
    """Lista todos os traçados salvos (só metadados, sem os pontos)."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT track_key, nome_pista,
                   LENGTH(segmentos) AS tamanho,
                   updated_at
            FROM tracados
            ORDER BY updated_at DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify([]), 500


@app.route("/api/tracados/<track_key>", methods=["GET"])
def carregar_tracado(track_key):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT nome_pista, segmentos, updated_at FROM tracados WHERE track_key = ?",
            (track_key.upper(),)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"ok": False, "erro": "não encontrado"}), 404

        try:
            segmentos = json.loads(row["segmentos"])
        except Exception:
            segmentos = []

        return jsonify({
            "ok": True,
            "track_key": track_key.upper(),
            "nome_pista": row["nome_pista"],
            "segmentos": segmentos,
            "updated_at": row["updated_at"],
        })
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/api/tracados/<track_key>", methods=["POST"])
def salvar_tracado(track_key):
    """
    Salva (ou substitui) o traçado de uma pista.

    Body JSON esperado:
        {
            "nome_pista": "Interlagos",
            "segmentos": [
                [ {"x": 1.2, "z": 3.4, "speed": 210}, ... ],   # seg 1
                [ {"x": 5.6, "z": 7.8, "speed": 180}, ... ],   # seg 2
                ...
            ]
        }
    """
    # ── 0) Backend saudável? ──────────────────────────────────────
    if not TRACADOS_OK:
        print(f"❌ POST /api/tracados/{track_key} rejeitado: tabela indisponível")
        return jsonify({
            "ok": False,
            "erro": "tabela 'tracados' indisponível no backend",
            "db_path": DB_PATH,
        }), 503

    try:
        # ── 1) Log de entrada (sempre, ajuda a diagnosticar) ──────
        payload_bytes = len(request.data or b"")
        print(f"🔵 POST /api/tracados/{track_key} — {payload_bytes} bytes recebidos")

        # ── 2) Parse do body ──────────────────────────────────────
        data = request.get_json(silent=True)
        if data is None:
            print(f"❌ body JSON inválido em {track_key}")
            return jsonify({"ok": False, "erro": "body não é JSON válido"}), 400

        segmentos  = data.get("segmentos")
        nome_pista = (data.get("nome_pista") or track_key or "").strip() or track_key

        # ── 3) Validação ──────────────────────────────────────────
        if not isinstance(segmentos, list):
            print(f"❌ segmentos não é lista em {track_key}")
            return jsonify({"ok": False, "erro": "segmentos deve ser uma lista"}), 400

        # Filtra segmentos vazios/inválidos
        segmentos = [
            s for s in segmentos
            if isinstance(s, list) and len(s) > 0
        ]

        if not segmentos:
            print(f"⚠️  {track_key}: nenhum segmento válido para salvar")
            return jsonify({"ok": False, "erro": "nenhum segmento válido"}), 400

        # Limita a 20 segmentos (mesma regra do front)
        if len(segmentos) > 20:
            segmentos = segmentos[-20:]

        # Valida pontos mínimos (cada ponto precisa de x e z)
        segmentos_saneados = []
        for i, seg in enumerate(segmentos):
            pontos_ok = []
            for p in seg:
                if isinstance(p, dict) and "x" in p and "z" in p:
                    try:
                        pontos_ok.append({
                            "x": float(p["x"]),
                            "z": float(p["z"]),
                            "speed": float(p.get("speed", 0) or 0),
                        })
                    except (TypeError, ValueError):
                        continue
            if pontos_ok:
                segmentos_saneados.append(pontos_ok)

        if not segmentos_saneados:
            print(f"❌ {track_key}: todos os pontos inválidos após sanitização")
            return jsonify({"ok": False, "erro": "pontos inválidos"}), 400

        # ── 4) Serialização ───────────────────────────────────────
        blob = json.dumps(segmentos_saneados, separators=(",", ":"))
        total_pontos = sum(len(s) for s in segmentos_saneados)

        # ── 5) Persistência ───────────────────────────────────────
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tracados (track_key, nome_pista, segmentos, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(track_key) DO UPDATE SET
                    nome_pista = excluded.nome_pista,
                    segmentos  = excluded.segmentos,
                    updated_at = CURRENT_TIMESTAMP
            """, (track_key.upper(), nome_pista, blob))
            conn.commit()
        finally:
            conn.close()

        # ── 6) Log de sucesso ─────────────────────────────────────
        print(f"💾 traçado salvo: {track_key} "
              f"({len(segmentos_saneados)} seg, {total_pontos} pts, {len(blob)} bytes)")

        return jsonify({
            "ok":         True,
            "track_key":  track_key.upper(),
            "nome_pista": nome_pista,
            "segmentos":  len(segmentos_saneados),
            "pontos":     total_pontos,
            "bytes":      len(blob),
        })

    except sqlite3.OperationalError as e:
        # Erro específico do SQLite (ex.: no such table, disk full, locked)
        import traceback; traceback.print_exc()
        print(f"❌ SQLite OperationalError em {track_key}: {e}")
        return jsonify({
            "ok": False,
            "erro": f"SQLite: {e}",
            "db_path": DB_PATH,
        }), 500

    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"❌ Erro inesperado em salvar_tracado/{track_key}: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500

@app.route("/api/tracados/<track_key>", methods=["DELETE"])
def deletar_tracado(track_key):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()
        cur.execute("DELETE FROM tracados WHERE track_key = ?", (track_key.upper(),))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
if __name__ == "__main__":
    print(f"[INFO] STATIC_PATH: {STATIC_PATH}")
    print()
    print("🚀 Servidor rodando!")
    print("Acesse: http://localhost:5000/")
    print("=" * 50)
    print()
    app.run(host="0.0.0.0", port=5000, debug=True)