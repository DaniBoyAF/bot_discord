import json

async def comando_media(ctx):
    with open("dados_salvar.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
    medias = {}
    for jogador in dados:
        nome = jogador["nome"]
        voltas = jogador["voltas"]
        # Só considera voltas completas (3 setores preenchidos e > 0)
        voltas_completas = [v for v in voltas if len(v.get("setores", [])) == 3 and all(s > 0 for s in v.get("setores", []))]
        tempos = [v["tempo_total"] for v in voltas_completas if "tempo_total" in v]
        if tempos:
            medias[nome] = sum(tempos) / len(tempos)
    if not medias:
        await ctx.send("Nenhum dado de média encontrado.")
        return
    medias_ordenadas = sorted(medias.items(), key=lambda x: x[1])
    melhor_media = medias_ordenadas[0][1]

    linhas = []
    for idx, (nome, media) in enumerate(medias_ordenadas, 1):
        if idx == 1:
            linhas.append(f"{idx}) {nome:<15} Quickest")
        else:
            diff = media - melhor_media
            linhas.append(f"{idx}) {nome:<15} +{diff:.2f} s/lap")

    mensagem = "```\n" + "\n".join(linhas) + "\n```"
    await ctx.send(mensagem)