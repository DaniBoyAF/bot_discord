async def ers(ctx):
    """Mostra ERS de todos os pilotos"""
    from Bot.jogadores import get_jogadores

    try:
        jogadores = get_jogadores()
        jogadores = [j for j in jogadores if (getattr(j, 'position', 0) or 0) > 0]
        jogadores = sorted(jogadores, key=lambda x: (getattr(x, 'position', None) or 99))

        if not jogadores:
            await ctx.send("❌ Nenhum piloto na sessão")
            return

        mode_names = {0: 'None', 1: 'Medium', 2: 'Hotlap', 3: 'Overtake'}

        linhas = ["```"]
        linhas.append("P  PILOTO                   ERS%   MODE      DRS")
        linhas.append("─" * 50)

        ERS_MAX = 4000000  # 4MJ

        for j in jogadores[:20]:
            pos = getattr(j, 'position', 0) or 0
            nome = (getattr(j, 'name', None) or 'Unknown')[:15].ljust(15)

            ers_energy = getattr(j, 'ers_store_energy', None)
            sem_dados = not isinstance(ers_energy, (int, float))

            if sem_dados:
                linhas.append(f"{pos:<2} {nome} {'░'*10}  --%   {'—':<8} ⚪ SEM DADOS")
                continue

            ers_percent = max(0, min(100, (ers_energy / ERS_MAX) * 100))
            ers_mode = mode_names.get(getattr(j, 'ers_deploy_mode', 0) or 0, 'None')
            drs_val  = getattr(j, 'drs_allowed', None)
            drs = "✅" if drs_val == 1 else "❌"

            bars = int(ers_percent / 10)
            bar_visual = "█" * bars + "░" * (10 - bars)

            linhas.append(f"{pos:<2} {nome} {bar_visual} {ers_percent:>4.0f}%  {ers_mode:<8} {drs}")

        linhas.append("```")
        await ctx.send("\n".join(linhas))

    except Exception as e:
        await ctx.send(f"❌ Erro ao gerar ERS: {e}")