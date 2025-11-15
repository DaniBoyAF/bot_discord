from utils.dictionnaries import tyres_dictionnary  
from Bot.jogadores import get_jogadores
async def comando_pneusv(ctx,*, piloto: str | None=None):
    jogadores = get_jogadores()
   
    if not piloto:
        await ctx.send("❌ Nenhum piloto encontrado. Ex: pneusv. Nome do jogador")
        return
    for p in jogadores:
            if piloto.lower() in p.name.lower():
                tipo = tyres_dictionnary.get(p.tyres, "Desconhecido")
                texto=(f"Pneus do carro de **{p.name:<14}** com o pneu **{tipo}**:\n"
             f"- TyresAge: {p.tyresAgeLaps} Laps\n" #[FL, FR, RL, RR]
             f"- Porcentagem de desgaste dos pneus:\n"
             f"- TyresWear FL: {p.tyre_wear[2]:.2f}% | TyresWear FR: {p.tyre_wear[3]:.2f}%\n" 
             f"- TyresWear RL: {p.tyre_wear[0]:.2f}% | TyresWear RR: {p.tyre_wear[1]:.2f}%\n"
             f"- Temperatura dos Pneus: primeiro a da superfície e depois a interna.\n"
             f"- TyresTemp FL: {p.tyres_temp_surface[2]}°C | {p.tyres_temp_inner[2]}°C\n" 
             f"- TyresTemp FR: {p.tyres_temp_surface[3]}°C | {p.tyres_temp_inner[3]}°C\n" 
             f"- TyresTemp RL: {p.tyres_temp_surface[0]}°C | {p.tyres_temp_inner[0]}°C\n" 
             f"- TyresTemp RR: {p.tyres_temp_surface[1]}°C | {p.tyres_temp_inner[1]}°C\n" 
             )
                await ctx.send(texto)
                return
    await ctx.send("❌ Piloto não encontrado.")
    # Se nenhum piloto foi encontrado
