from discord.ext import commands
from Bot.jogadores import get_jogadores
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores

async def comando_delta(ctx):
    if not ctx.send("❌ Não há dados."):
        return

    jogadores = get_jogadores()
    validos = [p for p in jogadores if not p.hasRetired and p.bestLapTime > 0]

    if not validos:
        texto = "Nenhum piloto com volta válida ainda."
    else:
        melhor = min(validos, key=lambda p: p.bestLapTime)
        tempo = melhor.bestLapTime / 1000
        minutos = int(tempo // 60)
        segundos = tempo % 60
        texto = (f"{melhor.name} é o mais rápido da pista com {minutos} minuto e {segundos:.3f} segundos.")
    await ctx.send(texto)