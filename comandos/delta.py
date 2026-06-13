from discord.ext import commands
from Bot.jogadores import get_jogadores
from utils.dictionnaries import tyres_dictionnary, DRS_dict

def formatacao(ms):
    if ms == "—" or ms is None or ms <= 0:
        return "—"
    minutos = ms // 60000
    segundos = (ms % 60000) // 1000
    milissegundos = ms % 1000
    return f"{minutos}:{segundos:02}.{milissegundos:03}"

async def comando_delta(ctx, piloto: str | None=None):
    jogadores = get_jogadores()
    
    if not piloto:
        await ctx.send("❌ Especifique o nome do piloto. Ex: `.delta Nome do jogador`")
        return
    
    for j in jogadores:
        if piloto.lower() in getattr(j, 'name', '').lower():
            
            # Buscando os tempos de forma segura
            raw_best_time = getattr(j, 'bestLapTime', 0)
            raw_last_time = getattr(j, 'lastLapTime', 0)
            delta_leader = getattr(j, 'delta_to_leader', 0)
            
            # Formatando corretamente
            texto_melhor_volta = formatacao(raw_best_time)
            texto_ultima_volta = formatacao(raw_last_time)
            
            # Buscando DRS e Pneus
            drs_status = DRS_dict.get(getattr(j, 'drs', 0), 'Desconhecido')
            tyres_status = tyres_dictionnary.get(getattr(j, 'tyres', 0), 'Desconhecido')
            posicao = getattr(j, 'position', 0)
            
            msg = (
                f"⏱️ Delta do piloto **{j.name}**:\n"
                f"- Diferença para o líder: {delta_leader / 1000:.3f} segundos\n"
                f"- Posição: P{posicao}\n"
                f"- Melhor volta: {texto_melhor_volta}\n" # <- Agora está certo!
                f"- Volta anterior: {texto_ultima_volta}\n" # <- Agora está certo!
                f"- DRS: {drs_status}\n"
                f"- Tipo de pneus: {tyres_status}"
            )
            
            await ctx.send(msg)
            return
            
    await ctx.send("❌ Piloto não encontrado.")