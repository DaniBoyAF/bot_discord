import discord
from discord.ext import commands
import asyncio
import threading
from comandos.pneusv import comando_pneusv
from comandos.delta import comando_delta  # se o nome correto for esse
from comandos.pitstop import pitstop
from comandos.status import comando_status
from Bot.parser2024 import start_udp_listener
from comandos.clima import comando_clima
from comandos.pilotos import commando_piloto
from comandos.danos import danos as comandos_danos
from comandos.media import comando_media
import os
import json
TEMPO_INICIO = False
TEMPO_INICIO_TABELA = False
TEMPO_INICIO_VOLTAS = False
TEMPO_INICIO_TABELA_Q = False
# Corrige o caminho para importar módulos de fora da pasta
intents =discord.Intents.default()
intents.message_content=True
bot =commands.Bot(command_prefix=".", intents=intents)
@bot.event
async def on_ready():
    print("Bot on")
    bot.loop.create_task(volta_salvar(bot))
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `.comando` para ver a lista de comandos.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumento obrigatório ausente. Verifique o comando e tente novamente.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Este comando está em cooldown. Tente novamente em {error.retry_after:.2f} segundos.")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")
@bot.event
async def on_member_join(membro:discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} entrou no servidor !!")

@bot.event
async def on_member_remove(membro: discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} Saiu do servidor !!")
@bot.command()
async def ola(ctx: commands.Context):
    nome= ctx.author.name
    await ctx.reply(f"Olá, {nome}! tudo bem?")
@bot.command()
async def bem(ctx: commands.Context):
    nome=ctx.author.name
    await ctx.reply(f"Que bom {nome}! Digite '.comando' pra mais informações")
@bot.command()
async def comando(ctx: commands.Context):
    await ctx.reply("Os comandos são:\n"
    ".ola            - O bot cumprimenta você\n"
    ".pitstop        - Mostra informações de pitstop dos pilotos\n"
    ".status         - Mostra o status de um piloto (ex: em pista, no pit, etc)\n"
    ".clima          - Mostra informações do clima atual\n"
    ".delta          - Mostra o delta de tempo dos pilotos\n"
    ".pneusv         - Mostra informações dos pneus dos pilotos\n"
    ".danos          - Mostra os danos do carro de um piloto\n"
    ".pilotos        - Lista os pilotos da sessão\n"
    ".Tabela_Qualy   - Mostra os tempos\n"
    ".sobre          - Mostra informações sobre o bot\n"
    ".voltas         - Mostra os tempos de volta de um piloto\n"
    ".salvar_dados     - Envia mensagens automáticas com setores e pneus dos pilotos\n"
    ".parar_salvar   - Para o envio automático de dados\n"
    ".velocidade     - Mostra o piloto mais rápido no speed trap\n"
    ".ranking        - Mostra o top 10 da corrida\n"
    ".grafico        - Envia o gráfico dos tempos de volta\n"
    ".tabela         - Envia a tabela ao vivo dos pilotos\n"
    ".parartabela    - Para o envio automático da tabela\n"
    "Use o comando '.comando' para ver a lista de comandos disponíveis.")
@bot.command()
async def sobre(ctx:commands.Context):
 await ctx.reply("Sou um bot que pode falar com radio e criar pdf.")
@bot.command()
async def voltas(ctx,*,piloto: str):
    from Bot.jogadores import get_jogadores
    jogadores= get_jogadores()
    piloto = piloto.lower()
    for j in jogadores:
        if piloto in j.name.lower():
            todas_voltas = getattr(j,"todas_voltas_setores",[])
            voltas = [f"Volta {v['volta']}: {v['tempo_total']:.3f}s" for v in todas_voltas]
            texto ="\n".join(voltas) or "não a dados sobre os registradas."
            await ctx.send(f"📊 Tempos de volta de {j.name}:\n```{texto}```")
            return
    await ctx.send("❌ Piloto não encontrado.")
@bot.command()#pronto
async def velocidade(ctx):#pronto
    """Comando para mostrar o piloto mais rápido no speed trap."""
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()

    m_rapido = max(jogadores, key=lambda j: j.speed_trap)
    await ctx.send(f"🚀 {m_rapido.name} foi o mais rápido no speed trap: {m_rapido.speed_trap:.2f} km/h")
@bot.command()
async def ranking(ctx):# pronto
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()
    top10 = sorted(jogadores,key=lambda j: j.position )[:10]
    texto="\n".join([f"{j.position}º - {j.name} - {j.speed_trap} km/h" for j in top10])
    await ctx.send(f"🏆 Top 10 da corrida:\n```{texto}```")
