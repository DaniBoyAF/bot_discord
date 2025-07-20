from discord.ext import commands
from Bot.jogadores import get_jogadores
from utils.dictionnaries import tyres_dictionnary , DRS_dict
import sys
import os
def formatacao(ms):
    if ms == "—" or ms is None:
        return "—"
    minutos = ms // 60000
    segundos = (ms % 60000) // 1000
    milissegundos = ms % 1000
    return f"{minutos}:{segundos:02}.{milissegundos:03}"

async def comando_delta(ctx, piloto: str = None):
    jogadores = get_jogadores()
    tyres_nome = tyres_dictionnary
    
    if not piloto:
        await ctx.send("❌ Especifique o nome do piloto. Ex: `.delta Nome do jogador`")
        return
    
    for j in jogadores:
        if piloto.lower() in j.name.lower():
            raw_best_time = j.bestLapTime
            raw_Last_time = j.lastLapTime
            formatando2 = formatacao(raw_Last_time)
            formatado = formatacao(raw_best_time)
            msg = (
                f"⏱️ Delta do piloto **{j.name}**:\n"
                f"- Diferença para o líder: {j.delta_to_leader / 1000:.3f} segundos\n"
                f"- Posição: {j.position}\n"
                f"- Melhor volta: {formatando2} \n"
                f"- DRS: {DRS_dict.get(j.drs, 'Desconhecido')} \n"
                f"- Volta anterior: {formatado} \n"
                f"- Tipo de pneus: {tyres_nome.get(j.tyres, 'Desconhecido')}"
            )
            await ctx.send(msg)
            return
    await ctx.send("❌ Piloto não encontrado.")