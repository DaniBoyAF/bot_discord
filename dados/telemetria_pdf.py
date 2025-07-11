import matplotlib.pyplot as plt

def mostra_graficos_geral(jogadores, total_voltas=None, nome_arquivo="graficos_geral.png"):
    plt.figure(figsize=(10,6))
    melhor_tempo = float('inf')
    melhor_volta = None
    melhor_piloto = ''
    for j in jogadores:

        if hasattr(j,"voltas") and len(j.voltas)>=2:
            for v in j.voltas:
                tempo = v.get("tempo_total", 0)
                if tempo > 0 and tempo < melhor_tempo:
                    melhor_tempo = tempo
                    melhor_volta = v.get("volta", None)
                    melhor_piloto = getattr(j, "nome", getattr(j, "name", "Piloto"))
                   
    for j in jogadores:
        # Usa o campo 'voltas' do JSON
        if hasattr(j, "voltas") and len(j.voltas) >= 2:
            voltas = [v.get("volta", i+1) for i, v in enumerate(j.voltas)]
            tempos = [v.get("tempo_total", 0) for v in j.voltas]
            plt.plot(voltas, tempos, label=getattr(j, "nome", getattr(j, "name", "Piloto")))
    plt.xlabel("Voltas")
    plt.ylabel("Tempo (s)")
    if total_voltas:
        plt.title(f"Tempos de Volta por Piloto (Total de Voltas: {total_voltas})")
    else:
        plt.title("Tempos de Volta por Piloto")
    minutos = int(melhor_tempo // 60)
    segundos = int(melhor_tempo % 60)
    milissegundos = int((melhor_tempo - int(melhor_tempo)) * 1000)
    j.tyres = getattr(j, 'tyres', 'N/A')  # Verifica se o atributo 'tyres' existe
    tyres_dictionnary = {
    0:"Macio",
    16: "Macio",
    17: "Médio",
    18: "Duro",
    7: "Intermediário",
    8: "Molhado",
    #F2 2024
    11: "Supermacio",
    12: "Macio",
    13: "Médio",
    14: "Duro",
    15: "Chuva"
        }

    if melhor_volta is not None:
        plt.text(0.05, 0.97, f"Melhor volta: {melhor_volta} ({melhor_piloto}) - {melhor_tempo:.3f}s Pneus - {tyres_dictionnary.get(j.tyres, 'N/A')}",
                fontsize=10, color='green', ha='left', va='top')
    if melhor_tempo is not None:
        plt.figtext(0.15, 0.97, f"Melhor tempo: {minutos:02d}:{segundos:02d}.{milissegundos:03d}s ({melhor_piloto} - {tyres_dictionnary.get(j.tyres, 'N/A')})", fontsize=20, color='green', ha='left', va='top')
    plt.legend(loc='lower right', fontsize=8)  # legenda no canto inferior direito
    max_volta_global =max(
    max((v.get("volta", 0) for v in j.voltas),default=0)
    for j in jogadores 
    )
    plt.xlim(1,max_volta_global)
    plt.grid(True)
    plt.savefig(nome_arquivo)
    plt.close()