import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
async def commando_piloto(ctx):
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()
    text = "🏁 **Pilotos na corrida:**\n\n"
    tudo = sorted(jogadores,key=lambda j: j.position )[:22]
    texto="\n".join([f"{j.position}º - {j.name}" for j in tudo])
    await ctx.send(f"🏆 Geral da corrida:\n```{texto}```")

    await ctx.send(text)