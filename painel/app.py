from flask import Flask, render_template, jsonify
import json
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

#carregar json
@app.route("/dados_pneus")
def dados_pneus():
    try:
        conn = get_db()
        cur = conn.cursor()
        sessao_id = get_last_session_id(cur)
        if not sessao_id:
            conn.close()
            return jsonify([])
        cur.execute("""
          SELECT p.nome, p.numero, p.posicao AS position,
                 pn.tipo_pneu AS tyres,
                 pn.idade_voltas AS tyresAgeLaps,
                 pn.desgaste_RL, pn.desgaste_RR, pn.desgaste_FL, pn.desgaste_FR,
                 pn.temp_interna_RL, pn.temp_interna_RR, pn.temp_interna_FL, pn.temp_interna_FR,
                 pn.temp_superficie_RL, pn.temp_superficie_RR, pn.temp_superficie_FL, pn.temp_superficie_FR,
                 pn.vida_util AS tyre_life,
                 pn.tyre_set_data,
                 pn.lap_delta_time,
                 pn.pit_stops
          FROM pilotos p
          LEFT JOIN pneus pn ON p.id = pn.piloto_id
          WHERE p.sessao_id = ?
          ORDER BY p.posicao
        """, (sessao_id,))
        rows = cur.fetchall()
        conn.close()
        data = []
        for r in rows:
            tyre_wear = [r["desgaste_RL"], r["desgaste_RR"], r["desgaste_FL"], r["desgaste_FR"]]
            tyre_temp_i = [r["temp_interna_RL"], r["temp_interna_RR"], r["temp_interna_FL"], r["temp_interna_FR"]]
            tyre_temp_s = [r["temp_superficie_RL"], r["temp_superficie_RR"], r["temp_superficie_FL"], r["temp_superficie_FR"]]
            data.append({
                "nome": r["nome"],
                "numero": r["numero"],
                "position": r["position"],
                "tyres": r["tyres"],
                "tyresAgeLaps": r["tyresAgeLaps"],
                "tyre_wear": tyre_wear,
                "tyre_temp_i": tyre_temp_i,
                "tyre_temp_s": tyre_temp_s,
                "tyre_life": r["tyre_life"],
                "tyre_set_data": r["tyre_set_data"],
                "lap_delta_time": r["lap_delta_time"],
                "pit_stop": r["pit_stops"]
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"erro": str(e)})

@app.route("/dados_voltas")
def dados_voltas():
    try:
        conn = get_db()
        cur = conn.cursor()
        sessao_id = get_last_session_id(cur)
        if not sessao_id:
            conn.close()
            return jsonify([])
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
                    "setor1": v["setor1"],
                    "setor2": v["setor2"],
                    "setor3": v["setor3"]
                })
            resultado.append({
                "nome": pb["nome"],
                "numero": pb["numero"],
                "position": pb["posicao"],
                "tyres": pb["tyres"],
                "tyresAgeLaps": pb["tyresAgeLaps"],
                "laps_max": pb["total_voltas"],
                "voltas": lista_voltas
            })
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)})

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
    from Bot.jogadores import get_jogadores
    
    jogadores = get_jogadores()
    dados = []
    
    for j in jogadores:
        # Pega os stints de pneus DO OBJETO DO PILOTO (em tempo real)
        stints = getattr(j, 'pneu_stints', [])
        
        # Se não houver stints, cria um padrão
        if not stints:
            current_lap = getattr(j, 'current_lap_num', 0)
            stints = [{
                'stint_numero': 1,
                'tipo_pneu': getattr(j, 'tyres', 'MEDIUM'),
                'composto_real': getattr(j, 'tyres', 7),
                'volta_inicio': 1,
                'volta_fim': current_lap,
                'total_voltas': current_lap
            }]
        
        dados.append({
            'nome': getattr(j, 'name', 'Piloto'),
            'numero': getattr(j, 'numero', 0),
            'position': getattr(j, 'position', 0),
            'pit_stop': getattr(j, 'pit_stops', 0),
            'num_laps': getattr(j, 'current_lap_num', 0),
            'tyres': getattr(j, 'tyres', 'MEDIUM'),
            'stints': stints  # ← ENVIA OS STINTS
        })
    
    return jsonify(dados)

@app.route("/dados_completos")
def dados_completos():
    try:
        conn = get_db()
        cur = conn.cursor()
        sessao_id = get_last_session_id(cur)
        if not sessao_id:
            conn.close()
            return jsonify({"sessao": {}, "pilotos": []})
        cur.execute("""
          SELECT clima, temperatura_ar AS tempo_ar, temperatura_pista AS tempo_pista,
                 porcentagem_chuva AS rain_porcentagem,
                 safety_car_status AS safety_car_status,
                 tipo_sessao AS Sessao,
                 flag,
                 velocidade_maxima_geral AS maior_speed_geral,
                 total_voltas,
                 nome_pista
          FROM sessoes WHERE id = ?
        """, (sessao_id,))
        sessao = dict(cur.fetchone())
        cur.execute("""
          SELECT p.nome, p.numero, p.posicao AS position,
                 COALESCE(pn.tipo_pneu,'') AS tyres,
                 COALESCE(pn.idade_voltas,0) AS tyresAgeLaps,
                 COALESCE(d.delta_to_leader,'—') AS delta_to_leader,
                 s.total_voltas AS num_laps,
                 COALESCE(pn.pit_stops,0) AS pit_stop
          FROM pilotos p
          LEFT JOIN pneus pn ON p.id = pn.piloto_id
          LEFT JOIN danos d ON p.id = d.piloto_id
          JOIN sessoes s ON p.sessao_id = s.id
          WHERE p.sessao_id = ?
          ORDER BY p.posicao
        """, (sessao_id,))
        pilotos = [dict(r) for r in cur.fetchall()]
        conn.close()
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