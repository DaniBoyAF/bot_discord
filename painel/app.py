from flask import Flask, render_template, jsonify
import ctypes
from Bot.jogadores import get_jogadores
from utils.dictionnaries import tyres_dictionnary

tyres_nomes = {}

import sqlite3

app = Flask(__name__)
#carregar pagina
def get_db():
    conn = sqlite3.connect('f1_telemetry.db')
    conn.row_factory = sqlite3.Row
    return conn
def get_last_session_id(cur):
    cur.execute('SELECT MAX(id) FROM sessoes')
    return cur.fetchone()[0]

@app.route("/")
def home():
    return render_template("painel.html")
@app.route("/pnues")
def pneus():
    return render_template("Tyre_hub.html")
@app.route("/graf")
def grafico1():
    return render_template("Media_lap.html")#certo
@app.route("/g")
def media_HD():
    return render_template("Race_Pace.html")#certo
@app.route("/pit")
def pit():
    return render_template("pit_stop.html")
@app.route("/selecionar_sessao")
def selecionar_sessao():
    return render_template("selecionar_sessao.html")

def _to_primitive(value):
    """Converte ctypes arrays/ctypes scalars e objetos iteráveis em tipos JSON-serializáveis."""
    # ctypes scalar
    if isinstance(value, (ctypes.c_int, ctypes.c_uint, ctypes.c_long, ctypes.c_ulong)):
        try:
            return int(value.value)
        except Exception:
            return int(value)
    if isinstance(value, (ctypes.c_float, ctypes.c_double)):
        try:
            return float(value.value)
        except Exception:
            return float(value)
    # ctypes array / other iterable (mas não str/bytes/dict)
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict, list, tuple)):
        try:
            return [_to_primitive(x) for x in value]
        except Exception:
            pass
    # lists/tuples/dicts: recurse
    if isinstance(value, (list, tuple)):
        return [_to_primitive(x) for x in value]
    if isinstance(value, dict):
        return {k: _to_primitive(v) for k, v in value.items()}
    # fallback: primitive or str()
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    try:
        return str(value)
    except Exception:
        return None

def _tyre_name_from_code(v):
    """Converte código (ctypes/int/str) para nome legível usando tyres_nomes -> tyres_dictionnary."""
    try:
        # converte ctypes/objects pra primitivo
        if hasattr(v, "value"):
            v = v.value
        if isinstance(v, str) and v.strip() == "":
            return "Desconhecido"
        # tenta interpretar como inteiro (aceita "1", "1.0", etc.)
        code = None
        if isinstance(v, (int, float)):
            code = int(v)
        elif isinstance(v, str):
            try:
                code = int(float(v))
            except Exception:
                code = None
        else:
            try:
                code = int(v)
            except Exception:
                code = None
    except Exception:
        return "Desconhecido"

    # prioridade: tyres_nomes (mais específica), depois tyres_dictionnary, fallback texto
    if code is not None:
        if code in tyres_nomes:
            return tyres_nomes[code]
        if code in tyres_dictionnary:
            return tyres_dictionnary[code]
        return f"Código {code}"
    # se não foi possível converter, retorna texto original ou 'Desconhecido'
    return str(v) if v not in (None, '') else "Desconhecido"

#carregar json
@app.route("/dados_pneus_live")
def dados_pneus_live():
    jogadores = get_jogadores()
    resultado = []
    for j in jogadores:
        tyre_code = _to_primitive(getattr(j, "tyres", None))
        resultado.append({
            "name": getattr(j, "name", ""),
            "numero": getattr(j, "numero", 0),
            "position": getattr(j, "position", None),
            "tyres": _tyre_name_from_code(tyre_code),
            "tyresAgeLaps": _to_primitive(getattr(j, "tyresAgeLaps", 0)),
            "tyre_wear": _to_primitive(getattr(j, "tyre_wear", [0, 0, 0, 0])),
            "tyres_temp_inner": _to_primitive(getattr(j, "tyres_temp_inner", [0, 0, 0, 0])),
            "tyres_temp_surface": _to_primitive(getattr(j, "tyres_temp_surface", [0, 0, 0, 0])),
        })
    return jsonify(resultado)