@bot.command()
async def grafico(ctx):# pronto
    import json
    from dados.telemetria_pdf import mostra_graficos_geral
    from Bot.Session import SESSION
    total_voltas = getattr(SESSION, "m_total_laps", None)
    
    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d

    # Lê o JSON salvo
    with open("dados_salvar.json", "r", encoding="utf-8") as f:
        dados_salvos = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_salvos]

    # Gera o gráfico
    mostra_graficos_geral(pilotos,total_voltas=total_voltas, nome_arquivo="grafico_tempos.png")
    await ctx.send(file=discord.File("grafico_tempos.png"))
@bot.command()
async def tabela(ctx):  # pronto
    global TEMPO_INICIO_TABELA
    TEMPO_INICIO_TABELA = True
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary
    canal_id = 1381831375006601328
    canal = bot.get_channel(canal_id)
    if not canal:
        await ctx.send("❌ Canal de voz não encontrado.")
        return

    mensagem = await canal.send("🔄 Iniciando o envio de mensagens da tabela ao vivo...")
    while TEMPO_INICIO_TABELA:
        jogador = get_jogadores()
        tyres_nomes = tyres_dictionnary
        jogador = sorted(jogador, key=lambda j: j.position)

        linhas = ["P  #  NAME           GAP      TYRES       TYRES_AGE PIT   "]
        for j in jogador:
            delta_to_leader = getattr(j, "delta_to_leader", "—")
            current_lap = getattr(j, "current_lap", 0)
            if isinstance(current_lap, (int, float)) and current_lap > 0:
                delta_to_leader = f"+{int(current_lap)}L"

            nome = str(getattr(j, "name", "SemNome"))[:14]
            linhas.append(
                f"{j.position:<2} {getattr(j, 'numero', '--'):<2} {nome:<14} "
                f"{str(delta_to_leader):<8} "
            f"{tyres_nomes.get(j.tyres, 'Desconhecido'):<12}{j.tyresAgeLaps}         {'Sim' if j.pit else 'Não':<3}"
            )

        tabela = "```\n" + "\n".join(linhas) + "\n```"
        try:
            await mensagem.edit(content=tabela)
        except Exception as e:
            print(f"Erro ao atualizar tabela: {e}")
            break

        await asyncio.sleep(0.5) # Intervalo de atualização, ajuste conforme necessário
@bot.command()# pronto
async def parar_tabela(ctx):
    global TEMPO_INICIO_TABELA
    TEMPO_INICIO_TABELA = False
    await ctx.send("🛑 Envio automático da tabela parado.")
@bot.command()
async def salvar_dados(ctx):
    await ctx.send("🔄 Salvando dados dos pilotos...")
    bot.loop.create_task(volta_salvar(bot))

async def volta_salvar(bot):# pronto
    global TEMPO_INICIO_VOLTAS
    TEMPO_INICIO_VOLTAS = True
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary
    from Bot.Session import SESSION
    
    canal_id = 1382050740922482892
    canal = bot.get_channel(canal_id)
    if not canal:
        print("❌ Canal não encontrado.")
        return
    mensagem = await canal.send("🔄 Iniciando o envio de mensagens de volta. Se aparecer algum erro de envio de mensagem no discord é normal .")

    while TEMPO_INICIO_VOLTAS:
        jogadores = get_jogadores()
        tyres_nomes = tyres_dictionnary
        currentLap = getattr(SESSION, "m_current_lap", 0)
        mensagens = []
        dados_salvar = []
        for j in jogadores:
            if not j.name.strip():
                continue
            # Pega o histórico de todas as voltas/setores
            
            todas_voltas = getattr(j, "todas_voltas_setores", [])
            Gas = getattr(j, "fuelRemainingLaps", 0)

            # Salva no arquivo JSON
            dados_salvar.append({
                "nome": j.name,
                "voltas": todas_voltas,
                "laps_max": currentLap,
                "position": j.position,
                "tyres": tyres_nomes.get(j.tyres, 'Desconhecido'),
                "tyresAgeLaps": j.tyresAgeLaps,
                "tyre_wear": j.tyre_wear[0:4],  # Pega os 4 pneus
                "speed": j.speed_trap,
                "avisos": j.warnings,
                "Fuel": Gas,
            })
            # Monta mensagem para cada volta (opcional: só mostra a última volta se quiser)
            if todas_voltas:
                ultima_volta = todas_voltas[-1]
                setores_str = " | ".join(f"{s:.3f}s" for s in ultima_volta["setores"])
                texto = (
                    f"🏎️{j.position}|{j.name}|Volta {ultima_volta['volta']}| "
                    f"Setores: {setores_str} | Total: {ultima_volta['tempo_total']:.3f}s | "
                    f"Tyres: {tyres_nomes.get(j.tyres, 'Desconhecido')}| "
                    f"Tyres Age: {j.tyresAgeLaps}| Pit: {j.pit}|"
                )
                mensagens.append(texto)
        with open("dados_salvar.json", "w", encoding="utf-8") as f:
            json.dump(dados_salvar, f, ensure_ascii=False, indent=4)
        if mensagens:
            await mensagem.edit(content="📊 ** Telemetria Geral:**\n" + "\n".join(mensagens))
        await asyncio.sleep(0.5)  # Intervalo de atualização, ajuste conforme necessário
