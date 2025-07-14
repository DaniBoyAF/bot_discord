
from utils.dictionnaries import tyres_dictionnary, ERS_dictionary , pit_dictionary
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores
def formatacao(ms):
    if ms == "—" or ms is None:
        return "—"
    minutos = ms // 60000
    segundos = (ms % 60000) // 1000
    milissegundos = ms % 1000
    return f"{minutos}:{segundos:02}.{milissegundos:03}"

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
    raw_best_time = selecionado.bestLapTime
    raw_Last_time = selecionado.lastLapTime
    formatando2 = formatacao(raw_Last_time)
    formatado = formatacao(raw_best_time)
    nome = selecionado.name
    pos = selecionado.position
    pneus = tyres_dictionnary.get(selecionado.tyres, "desconhecido")
    voltas_pneu = selecionado.tyresAgeLaps
    energia = ERS_dictionary.get(selecionado.ERS_mode, "desconhecido")
    percentual_ers = f"{selecionado.ERS_pourcentage:.0f}%"
    combustivel = round(selecionado.fuelRemainingLaps, 2)
    pit = pit_dictionary.get(selecionado.pit, "desconhecido")
    aviso = selecionado.warnings
    if aviso == 3:
        aviso = 0 # recomeçar a contagem de avisos
    penalties = selecionado.penalties

    linhas = ["NAME    POS     TYRES     TYRES_AGE   BEST_LAP   LAST_LAP   ERS_MODE   FUEL   WARNINGS   PENALTIES   PIT"]

    linhas.append(
        f"{nome:<14} {pos} {pneus} {voltas_pneu} {formatado:.3f} {formatando2:.3f} {percentual_ers} {energia} {aviso} {penalties}  {pit}  {combustivel:.2f}L"
    )
    mensagem = "```\n" + "\n".join(linhas) + "\n```"
    await ctx.send(mensagem)
