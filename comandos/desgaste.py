async def desgaste(ctx):
    """Mostra desgaste dos pneus de todos os pilotos"""
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary  
    
    jogadores = get_jogadores()
    jogadores = [j for j in jogadores if getattr(j, 'position', 0) > 0]
    jogadores = sorted(jogadores, key=lambda x: getattr(x, 'position', 99))
 
    if not jogadores:
        await ctx.send("❌ Nenhum piloto na sessão.")
        return
        
    linhas = ["```"]
    # Cabecalho (mesma ordem do pneusv: FL, FR, RL, RR) — larguras batem com a linha de dados
    linhas.append(f"{'P':<2} {'PILOTO':<15} {'FL':>5} {'FR':>5} {'RL':>5} {'RR':>5}   {'AGE':>3} {'MAX':<2} {'TIPO'}")
    linhas.append("─" * 57)
    
    for j in jogadores[:20]:
        pos = getattr(j, 'position', 0)
        nome = getattr(j, 'name', 'Unknown')[:15].ljust(15)
    
        wear = getattr(j, 'tyre_wear', None)
        # Excelente proteção que você fez!
        if not isinstance(wear, (list, tuple)) or len(wear) < 4:
            wear = (j.tyre_wear[2], j.tyre_wear[3], j.tyre_wear[0], j.tyre_wear[1])
        
        max_wear = max(j.tyre_wear[2], j.tyre_wear[3], j.tyre_wear[0], j.tyre_wear[1])
        
        # Mesmo atributo usado no pneusv.py (tyresAgeLaps, camelCase)
        age = j.tyresAgeLaps 
        
        # Emoji baseado no desgaste máximo
        if max_wear > 80:
            emoji = "🛑"
        elif max_wear > 50:
            emoji = "🟧"
        else:
            emoji = "🟩"
        
        # Índices batem com o pneusv.py: FL=2, FR=3, RL=0, RR=1
        fl, fr, rl, rr = j.tyre_wear[2], j.tyre_wear[3], j.tyre_wear[0], j.tyre_wear[1]
        tipo = tyres_dictionnary.get(j.tyres, "Desconhecido")
        if tipo == "Macio":
            tipo = "🔴"
        elif tipo == "Médio":
            tipo = "🟡" 
        elif tipo == "Duro":
            tipo = "⚪"
        elif tipo == "Intermediário":
            tipo = "🟢" 
        elif tipo == "Molhado":
            tipo = "🔵"
        elif tipo == "Supermacio":
            tipo = "🟣"
        linhas.append(f"{pos:<2} {nome} {fl:>4.0f}% {fr:>4.0f}% {rl:>4.0f}% {rr:>4.0f}%   {age:>3} {emoji} {tipo}")
    
    linhas.append("```")
    
    await ctx.send("\n".join(linhas))