from Bot.jogadores import get_jogadores
from utils.dictionnaries import tyres_dictionnary
async def danos(ctx, piloto: str | None=None):
    jogadores = get_jogadores ()
    tyres_nomes = tyres_dictionnary
    if not piloto :
        await ctx.send("❌ Especifique o nome do piloto. Ex: `.danos Nome do jogador") 
        return
    
    for j in jogadores:
         if piloto.lower() in j.name.lower():
            msg = (
                f"🔧 Danos do carro de **{j.name}** com o pneu **{tyres_nomes.get(j.tyres, 'Desconhecido'):<12}**:\n"
                f"- Asa Dianteira: Esq {j.FrontLeftWingDamage}% | Dir {j.FrontRightWingDamage}%\n"
                f"- Asa Traseira: {j.rearWingDamage}%\n"
                f"- Assoalho: {j.floorDamage}%\n"
                f"- Difusor: {j.diffuserDamage}%\n"
                f"- Sidepods: {j.sidepodDamage}%\n"
            )
            await ctx.send(msg)
            return
    # Se nenhum piloto foi encontrado
    await ctx.send("❌ Piloto não encontrado.")
