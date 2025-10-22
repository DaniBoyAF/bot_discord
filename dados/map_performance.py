import matplotlib.pyplot as plt
from collections import defaultdict

# Dicionários para armazenar dados temporariamente
carros_dados = defaultdict(list)
referencia_volta = {}

def atualizar_dados_motion(idx, car_motion, tempo_volta):
    """Armazena posição e velocidade de cada carro"""
    x = car_motion.m_world_position_x
    y = car_motion.m_world_position_y
    vel = (car_motion.m_world_velocity_x**2 +
           car_motion.m_world_velocity_y**2 +
           car_motion.m_world_velocity_z**2) ** 0.5
    carros_dados[idx].append((x, y, vel, tempo_volta))


def definir_volta_referencia(idx, melhor_volta):
    """Define a volta de referência para o carro"""
    referencia_volta[idx] = melhor_volta


def gerar_mapa_performance(idx):
    """Gera gráfico colorido com base na diferença de tempo"""
    if idx not in carros_dados or idx not in referencia_volta:
        print(f"Sem dados suficientes para o carro {idx}")
        return

    dados = carros_dados[idx]
    volta_ref = referencia_volta[idx]

    xs, ys, cores = [], [], []

    for (x, y, vel, tempo) in dados:
        # compara tempo atual com volta referência
        diff = tempo - volta_ref

        if diff < -0.05:
            cor = 'purple'  # perfeito
        elif diff < 0.05:
            cor = 'green'   # bom
        else:
            cor = 'red'     # ruim

        xs.append(x)
        ys.append(y)
        cores.append(cor)

    plt.figure(figsize=(8, 6))
    plt.scatter(xs, ys, c=cores, s=3)
    plt.axis("equal")
    plt.title(f"Mapa de Performance - Carro {idx}")
    plt.show()