@app.route("/dados_delta")
def dados_delta():
    try:
        conn = get_db()
        cur = conn.cursor()
        sessao_id = get_last_session_id(cur)
        if not sessao_id:
            conn.close()
            return jsonify([])
        cur.execute("""
          SELECT p.nome, p.numero,
                 d.delta_to_leader,
                 d.combustivel_restante AS Fuel,
                 d.dano_asa_esquerda AS FL,
                 d.dano_asa_direita  AS FR,
                 d.dano_asa_traseira AS 'Asa Traseira',
                 d.dano_assoalho     AS 'Assoalho',
                 d.dano_difusor      AS 'Difusor',
                 d.dano_sidepods     AS 'Sidepods'
          FROM pilotos p
          LEFT JOIN danos d ON p.id = d.piloto_id
          WHERE p.sessao_id = ?
          ORDER BY p.posicao
        """, (sessao_id,))
        rows = cur.fetchall()
        conn.close()
        data = []
        for r in rows:
            data.append({
                "delta_to_leader": r["delta_to_leader"],
                "nome": r["nome"],
                "numero": r["numero"],
                "Fuel": r["Fuel"],
                "FL": r["FL"],
                "FR": r["FR"],
                "Asa Traseira": r["Asa Traseira"],
                "Assoalho": r["Assoalho"],
                "Difusor": r["Difusor"],
                "Sidepods": r["Sidepods"]
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/dados_pra_o_painel")
def dados_pra_o_painel():
    try:
        conn = get_db()
        cur = conn.cursor()
        sessao_id = get_last_session_id(cur)
        
        cur.execute("""
            SELECT p.id AS piloto_id, p.nome, p.numero, p.posicao,
                   COALESCE(pn.tipo_pneu,'') AS tyres,
                   COALESCE(pn.idade_voltas,0) AS tyresAgeLaps,
                   COALESCE(pn.pit_stops,0) AS pit_stop,
                   -- adiciona desgaste e temperaturas vindos da tabela pneus
                   COALESCE(pn.desgaste_RL,0) AS desgaste_RL,
                   COALESCE(pn.desgaste_RR,0) AS desgaste_RR,
                   COALESCE(pn.desgaste_FL,0) AS desgaste_FL,
                   COALESCE(pn.desgaste_FR,0) AS desgaste_FR,
                   COALESCE(pn.temp_interna_RL,0) AS temp_interna_RL,
                   COALESCE(pn.temp_interna_RR,0) AS temp_interna_RR,
                   COALESCE(pn.temp_interna_FL,0) AS temp_interna_FL,
                   COALESCE(pn.temp_interna_FR,0) AS temp_interna_FR,
                   COALESCE(pn.temp_superficie_RL,0) AS temp_superficie_RL,
                   COALESCE(pn.temp_superficie_RR,0) AS temp_superficie_RR,
                   COALESCE(pn.temp_superficie_FL,0) AS temp_superficie_FL,
                   COALESCE(pn.temp_superficie_FR,0) AS temp_superficie_FR,
                   s.total_voltas AS num_laps
            FROM pilotos p
            LEFT JOIN pneus pn ON p.id = pn.piloto_id
            JOIN sessoes s ON p.sessao_id = s.id
            WHERE p.sessao_id = ?
        """, (sessao_id,))
        
        resultado = []
        for pb in cur.fetchall():
            # ✅ PEGA STINTS DO BANCO
            cur.execute("""
                SELECT stint_numero, tipo_pneu, composto_real,
                       volta_inicio, volta_fim, total_voltas
                FROM pneu_stints
                WHERE sessao_id = ? AND piloto_id = ?
                ORDER BY stint_numero
            """, (sessao_id, pb["piloto_id"]))
            
            stints = [{
                "stint_numero": s["stint_numero"],
                "tipo_pneu": s["tipo_pneu"],
                "composto_real": s["composto_real"],
                "volta_inicio": s["volta_inicio"],
                "volta_fim": s["volta_fim"],
                "total_voltas": s["total_voltas"]
            } for s in cur.fetchall()]
            
            tyres_raw = pb["tyres"]
            tyres_nome = _tyre_name_from_code(tyres_raw) if tyres_raw not in (None, '') else ""
            
            # construir arrays no formato que o frontend espera: [RL, RR, FL, FR]
            tyre_wear = [pb["desgaste_RL"], pb["desgaste_RR"], pb["desgaste_FL"], pb["desgaste_FR"]]
            tyre_temp_inner = [pb["temp_interna_RL"], pb["temp_interna_RR"], pb["temp_interna_FL"], pb["temp_interna_FR"]]
            tyre_temp_surf = [pb["temp_superficie_RL"], pb["temp_superficie_RR"], pb["temp_superficie_FL"], pb["temp_superficie_FR"]]

            resultado.append({
                "nome": pb["nome"],
                "numero": pb["numero"],
                "position": pb["posicao"],
                "tyres": tyres_nome,
                "tyresAgeLaps": pb["tyresAgeLaps"],
                "tyre_wear": tyre_wear,
                "tyres_temp_inner": tyre_temp_inner,
                "tyres_temp_surface": tyre_temp_surf,
                "num_laps": pb["num_laps"],
                "pit_stop": pb["pit_stop"],
                "stints": stints
            })
        
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/dados_completos_live")
def dados_completos_live():
    """Dashboard em tempo real (direto do parser)"""
    try:
        from Bot.parser2024 import get_jogadores
        from Bot.Session import SESSION
        
        jogadores = get_jogadores()
        
        # Dados da sessão
        sessao = {
            "clima": getattr(SESSION, 'weather', 'Desconhecido'),
            "tempo_ar": getattr(SESSION, 'm_air_temperature', 0),
            "tempo_pista": getattr(SESSION, 'm_track_temperature', 0),
            "rain_porcentagem": getattr(SESSION, 'rainPercentage', 0),
            "safety_car_status": getattr(SESSION, 'm_safety_car_status', 0),
            "Sessao": getattr(SESSION, 'm_session_type', 0),
            "flag": getattr(SESSION, 'm_zone_flag', 'Verde'),
            "maior_speed_geral": max([getattr(j, 'speed', 0) for j in jogadores], default=0),
            "total_voltas": getattr(SESSION, 'm_total_laps', 0),
            "nome_pista": getattr(SESSION, 'track_name', 'Desconhecida')
        }
        
        # Dados dos pilotos
        pilotos = []
        for j in jogadores:
            # normaliza o código vindo do parser (ctypes / str / int)
            tyre_code = _to_primitive(getattr(j, 'tyres', None))
            tyre_name = _tyre_name_from_code(tyre_code)

            pilotos.append({
                "nome": getattr(j, 'name', 'Piloto'),
                "numero": getattr(j, 'numero', 0),
                "position": getattr(j, 'position', 0),
                "tyres": tyre_name,
                "tyresAgeLaps": getattr(j, 'tyresAgeLaps', 0),
                "delta_to_leader": getattr(j, 'delta_to_leader', 0),
                "num_laps": getattr(j, 'current_lap_num', 0),
                "pit_stop": getattr(j, 'pit_stops', 0)
            })
        
        return jsonify({"sessao": sessao, "pilotos": pilotos})
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/historico_sessoes")
def historico_sessoes():
    """Lista todas as sessões do banco"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
          SELECT id, nome_pista, tipo_sessao, total_voltas, 
                 data_hora, velocidade_maxima_geral
          FROM sessoes
          ORDER BY data_hora DESC
        """)
        sessoes = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(sessoes)
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/dados_voltas/<int:sessao_id>")
def dados_voltas_por_sessao(sessao_id):
    """Retorna voltas de uma sessão específica"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
          SELECT p.id AS piloto_id, p.nome, p.numero, p.posicao,
                 COALESCE(pn.tipo_pneu,'') AS tyres,
                 COALESCE(pn.idade_voltas,0) AS tyresAgeLaps,
                 s.total_voltas
          FROM pilotos p
          LEFT JOIN pneus pn ON p.id = pn.piloto_id
          JOIN sessoes s ON p.sessao_id = s.id
          WHERE p.sessao_id = ?
          ORDER BY p.posicao
        """, (sessao_id,))
        pilotos_base = cur.fetchall()
        
        resultado = []
        for pb in pilotos_base:
            cur.execute("""
              SELECT numero_volta, tempo_volta, setor1, setor2, setor3
              FROM voltas
              WHERE sessao_id = ? AND piloto_id = ?
              ORDER BY numero_volta
            """, (sessao_id, pb["piloto_id"]))
            voltas_rows = cur.fetchall()
            
            lista_voltas = []
            for v in voltas_rows:
                lista_voltas.append({
                    "volta": v["numero_volta"],
                    "tempo_total": v["tempo_volta"],
                    "setores": [v["setor1"], v["setor2"], v["setor3"]]
                })
            
            resultado.append({
                "nome": pb["nome"],
                "numero": pb["numero"],
                "position": pb["posicao"],
                "tyres": pb["tyres"],
                "tyresAgeLaps": pb["tyresAgeLaps"],
                "laps_max": pb["total_voltas"],
                "voltas": lista_voltas,
                "pit_stop": 0
            })
        
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)