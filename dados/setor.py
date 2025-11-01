import matplotlib.pyplot as plt
import json
import random
def gerar_cor_aleatoria():
    return "rgb({},{},{})".format(random.randint(0,255), random.randint(0,255), random.randint(0,255))
def melhor_setor_gap(json_path="dados_de_voltas.json", nome_arquivo_prefix="grafico_melhor_setor"):
    with open(json_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Supondo que cada volta tem uma lista 'setores' com 3 tempos
    num_setores = 3  # ajuste se tiver mais setores

    for setor_idx in range(num_setores):
        pilotos = []
        melhores_setores = []
        for piloto in dados:
            nome = piloto.get("nome", "Desconhecido")
            voltas = piloto.get("voltas", [])
            # Pega todos os tempos desse setor nas voltas
            tempos_setor = [v.get("setores", [])[setor_idx] for v in voltas if len(v.get("setores", [])) > setor_idx]
            if tempos_setor:
                melhor = min(tempos_setor)
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
        color_aleatorias = [gerar_cor_aleatoria()for _ in nome]
        plt.figure(figsize=(12, 6))
        bars = plt.bar(nomes_ordenados, gaps_ordenados, color=color_aleatorias)
        plt.xlabel("Piloto")
        plt.ylabel(f"Gap para melhor setor {setor_idx+1} (s)")
        plt.title(f"Best Sector {setor_idx+1} Gap")
        plt.xticks(rotation=45)
        plt.tight_layout()
        # Adiciona os valores em cima das barras
        for bar, gap in zip(bars, gaps_ordenados):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{gap:.3f}", ha='center', va='bottom', fontsize=9)
        plt.savefig(f"{nome_arquivo_prefix}_setor{setor_idx+1}.png")
        plt.close()