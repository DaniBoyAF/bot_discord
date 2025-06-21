
from utils.dictionnaries import tyres_dictionnary, ERS_dictionary
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores

async def comando_status(ctx, *, piloto: str = None):
    jogadores = get_jogadores()
    selecionado = None

    # Buscar piloto por posição (ex: ".status 1")
    if piloto and piloto.isdigit():
        pos = int(piloto)
        selecionado = next((j for j in jogadores if j.position == pos), None)
    elif piloto:
        # Buscar por nome parcial (ex: ".status leclerc")
        selecionado = next((j for j in jogadores if piloto.lower() in j.name.lower()), None)

    if not selecionado:
        await ctx.send("❌ Piloto não encontrado. Use o número da posição ou parte do nome.")
        return

    nome = selecionado.name
    pos = selecionado.position
    pneus = tyres_dictionnary.get(selecionado.tyres, "desconhecido")
    voltas_pneu = selecionado.tyresAgeLaps
    melhor_volta = selecionado.bestLapTime
    last_lap = selecionado.lastLapTime
    energia = ERS_dictionary.get(selecionado.ERS_mode, "desconhecido")
    percentual_ers = f"{selecionado.ERS_pourcentage:.0f}%"
    combustivel = round(selecionado.fuelRemainingLaps, 2)

    texto = (
        f"📻 Status de {nome}: posição {pos}, com pneu {pneus} há {voltas_pneu} voltas. "
        f"Melhor volta em {melhor_volta:.3f} segundos. "
        f"Última volta em {last_lap:.3f} segundos. "
        f"Diferença da melhor pra ultima volta: {melhor_volta - last_lap:.3f} segundos. "
        f"ERS em {percentual_ers}, modo {energia}. "
        f"Combustível restante para {combustivel} voltas."
    )
    await ctx.send(texto)
  