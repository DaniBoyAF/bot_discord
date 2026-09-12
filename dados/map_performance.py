from collections import defaultdict, deque
import matplotlib.pyplot as plt


# ═══════════════════════════════════════════════════════════════════
#  ARMAZENAMENTO
# ═══════════════════════════════════════════════════════════════════
#  Cada carro guarda uma deque de tuplas (x, z, vel, tempo_volta).
#  A deque tem tamanho máximo para não estourar a RAM durante
#  uma corrida longa (o parser manda ~60 pacotes/s por carro).
#
#  Eixos:
#    X = posição horizontal (mundo)
#    Z = posição "no chão"  (mundo)  ← este é o que forma o mapa top-down
#    Y = ALTURA do carro em relação ao solo (Eau Rouge etc.) — NÃO usar no mapa
# ═══════════════════════════════════════════════════════════════════

MAX_PONTOS_POR_CARRO = 20000   # ≈ 5,5 min a 60 Hz; ajuste se quiser mais

carros_dados = defaultdict(lambda: deque(maxlen=MAX_PONTOS_POR_CARRO))
referencia_volta = {}


# ═══════════════════════════════════════════════════════════════════
#  ATUALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════
def atualizar_dados_motion(idx, car_motion, tempo_volta):
    """
    Armazena posição (x, z) e velocidade resultante de cada carro.

    Args:
        idx        : índice do carro no array do jogo (0..21)
        car_motion : CarMotionData do pacote UDP
        tempo_volta: tempo da volta atual (opcional, usado no plot)
    """
    x = car_motion.m_world_position_x
    z = car_motion.m_world_position_z          # ← chão, não Y

    # módulo da velocidade vetorial (m/s)
    vx = car_motion.m_world_velocity_x
    vy = car_motion.m_world_velocity_y
    vz = car_motion.m_world_velocity_z
    vel = (vx * vx + vy * vy + vz * vz) ** 0.5

    carros_dados[idx].append((x, z, vel, tempo_volta))


def definir_volta_referencia(idx, melhor_volta):
    """Define a volta de referência (best lap) para o carro idx."""
    referencia_volta[idx] = melhor_volta


# ═══════════════════════════════════════════════════════════════════
#  UTILITÁRIOS PARA O FLASK
# ═══════════════════════════════════════════════════════════════════
def get_ultima_posicao(idx):
    """
    Retorna (x, z, vel, tempo_volta) do último pacote recebido,
    ou None se ainda não há dados para esse carro.
    """
    d = carros_dados.get(idx)
    if not d:
        return None
    return d[-1]


def get_tracado(idx):
    """
    Retorna a lista completa de pontos [(x, z, vel, tempo), ...]
    para o carro idx (limitado ao MAX_PONTOS_POR_CARRO).
    """
    return list(carros_dados.get(idx, []))


def limpar_carro(idx):
    """Limpa os dados de um carro específico."""
    if idx in carros_dados:
        carros_dados[idx].clear()


def limpar_tudo():
    """Limpa todos os carros e referências (ex.: trocou de pista)."""
    carros_dados.clear()
    referencia_volta.clear()


# ═══════════════════════════════════════════════════════════════════
#  PLOT (matplotlib, uso manual/offline)
# ═══════════════════════════════════════════════════════════════════
def gerar_mapa_performance(idx):
    """
    Gera um gráfico scatter colorido pela diferença de tempo
    em relação à volta de referência do carro.
    """
    if idx not in carros_dados or not carros_dados[idx]:
        print(f"[map_performance] Sem dados para o carro {idx}")
        return

    if idx not in referencia_volta:
        print(f"[map_performance] Sem volta de referência para o carro {idx}")
        return

    dados   = list(carros_dados[idx])
    volta_ref = referencia_volta[idx]

    xs, zs, cores = [], [], []
    for (x, z, vel, tempo) in dados:
        diff = tempo - volta_ref

        if diff < -0.05:
            cor = 'purple'   # abaixo da referência → perfeito
        elif diff < 0.05:
            cor = 'green'    # dentro da tolerância
        else:
            cor = 'red'      # acima → perdeu tempo

        xs.append(x)
        zs.append(z)
        cores.append(cor)

    plt.figure(figsize=(8, 6))
    plt.scatter(xs, zs, c=cores, s=3)
    plt.axis("equal")
    plt.title(f"Mapa de Performance — Carro {idx}")
    plt.xlabel("X")
    plt.ylabel("Z")
    plt.grid(alpha=0.2)
    plt.show()