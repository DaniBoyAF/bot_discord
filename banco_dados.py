import sqlite3

# Variável global para controlar a sessão atual
sessao_id_atual = None

# Cria o banco de dados
def criar_banco():
    conn = sqlite3.connect('f1_telemetry.db')
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
    
    # Tabela de Telemetria
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        velocidade REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado!")

# Executa ao iniciar
criar_banco()