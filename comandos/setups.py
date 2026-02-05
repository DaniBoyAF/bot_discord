import discord
from discord.ext import commands


async def setups(ctx,piloto: str | None): 
    """Mostra o setup de um piloto - .setup ou .setup NomePiloto"""
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()
    jogadores = [j for j in jogadores if getattr(j, 'position', 0)]

    if not jogadores:
        await ctx.send("❌ Nenhum piloto na sessão.")
        return
    # Encontra o piloto
    if piloto:
      j = next((p for p in jogadores if piloto.lower() in getattr(p, 'name', '').lower()), None)
      if not j:
            await ctx.send(f"❌ Piloto '{piloto}' não encontrado")
            return
    else:
        # Pega o primeiro piloto humano ou o líder
        j = jogadores[0]
    
    nome = getattr(j, 'name', 'Desconhecido')
    pos = getattr(j, 'position', '?')
    
    embed = discord.Embed(
        title=f"🔧 Setup de {nome} (P{pos})",
        color=discord.Color.blue()
    )
    
    # ✈️ Aerodinâmica
    embed.add_field(
        name="✈️ Aerodinâmica",
        value=f"Asa Diant: **{getattr(j, 'front_wing', '?')}**\n"
              f"Asa Tras: **{getattr(j, 'rear_wing', '?')}**",
        inline=True
    )
    
    # 🛑 Freios
    embed.add_field(
        name="🛑 Freios",
        value=f"Pressão: **{getattr(j, 'brake_pressure', '?')}%**\n"
              f"Balanço: **{getattr(j, 'brake_bias', '?')}%**",
        inline=True
    )
    
    # ⚙️ Diferencial
    embed.add_field(
        name="⚙️ Diferencial",
        value=f"On Throttle: **{getattr(j, 'diff_on_throttle', '?')}%**\n"
              f"Off Throttle: **{getattr(j, 'diff_off_throttle', '?')}%**",
        inline=True
    )
    
    # 🔧 Suspensão
    embed.add_field(
        name="🔧 Suspensão",
        value=f"Diant: **{getattr(j, 'front_suspension', '?')}** | Tras: **{getattr(j, 'rear_suspension', '?')}**\n"
              f"Altura D: **{getattr(j, 'front_suspension_height', '?')}** | T: **{getattr(j, 'rear_suspension_height', '?')}**\n"
              f"Anti-Roll D: **{getattr(j, 'front_anti_roll_bar', '?')}** | T: **{getattr(j, 'rear_anti_roll_bar', '?')}**",
        inline=False
    )
    
    # 🛞 Pressão dos Pneus
    embed.add_field(
        name="🛞 Pressão Pneus (PSI)",
        value=f"FL: **{getattr(j, 'tyre_pressure_fl', 0):.1f}** | FR: **{getattr(j, 'tyre_pressure_fr', 0):.1f}**\n"
              f"RL: **{getattr(j, 'tyre_pressure_rl', 0):.1f}** | RR: **{getattr(j, 'tyre_pressure_rr', 0):.1f}**",
        inline=True
    )
    
    # ⛽ Combustível
    embed.add_field(
        name="⛽ Combustível",
        value=f"Carga Inicial: **{getattr(j, 'fuel_load', 0):.1f} kg**",
        inline=True
    )
    
    await ctx.send(embed=embed)

