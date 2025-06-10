import matplotlib.pyplot as plt

def mostra_graficos_geral(jogadores, nome_arquivo="graficos_geral.png"):
    plt.figure(figsize=(10,6))

    for j in jogadores:
        if len(j.laps_info)>= 2:
            voltas =list(range(1,len(j.laps_info) + 1))
            tempos = [lap/1000 for lap in j.laps_info]
            plt.plot(voltas , tempos , label=j.name)
    plt.xlabel("Laps")
    plt.ylabel("Tempo (s)")
    plt.title("Tempos de volta por piloto")
    plt.legend()
    plt.grid(True)
    plt.savefig(nome_arquivo)
    plt.close()