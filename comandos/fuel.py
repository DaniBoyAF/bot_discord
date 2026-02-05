async def fuel(ctx):
    """Mostra combustível de todos os pilotos"""
    from Bot.jogadores import get_jogadores
    
    jogadores = get_jogadores()
    jogadores = [j for j in jogadores if getattr(j, 'position', 0) > 0]
    jogadores = sorted(jogadores, key=lambda x: getattr(x, 'position', 99))
    
    if not jogadores:
        await ctx.send("❌ Nenhum piloto na sessão")
        return
    
    mix_names = {0: '🟢Lean', 1: '⚪Std', 2: '🟡Rich', 3: '🔴Max'}
    
    linhas = ["```"]
    linhas.append("P  PILOTO           FUEL(kg)  LAPS   MIX")
    linhas.append("─" * 50)
    
    for j in jogadores[:20]:
        pos = getattr(j, 'position', 0)
        nome = getattr(j, 'name', 'Unknown')[:15].ljust(15)
        fuel = getattr(j, 'fuel_in_tank', 0)
        laps = getattr(j, 'fuel_remaining_laps', 0)
        mix = mix_names.get(getattr(j, 'fuel_mix', 1), '⚪Std')
        
        # Emoji baseado nas voltas restantes
        if laps < 1:
            emoji = "🔴"
        elif laps < 3:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        linhas.append(f"{pos:<2} {nome} {fuel:>6.1f}   {laps:>5.1f}  {mix} {emoji}")
    
    linhas.append("```")