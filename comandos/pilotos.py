from Bot.jogadores import get_jogadores

async def commando_piloto(ctx):
    jogadores = get_jogadores
    jogadores_ordem = sorted(jogadores,lambda j : j.position)

    text = "🏁 **Pilotos na corrida:**\n\n"
    for j in jogadores_ordem :
        if j.position > 0 :
             text += f"{j.position}º {j.name}\n"

    await ctx.send(text)