import matplotlib.pyplot as plt 

def mostra_graficos_geral(jogadores, total_voltas=None, nome_arquivo="graficos_geral.png"):
    from utils.dictionnaries import tyres_dictionnary
    plt.figure(figsize=(12, 6))

    melhor_tempo = float('inf')
    melhor_volta = None
    melhor_piloto = ''
    melhor_tyres = ''

    for j in jogadores:
        if hasattr(j, "voltas") and len(j.voltas) >= 2:
            for v in j.voltas:
                tempo = v.get("tempo_total", 0)
                if tempo > 0 and tempo < melhor_tempo:
                    melhor_tempo = tempo
                    melhor_volta = v.get("volta", None)
                    melhor_piloto = getattr(j, "nome", getattr(j, "name", "Piloto"))
                    melhor_tyres = tyres_dictionnary.get(getattr(j, "tyres", None), "N/A")

    for j in jogadores:
        if hasattr(j, "voltas") and len(j.voltas) >= 2:
            tempos = [v.get("tempo_total", 0) for v in j.voltas]
            voltas = [v.get("volta", i + 1) for i, v in enumerate(j.voltas)]
            nome = getattr(j, "nome", getattr(j, "name", "Piloto"))
            plt.plot(voltas, tempos, label=nome)

    plt.xlabel("Voltas")
    plt.ylabel("Tempo (s)")

    if total_voltas:
        plt.title(f"Tempos de Volta por Piloto (Total de Voltas: {total_voltas})")
    else:
        plt.title("Tempos de Volta por Piloto")

    # Melhor tempo formatado
    if melhor_volta is not None:
        minutos = int(melhor_tempo // 60)
        segundos = int(melhor_tempo % 60)
        milissegundos = int((melhor_tempo - int(melhor_tempo)) * 1000)

        texto = f"Melhor Volta: {melhor_volta} - {melhor_piloto} - {minutos:02}:{segundos:02}.{milissegundos:03} - {melhor_tyres}"
        plt.figtext(0.15, 0.97, texto, fontsize=10, color='green', ha='left', va='top')

    # Ajustes finais
    max_volta_global = max(
        max((v.get("volta", 0) for v in j.voltas), default=0)
        for j in jogadores if hasattr(j, "voltas")
    )
    plt.xlim(1, max_volta_global)
    plt.legend(loc='lower right', fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.close()