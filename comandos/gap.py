from Bot.jogadores import get_jogadores
import discord
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def comando_gap(ctx):
    if not ctx.send("❌ Não há dados."):
        return

    jogadores = get_jogadores()
    top3 = sorted([p for p in jogadores if not p.hasRetired], key=lambda x: x.position)[:3]

    if len(top3) < 2:
        await ctx.send("❌ Não há pilotos suficientes.")
        return

    lider = top3[0]
    falas = []
    for p in top3[1:]:
        gap = (p.bestLapTime - lider.bestLapTime)
        falas.append(f"{p.name} está a {gap:.3f} segundos de {lider.name}")

    texto = "Diferença entre os 3 primeiros: " + ". ".join(falas)
    
    await ctx.send(texto)