@bot.command()
async def parar_salvar(ctx):#pronto
    global TEMPO_INICIO_VOLTAS
    TEMPO_INICIO_VOLTAS = False
    await ctx.send("🛑 Envio automático de voltas parado.")
@bot.command()
async def delta(ctx):
    await comando_delta(ctx)
@bot.command()
async def pneusv(ctx):
    await comando_pneusv(ctx)
@bot.command()
async def pitstop(ctx):
    await pitstop(ctx)
@bot.command()
async def status(ctx,*, piloto: str = None):
     await comando_status(ctx, piloto=piloto)
@bot.command()
async def clima(ctx):#pronto
    await comando_clima(ctx)
@bot.command()
async def pilotos(ctx):
    await commando_piloto(ctx)
@bot.command()
async def danos(ctx, piloto: str = None):
    await comandos_danos(ctx, piloto=piloto)
def formatacao(ms):
    if ms == "—" or ms is None:
        return "—"
    minutos = ms // 60000
    segundos = (ms % 60000) // 1000
    milissegundos = ms % 1000
    return f"{minutos}:{segundos:02}.{milissegundos:03}"
@bot.command()
async def Tabela_Qualy(ctx):
  global TEMPO_INICIO_TABELA_Q
  TEMPO_INICIO_TABELA_Q = True
  from Bot.jogadores import get_jogadores
  from utils.dictionnaries import tyres_dictionnary 
  canal_id = 1373049532983804014
  canal = bot.get_channel(canal_id)
  if not canal:
    await ctx.send("❌ Canal de voz não encontrado.")
    return
  mensagem = await canal.send("🔄 Iniciando o envio de mensagens da tabela ao vivo...")  
  while TEMPO_INICIO_TABELA_Q:
    jogador = get_jogadores()
    tyres_nomes = tyres_dictionnary
    jogador = sorted(jogador, key=lambda j: j.position)
    linhas = ["P  #  NAME           BEST_LAP  LAST_LAP   TYRES     TYRES_AGE     "]
    for j in jogador:
        raw_best_time = j.bestLapTime
        raw_Last_time = j.lastLapTime
        formatando2 = formatacao(raw_Last_time)
        formatado = formatacao(raw_best_time)
        nome = str(getattr(j, "name", "SemNome"))[:14]
        linhas.append(
        f"{j.position:<2} {getattr(j, 'numero', '--'):<2} {nome:<14} "
        f"{int(formatado):<8}  {int(formatando2):<8}"
        f"   {tyres_nomes.get(j.tyres, 'Desconhecido'):<12} {j.tyresAgeLaps}         "
         )
    tabela = "```\n" + "\n".join(linhas) + "\n```"
    try:
            await mensagem.edit(content=tabela)
    except Exception as e:
            print(f"Erro ao atualizar tabela: {e}")
            break

    await asyncio.sleep(0.5)
@bot.command()
async def parar_tabela_Qualy(ctx):
    global TEMPO_INICIO_TABELA_Q
    TEMPO_INICIO_TABELA_Q = False
    await ctx.send("🛑 Envio automático da tabela parado.")
@bot.command()
async def media_lap(ctx):
  await comando_media(ctx)
if __name__ == "__main__":
    import threading
    from Bot.parser2024 import start_udp_listener
    threading.Thread(target=start_udp_listener, daemon=True).start()    
bot.run("") # Substitua pelo seu token do bot
 #python Bot/bot_discord.py pra ativar

