from Bot.jogadores import get_jogadores
import discord
import asyncio
from utils.dictionnaries import tyres_dictionnary, ERS_dictionary
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores
estado_pneu_anterior={}

async def pitstop(ctx):
    if not ctx.send("❌ Não há dados."):
        return
    jogadores = get_jogadores()
    pitaram = []

    for p in jogadores:
        if p.name not in estado_pneu_anterior:
            estado_pneu_anterior[p.name] = p.tyresAgeLaps
        else:
            if p.tyresAgeLaps < estado_pneu_anterior[p.name]:
                pitaram.append(p.name)
            estado_pneu_anterior[p.name] = p.tyresAgeLaps

    if pitaram:
        texto = "\n Fizeram pit stop recentemente: " + ", ".join(pitaram)
    else:
        texto = "Nenhum pit stop recente detectado."

    await ctx.send(texto)
