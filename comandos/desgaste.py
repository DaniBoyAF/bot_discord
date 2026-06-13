async def desgaste(ctx):
    """Mostra desgaste dos pneus de todos os pilotos"""
    from Bot.jogadores import get_jogadores
    
    jogadores = get_jogadores()
    jogadores = [j for j in jogadores if getattr(j, 'position', 0) > 0]
    jogadores = sorted(jogadores, key=lambda x: getattr(x, 'position', 99))

    if not jogadores:
        await ctx.send("❌ Nenhum piloto na sessão.")
        return
        
    linhas = ["```"]
    # Cabecalho
    linhas.append("P  PILOTO          RL    RR    FL    FR   MAX  AGE")
    linhas.append("─" * 58)
    
    for j in jogadores[:20]:
        pos = getattr(j, 'position', 0)
        nome = getattr(j, 'name', 'Unknown')[:15].ljust(15)
        
        wear = getattr(j, 'tyre_wear', [0, 0, 0, 0])
        # Excelente proteção que você fez!
        if not isinstance(wear, (list, tuple)) or len(wear) < 4:
            wear = [0, 0, 0, 0]
        
        max_wear = max(wear)
        
        # PROTEÇÃO EXTRA AQUI: tenta camelCase e snake_case
        age = getattr(j, 'tyres_age_laps', getattr(j, 'tyresAgeLaps', 0)) or 0
        
        # Emoji baseado no desgaste máximo
        if max_wear > 80:
            emoji = "🔴"
        elif max_wear > 50:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        # RL, RR, FL, FR batem exatamente com o índice 0, 1, 2, 3 do F1!
        linhas.append(f"{pos:<2} {nome} {wear[0]:>4.0f}% {wear[1]:>4.0f}% {wear[2]:>4.0f}% {wear[3]:>4.0f}%  {max_wear:>3.0f}% {age:>3} {emoji}")
    
    linhas.append("```")
    
    await ctx.send("\n".join(linhas))