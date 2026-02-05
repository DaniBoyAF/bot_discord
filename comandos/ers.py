import discord
from discord.ext import commands

async def ers(ctx):
  """Mostra ERS de todos os pilotos"""
  from Bot.jogadores import get_jogadores
    
  jogadores = get_jogadores()
  jogadores = [j for j in jogadores if getattr(j, 'position', 0) > 0]
  jogadores = sorted(jogadores, key=lambda x: getattr(x, 'position', 99))
    
  if not jogadores:
      await ctx.send("❌ Nenhum piloto na sessão")
      return
    
  mode_names = {0: 'None', 1: 'Medium', 2: 'Hotlap', 3: 'Overtake'}
    
  linhas = ["```"]
  linhas.append("P  PILOTO           ERS%   MODE      DRS")
  linhas.append("─" * 50)
    
    # ERS max é 4MJ = 4000000 Joules
  ERS_MAX = 4000000
    
  for j in jogadores[:20]:
        pos = getattr(j, 'position', 0)
        nome = getattr(j, 'name', 'Unknown')[:15].ljust(15)
        
        ers_energy = getattr(j, 'ers_store_energy', 0)
        ers_percent = (ers_energy / ERS_MAX) * 100 if ERS_MAX > 0 else 0
        ers_mode = mode_names.get(getattr(j, 'ers_deploy_mode', 0), 'None')
        drs = "✅" if getattr(j, 'drs_allowed', 0) == 1 else "❌"
        
        # Barra visual de ERS
        bars = int(ers_percent / 10)
        bar_visual = "█" * bars + "░" * (10 - bars)
        
        linhas.append(f"{pos:<2} {nome} {bar_visual} {ers_percent:>4.0f}%  {ers_mode:<8} {drs}")
    
  linhas.append("```")
    
  await ctx.send("\n".join(linhas))