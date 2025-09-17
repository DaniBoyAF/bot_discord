import matplotlib.pyplot as plt
import json 
def melhor_setor_gap(json_path, nome_arquivo="grafico_melhor_setor.png"):
    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    pilotos = []
    melhores_setores = []
    # Para cada piloto, pega o melhor tempo de setor (menor valor)
    for piloto in dados:
        nome = piloto.get("nome", "Desconhecido")
        voltas = piloto.get("voltas", [])
        # Junta todos os setores de todas as voltas
        setores = []
        for v in voltas:
            setores += v.get("setores", [])
        if setores:
            melhor = min(setores)
            pilotos.append(nome)
            melhores_setores.append(melhor)

    # Calcula o gap para o melhor setor absoluto
    melhor_absoluto = min(melhores_setores) if melhores_setores else 0
    gaps = [s - melhor_absoluto for s in melhores_setores]

    # Ordena para ficar igual ao gráfico da foto
    pilotos_gaps = sorted(zip(pilotos, gaps), key=lambda x: x[1])

    nomes_ordenados = [x[0] for x in pilotos_gaps]
    gaps_ordenados = [x[1] for x in pilotos_gaps]

    # Plota o gráfico
    plt.figure(figsize=(12, 6))
    bars = plt.bar(nomes_ordenados, gaps_ordenados, color="deepskyblue")
    plt.xlabel("Piloto")
    plt.ylabel("Gap para melhor setor (s)")
    plt.title("Best Sector Gap")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Adiciona os valores em cima das barras
    for bar, gap in zip(bars, gaps_ordenados):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{gap:.3f}", ha='center', va='bottom', fontsize=9)

    plt.savefig(nome_arquivo)
    plt.close()