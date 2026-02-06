import sqlite3

# Variável global para controlar a sessão atual
sessao_id_atual = None

DB_PATH = "f1_telemetry.db"

def _ajustar_sqlite_sequence(conn, table_name):
    """Ajusta o contador do AUTOINCREMENT para não pular IDs"""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
        max_id = cur.fetchone()[0]
        cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table_name,))
        if max_id > 0:
            cur.execute("INSERT INTO sqlite_sequence(name, seq) VALUES(?, ?)", (table_name, int(max_id)))
    except sqlite3.OperationalError:
        return

def atualizar_estrutura_setups(conn):
    """Adiciona colunas que podem estar faltando em bancos de dados antigos"""
    cursor = conn.cursor()
    colunas_novas = [
        ("freio_motor", "INTEGER DEFAULT 100"),
        ("front_camber", "REAL DEFAULT -3.00"),
        ("rear_camber", "REAL DEFAULT -1.50"),
        ("front_toe", "REAL DEFAULT 0.05"),
        ("rear_toe", "REAL DEFAULT 0.20")
    ]
    
    for nome_col, tipo in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE setups ADD COLUMN {nome_col} {tipo}")
            print(f"✅ Coluna {nome_col} adicionada à tabela setups.")
        except sqlite3.OperationalError:
            # Se der erro operacional, é porque a coluna já existe
            pass

# Cria o banco de dados
def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de Sessões
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_pista TEXT,
        tipo_sessao TEXT,
        total_voltas INTEGER,
        clima TEXT,
        temperatura_ar REAL,
        temperatura_pista REAL,
        porcentagem_chuva INTEGER,
        safety_car_status TEXT,
        flag TEXT,
        velocidade_maxima_geral REAL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de Pilotos (por sessão)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pilotos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        nome TEXT,
        numero INTEGER,
        posicao INTEGER,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id)
    )
    ''')
    
    # Tabela de Voltas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voltas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        numero_volta INTEGER,
        tempo_volta REAL,
        setor1 REAL,
        setor2 REAL,
        setor3 REAL,
        velocidade_max REAL,
        combustivel_volta REAL,
        desgaste_pneu REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de Pneus
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pneus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        tipo_pneu TEXT,
        idade_voltas INTEGER,
        desgaste_RL REAL,
        desgaste_RR REAL,
        desgaste_FL REAL,
        desgaste_FR REAL,
        temp_interna_RL REAL,
        temp_interna_RR REAL,
        temp_interna_FL REAL,
        temp_interna_FR REAL,
        temp_superficie_RL REAL,
        temp_superficie_RR REAL,
        temp_superficie_FL REAL,
        temp_superficie_FR REAL,
        vida_util REAL,
        tyre_set_data REAL,
        lap_delta_time REAL,
        pit_stops INTEGER,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de Danos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS danos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        delta_to_leader TEXT,
        combustivel_restante REAL,
        dano_asa_esquerda REAL,
        dano_asa_direita REAL,
        dano_asa_traseira REAL,
        dano_assoalho REAL,
        dano_difusor REAL,
        dano_sidepods REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de Telemetria (EXPANDIDA)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        numero_volta INTEGER,
        velocidade REAL,
        rpm INTEGER,
        marcha INTEGER,
        acelerador REAL,
        freio REAL,
        posicao_volante REAL,
        ers_bateria REAL,
        ers_modo INTEGER,
        combustivel_kg REAL,
        combustivel_voltas REAL,
        combustivel_mix INTEGER,
        drs_ativo INTEGER,
        distancia_volta REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')

    # Tabela de Setups (COMPLETA - Todos os campos do jogo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS setups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        piloto_nome TEXT,
        pista TEXT,
        tipo_sessao TEXT,
        
        -- Aerodinâmica
        asa_dianteira INTEGER,
        asa_traseira INTEGER,
        
        -- Diferencial
        diff_on_throttle INTEGER,
        diff_off_throttle INTEGER,
        
        -- Freios
        freio_pressao INTEGER,
        freio_balanco INTEGER,
        freio_motor INTEGER,
        
        -- Suspensão
        suspensao_diant INTEGER,
        suspensao_tras INTEGER,
        barra_antirrolagem_diant INTEGER,
        barra_antirrolagem_tras INTEGER,
        altura_diant INTEGER,
        altura_tras INTEGER,
        
        -- Geometria de Suspensão
        front_camber REAL,
        rear_camber REAL,
        front_toe REAL,
        rear_toe REAL,
        
        -- Pressão Pneus (PSI)
        pressao_pneu_fl REAL,
        pressao_pneu_fr REAL,
        pressao_pneu_rl REAL,
        pressao_pneu_rr REAL,
        
        -- Combustível
        combustivel_inicial REAL,
        
        -- Performance Calculada
        melhor_volta REAL,
        media_volta REAL,
        avg_setor1 REAL,
        avg_setor2 REAL,
        avg_setor3 REAL,
        top_speed REAL,
        degradacao_media REAL,
        consistencia REAL,
        total_voltas INTEGER,
        
        -- Classificação Automática
        tipo_setup TEXT,
        estilo_pilotagem TEXT,
        
        data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')

    # Tabela de Stints de Pneus (Para Análise de Degradação)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pneu_stints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        piloto_nome TEXT,
        stint_numero INTEGER,
        tipo_pneu TEXT,
        volta_inicio INTEGER,
        volta_fim INTEGER,
        total_voltas INTEGER,
        desgaste_inicio REAL,
        desgaste_fim REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')

    conn.commit()

    # Ajusta sequências para não pular IDs
    for t in ("sessoes", "pilotos", "voltas", "pneus", "danos", "telemetria", "setups", "pneu_stints"):
        _ajustar_sqlite_sequence(conn, t)

    conn.commit()
    conn.close()
    print("✅ Banco de dados criado/atualizado com Telemetria, Setups e Stints!")

# Executa ao iniciar
criar_banco()