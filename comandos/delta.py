from discord.ext import commands
from Bot.jogadores import get_jogadores
from utils.dictionnaries import tyres_dictionnary
import sys
import os

async def comando_delta(ctx, piloto: str = None):
    jogadores = get_jogadores()
    tyres_nome = tyres_dictionnary
    if not piloto:
        await ctx.send("❌ Especifique o nome do piloto. Ex: `.delta Nome do jogador`")
        return
    
    for j in jogadores:
        if piloto.lower() in j.name.lower():
            msg = (
                f"⏱️ Delta do piloto **{j.name}**:\n"
                f"- Diferença para o líder: {j.delta_to_leader / 1000:.3f} segundos\n"
                f"- Posição: {j.position}\n"
                f"- Melhor volta: {j.bestLapTime / 1000:.3f} segundos\n"
                f"- Tempo atual: {j.currentLapTime / 1000:.3f} segundos\n"
                f"- Volta anterior: {j.lastLapTime / 1000:.3f} segundos\n"
                f"- Tipo de pneus: {tyres_nome.get(j.tyres, 'Desconhecido')}"
            )
            await ctx.send(msg)
            return
    await ctx.send("❌ Piloto não encontrado.")