import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "f1_telemetry.db")
OUT_DIR = os.path.join(os.path.dirname(__file__), "painel", "static")

def listar_sessoes():
    """Lista todas as sessões que têm dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT s.id, s.nome_pista, s.tipo_sessao, s.total_voltas, s.data_hora,
               s.velocidade_maxima_geral,
               (SELECT COUNT(*) FROM pilotos WHERE sessao_id = s.id) as num_pilotos,
               (SELECT COUNT(*) FROM voltas WHERE sessao_id = s.id) as num_voltas
        FROM sessoes s
        WHERE EXISTS (SELECT 1 FROM pilotos WHERE sessao_id = s.id)
        ORDER BY s.id DESC
    """)
    
    sessoes = [dict(r) for r in cur.fetchall()]
    conn.close()
    return sessoes

def exportar_sessao(sessao_id):
    """Exporta 3 JSONs para uma sessão específica"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Verifica se sessão existe e tem dados
    cur.execute("SELECT * FROM sessoes WHERE id = ?", (sessao_id,))
    sessao = cur.fetchone()
    if not sessao:
        print(f"Sessão {sessao_id} não encontrada!")
        return False
    
    print(f"Exportando sessão {sessao_id}: {sessao['nome_pista']} - {sessao['tipo_sessao']}...")
    
    # Busca pilotos da sessão
    cur.execute("""
        SELECT p.id, p.nome, p.numero, p.posicao
        FROM pilotos p
        WHERE p.sessao_id = ?
        ORDER BY p.posicao
    """, (sessao_id,))
    pilotos_db = cur.fetchall()
    
    if not pilotos_db:
        print(f"Sessão {sessao_id} não tem pilotos!")
        conn.close()
        return False
    
    # ========== JSON 1: VOLTAS E SETORES ==========
    json_voltas = []
    for p in pilotos_db:
        pid = p["id"]
        
        cur.execute("""
            SELECT numero_volta, tempo_volta, setor1, setor2, setor3
            FROM voltas
            WHERE sessao_id = ? AND piloto_id = ?
            ORDER BY numero_volta
        """, (sessao_id, pid))
        
        voltas = []
        for v in cur.fetchall():
            voltas.append({
                "volta": v["numero_volta"],
                "tempo_total": v["tempo_volta"],
                "setor1": v["setor1"],
                "setor2": v["setor2"],
                "setor3": v["setor3"]
            })
        
        json_voltas.append({
            "nome": p["nome"],
            "numero": p["numero"],
            "position": p["posicao"],
            "num_laps": len(voltas),
            "voltas": voltas
        })
    
    # ========== JSON 2: PNEUS E STINTS ==========
    json_pneus = []
    for p in pilotos_db:
        pid = p["id"]
        
        # Busca último estado dos pneus
        cur.execute("""
            SELECT tipo_pneu, idade_voltas, pit_stops,
                   desgaste_FL, desgaste_FR, desgaste_RL, desgaste_RR
            FROM pneus
            WHERE piloto_id = ?
            ORDER BY id DESC LIMIT 1
        """, (pid,))
        pneu = cur.fetchone()
        
        # Busca stints
        cur.execute("""
            SELECT stint_numero, tipo_pneu, volta_inicio, volta_fim, total_voltas
            FROM pneu_stints
            WHERE piloto_id = ?
            ORDER BY volta_inicio
        """, (pid,))
        stints = [dict(s) for s in cur.fetchall()]
        
        # Conta voltas do piloto para fallback
        num_voltas_piloto = next((p["num_laps"] for p in json_voltas if p["numero"] == p["numero"]), 0)
        
        json_pneus.append({
            "nome": p["nome"],
            "numero": p["numero"],
            "position": p["posicao"],
            "tyres": pneu["tipo_pneu"] if pneu else "MEDIUM",
            "tyresAgeLaps": pneu["idade_voltas"] if pneu else 0,
            "pit_stops": pneu["pit_stops"] if pneu else 0,
            "tyre_wear": [
                pneu["desgaste_FL"] if pneu else 0,
                pneu["desgaste_FR"] if pneu else 0,
                pneu["desgaste_RL"] if pneu else 0,
                pneu["desgaste_RR"] if pneu else 0
            ],
            "stints": stints if stints else [{
                "stint_numero": 1,
                "tipo_pneu": pneu["tipo_pneu"] if pneu else "MEDIUM",
                "volta_inicio": 1,
                "volta_fim": num_voltas_piloto,
                "total_voltas": num_voltas_piloto
            }]
        })
    
    # ========== JSON 3: DANOS E VELOCIDADE ==========
    # ⚠️ Colunas corretas baseadas no schema do main.py
    json_danos = []
    for p in pilotos_db:
        pid = p["id"]
        
        # Busca danos (colunas corretas do DB)
        cur.execute("""
            SELECT delta_to_leader, combustivel_restante,
                   dano_asa_esquerda, dano_asa_direita, dano_asa_traseira,
                   dano_assoalho, dano_difusor, dano_sidepods
            FROM danos
            WHERE piloto_id = ?
            ORDER BY id DESC LIMIT 1
        """, (pid,))
        dano = cur.fetchone()
        
        # Busca telemetria (velocidade máxima)
        cur.execute("""
            SELECT MAX(velocidade) as vel_max, AVG(velocidade) as vel_media
            FROM telemetria
            WHERE piloto_id = ?
        """, (pid,))
        tel = cur.fetchone()
        
        json_danos.append({
            "nome": p["nome"],
            "numero": p["numero"],
            "position": p["posicao"],
            "velocidade_maxima": tel["vel_max"] if tel and tel["vel_max"] else 0,
            "velocidade_media": tel["vel_media"] if tel and tel["vel_media"] else 0,
            "delta_to_leader": dano["delta_to_leader"] if dano else "—",
            "combustivel_restante": dano["combustivel_restante"] if dano else 0,
            "danos": {
                "asa_esquerda": dano["dano_asa_esquerda"] if dano else 0,
                "asa_direita": dano["dano_asa_direita"] if dano else 0,
                "asa_traseira": dano["dano_asa_traseira"] if dano else 0,
                "assoalho": dano["dano_assoalho"] if dano else 0,
                "difusor": dano["dano_difusor"] if dano else 0,
                "sidepods": dano["dano_sidepods"] if dano else 0
            }
        })
    
    conn.close()
    
    # ========== SALVA OS 3 JSONs ==========
    os.makedirs(OUT_DIR, exist_ok=True)
    
    sessao_info = {
        "sessao_id": sessao_id,
        "nome_pista": sessao["nome_pista"],
        "tipo_sessao": sessao["tipo_sessao"],
        "total_voltas": sessao["total_voltas"],
        "velocidade_maxima_geral": sessao["velocidade_maxima_geral"]
    }
    
    # JSON 1: Voltas
    with open(os.path.join(OUT_DIR, f"sessao_{sessao_id}_voltas.json"), "w", encoding="utf-8") as f:
        json.dump({"sessao": sessao_info, "pilotos": json_voltas}, f, ensure_ascii=False, indent=2)
    
    # JSON 2: Pneus
    with open(os.path.join(OUT_DIR, f"sessao_{sessao_id}_pneus.json"), "w", encoding="utf-8") as f:
        json.dump({"sessao": sessao_info, "pilotos": json_pneus}, f, ensure_ascii=False, indent=2)
    
    # JSON 3: Danos
    with open(os.path.join(OUT_DIR, f"sessao_{sessao_id}_danos.json"), "w", encoding="utf-8") as f:
        json.dump({"sessao": sessao_info, "pilotos": json_danos}, f, ensure_ascii=False, indent=2)
    
    print(f"OK! Exportados 3 JSONs para sessão {sessao_id}:")
    print(f"  - sessao_{sessao_id}_voltas.json ({len(json_voltas)} pilotos)")
    print(f"  - sessao_{sessao_id}_pneus.json ({len(json_pneus)} pilotos)")
    print(f"  - sessao_{sessao_id}_danos.json ({len(json_danos)} pilotos)")
    
    return True

def exportar_lista_sessoes():
    """Exporta JSON com lista de sessões disponíveis"""
    sessoes = listar_sessoes()
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUT_DIR, "sessoes.json"), "w", encoding="utf-8") as f:
        json.dump({"sessoes": sessoes}, f, ensure_ascii=False, indent=2)
    
    print(f"OK! Exportada lista com {len(sessoes)} sessões para sessoes.json")
    return sessoes

if __name__ == "__main__":
    print("=== EXPORTADOR DE SESSÕES F1 ===\n")
    
    # Exporta lista de sessões
    sessoes = exportar_lista_sessoes()
    
    if not sessoes:
        print("Nenhuma sessão com dados encontrada!")
    else:
        print(f"\nSessões disponíveis:")
        for s in sessoes:
            print(f"  [{s['id']}] {s['nome_pista']} - {s['tipo_sessao']} ({s['num_pilotos']} pilotos, {s['num_voltas']} voltas)")
        
        # Pergunta qual sessão exportar
        sid = input("\nDigite o ID da sessão para exportar (ou 'all' para todas): ")
        if sid == 'all':
            for s in sessoes:
                exportar_sessao(s['id'])
        else:
            exportar_sessao(int(sid))
