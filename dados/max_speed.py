import matplotlib.pyplot as plt 

def graficos_speed_max(jogadores, nome_arquivo="graficos_speed_max.png"):
    nomes =[]
    velocidade=[]
    for j in jogadores:
        if hasattr(j, "voltas") and j.voltas :
            nomes.append(getattr(j, "nome", getattr(j, "name")))
            velocidade.append([v.get("speed", 0) for v in j.voltas])
        if velocidade:
            media = max(velocidade) if velocidade else 0
        
        else:
            nomes.append(getattr(j,"nome", getattr(j,"name","Piloto")))
            velocidade.append(media)

    plt.figure(figsize=(10, 6))
    plt.bar(nomes, velocidade, color="blue")
    plt.xlabel("Pilotos")
    plt.ylabel("Velocidade Maxima")
    plt.title("Velocidade Maxima dos Pilotos")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.show()

