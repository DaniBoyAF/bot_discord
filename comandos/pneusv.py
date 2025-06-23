from utils.dictionnaries import tyres_dictionnary  
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores


async def comando_pneusv(ctx):
    if not ctx.send("❌ Não há dados."):
        return

    jogadores = get_jogadores()
    top22 = sorted([p for p in jogadores if not p.hasRetired], key=lambda x: x.position)[:22]

    mensagens = []
    for p in top22:
        tipo = tyres_dictionnary.get(p.tyres, "Desconhecido")
        mensagens.append(f"{p.name}: {p.tyresAgeLaps} voltas com pneu {tipo}")

    texto = "📻 Situação dos pneus dos 22 primeiros:\n " + ". ".join(mensagens)
    await ctx.send(texto)