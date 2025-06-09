from Bot.jogadores import get_jogadores

async def danos(ctx, piloto: str = None):
    jogadores = get_jogadores ()

    if not piloto :
        await ctx.send("❌ Especifique o nome do piloto. Ex: `.avaria Nome do jogador") 
        return
    for j in jogadores:
         if piloto.lower() in j.name.lower():
            msg = (
                f"🔧 Danos do carro de **{j.name}**:\n"
                f"- Asa Dianteira: Esq {j.FrontLeftWingDamage}% | Dir {j.FrontRightWingDamage}%\n"
                f"- Asa Traseira: {j.rearWingDamage}%\n"
                f"- Assoalho: {j.floorDamage}%\n"
                f"- Difusor: {j.diffuserDamage}%\n"
                f"- Sidepods: {j.sidepodDamage}%"
            )
            await ctx.send(msg)
            return

    await ctx.send("❌ Piloto não encontrado.")
