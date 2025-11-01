import discord
from discord.ext import commands
import asyncio
import threading
import time


import threading
from comandos.pneusv import comando_pneusv
from comandos.delta import comando_delta  # se o nome correto for esse
from comandos.status import comando_status
from Bot.parser2024 import start_udp_listener
from comandos.clima import comando_clima
from comandos.pilotos import commando_piloto
from comandos.danos import danos as comandos_danos
from comandos.media import comando_media 
from dados.voltas import gerar_boxplot

from Javes.modelo_ml import analisar_dados_auto
import json                   
from threading import Thread
import subprocess
import os
import signal
import sys
import shutil
import re
from painel.app import app

TEMPO_INICIO = False
TEMPO_INICIO_TABELA = False
TEMPO_INICIO_VOLTAS = False
TEMPO_INICIO_TABELA_Q = False
public_url = None
_cloudflared_proc = None
inicio= time.time()
tempo_maximo = 600 * 60 
# Corrige o caminho para importar módulos de fora da pasta
intents =discord.Intents.default()
intents.message_content=True
bot =commands.Bot(command_prefix=".", intents=intents)
@bot.event
async def on_ready():
    global TEMPO_INICIO_VOLTAS
    TEMPO_INICIO_VOLTAS = True
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
async def Jarves_on(ctx):
    resultado = analisar_dados_auto()
    canal_id = 1413993963072782436
    canal = bot.get_channel(canal_id)
    if not canal:
        await ctx.send("❌ Canal de texto não encontrado.")
        return
    await ctx.send("⚠️ Deseja continuar? Responda com `sim` ou `não`.")
    def check(m):# isso ver a mensagem sim ou não
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["sim", "não"]

    resposta = await bot.wait_for("message", check=check)
    if resposta.content.lower() == "sim":
        await ctx.send("✅ Continuando...")
        await ctx.send(resultado)
    else:
        await ctx.send("❌ Análise cancelada.")

@bot.command()
async def comando(ctx: commands.Context):
    await ctx.reply("Os comandos são:\n"
    ".ola            - O bot cumprimenta você\n"
    ".status         - Mostra o status de um piloto (ex: em pista, no pit, etc)\n"
    ".clima          - Mostra informações do clima atual\n"
    ".delta          - Mostra o delta de tempo dos pilotos\n"
    ".pneusv         - Mostra informações dos pneus dos pilotos\n"
    ".danos          - Mostra os danos do carro de um piloto\n"
    ".Jarves_on      - Analisar Dados com IA!!  \n"
    ".pilotos        - Lista os pilotos da sessão\n"
    ".sobre          - Mostra informações sobre o bot\n"
    ".voltas         - Mostra os tempos de volta de um piloto\n"
    ".salvar_dados     - Envia mensagens automáticas com setores e pneus dos pilotos\n"
    ".parar_salvar   - Para o envio automático de dados\n"
    ".velocidade     - Mostra o piloto mais rápido no speed trap\n"
    ".ranking        - Mostra o top 10 da corrida\n"
    ".grafico        - Envia o gráfico dos tempos de volta\n"
    ".grafico_midspeed - Envia o gráfico da velocidade média\n"
    ".media_setor    - Mostra a média de tempo de setor dos pilotos\n"
    ".grafico_maxspeed - Envia o gráfico da velocidade máxima\n"
    ".media_lap     - Mostra a média de tempo de volta dos pilotos\n"
    ".tabela         - Envia a tabela ao vivo dos pilotos\n"
    ".parartabela    - Para o envio automático da tabela\n"
    ".painel         - Faz um html sem deley grande\n "     
    ".pneusp         - Faz um html do pneus sem deley grande\n   "   
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
async def setor(ctx):
    import json
    from dados.setor import melhor_setor_gap
    
    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d

    # Lê o JSON salvo
    with open("dados_de_voltas.json", "r", encoding="utf-8") as f:
        dados_telemetria = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_telemetria]

    # Gera o gráfico
    melhor_setor_gap(pilotos, nome_arquivo="grafico_melhor_setor.png")
    await ctx.send(file=discord.File("grafico_melhor_setor.png"))
@bot.command()
async def grafico_midspeed(ctx):
    import json
    from dados.speed_mid import mostra_graficos_velocidade
    
    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d

    # Lê o JSON salvo
    with open("dados_telemetria.json", "r", encoding="utf-8") as f:
        dados_telemetria = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_telemetria]

    # Gera o gráfico
    mostra_graficos_velocidade(pilotos, nome_arquivo="grafico_velocidade.png")
    await ctx.send(file=discord.File("grafico_velocidade.png"))
@bot.command()
async def grafico_maxspeed(ctx):
    import json
    from dados.max_speed import graficos_speed_max

    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d

    # Lê o JSON salvo
    with open("dados_telemetria.json", "r", encoding="utf-8") as f:
       dados_telemetria = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_telemetria]

    # Gera o gráfico
    graficos_speed_max(pilotos, nome_arquivo="graficos_speed_max.png")
    await ctx.send(file=discord.File("graficos_speed_max.png"))

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
    with open("dados_de_voltas.json", "r", encoding="utf-8") as f:
        dados_de_voltas = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_de_voltas]

    # Gera o gráfico
    mostra_graficos_geral(pilotos,total_voltas=total_voltas, nome_arquivo="grafico_tempos.png")
    await ctx.send(file=discord.File("grafico_tempos.png"))
@bot.command()
async def corrida(ctx):
    import json
    from Bot.Session import SESSION
    total_voltas = getattr(SESSION, "m_total_laps", None)
    nome_pista = getattr(SESSION, "m_track_name", "Desconhecido")
    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d

    # Lê o JSON salvo
    with open("dados_de_voltas.json", "r", encoding="utf-8") as f:
        dados_de_voltas = json.load(f)

    # Cria lista de objetos temporários
    pilotos = [PilotoTemp(d) for d in dados_de_voltas]

    # Gera o gráfico
    gerar_boxplot(pilotos, nome_pista=nome_pista, total_voltas=total_voltas, nome_arquivo="corrida.png")
    await ctx.send(file=discord.File("corrida.png"))
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
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary, weather_dictionary, color_flag_dict,safetyCarStatusDict,session_dictionary
    from Bot.Session import SESSION
    
    
    canal_id = 1382050740922482892
    canal = bot.get_channel(canal_id)
    if not canal:
        print("❌ Canal não encontrado.")
        return
    mensagem = await canal.send("🔄 Iniciando o envio de mensagens de volta. Se aparecer algum erro de envio de mensagem no discord é normal .")
   
    while TEMPO_INICIO_VOLTAS:
        if time.time() - inicio >= tempo_maximo:
          print("⏱️ Tempo limite atingido, parando salvamento.")
          break
        jogadores = get_jogadores()
        tyres_nomes = tyres_dictionnary
        clima = weather_dictionary[getattr(SESSION, "m_weather", 0)]
        tempo_ar = getattr(SESSION, "m_air_temperature", 0)
        tempo_pista = getattr(SESSION, "m_track_temperature", 0)
        total_voltas = getattr(SESSION, "m_total_laps", 0)
        sessao = session_dictionary.get(getattr(SESSION,"m_session_type",0))

        dados_de_voltas = []
        dados_dos_pneus = []
        dados_dano = []
        dados_pra_o_painel = []
        dados_da_SESSION = []
        dados_telemetria = []
       
        for j in jogadores:
            if not j.name.strip():
                continue
            # Pega tudo
            
            todas_voltas = getattr(j, "todas_voltas_setores", [])
            Gas = getattr(j, "fuelRemainingLaps", 0)
            delta = getattr(j, "delta_to_leader", "—")
            num = getattr(j, 'numero', '--')
            rain_porcentagem = getattr(SESSION, "m_rain_percentage", 0)
            flag= color_flag_dict.get(getattr(SESSION, "m_flag", 0), "Desconhecida")
            SafetyCarStatus = safetyCarStatusDict.get(getattr(SESSION, "m_safety_car_status", 0),"Desconhecida")
            maior_speed_geral=max(j.speed_trap for j in jogadores)
            maior_speed = max(j.speed_trap) if isinstance(j.speed_trap, list) else j.speed_trap


            # Salva os dados em um dicionário
            dados_dano.append({
                "delta_to_leader": delta,
                "nome": j.name,
                "numero": num,
                 "Fuel": Gas,
                 "FL":j.FrontLeftWingDamage,
                 "FR":j.FrontRightWingDamage,
                 "Asa Traseira":j.rearWingDamage,
                 "Assoalho":j.floorDamage,
                 "Difusor":j.diffuserDamage,
                 "Sidepods":j.sidepodDamage
            })
            dados_dos_pneus.append({
                "nome": j.name,
                "numero": num,
                "position": j.position,
                "tyres": tyres_nomes.get(j.tyres, 'Desconhecido'),
                "tyresAgeLaps": j.tyresAgeLaps,
                "tyre_wear":j.tyre_wear[0:4],
                "tyre_temp_i": j.tyres_temp_inner [0:4],
                "tyre_temp_s": j.tyres_temp_surface[0:4],
                "tyre_life":j.tyre_life,
                "tyre_set_data":j.tyre_set_data,
                "lap_delta_time ":j.m_lap_delta_time,
            })
            # Salva no arquivo JSON
            dados_de_voltas.append({
                "nome": j.name,
                "numero": num ,
                "voltas": todas_voltas,
                "laps_max": total_voltas,
                "position": j.position,
                "tyres": tyres_nomes.get(j.tyres, 'Desconhecido'),
                "tyresAgeLaps": j.tyresAgeLaps
                
            })
            dados_pra_o_painel.append({
                "nome": j.name,
                "numero": num ,
                "position": j.position,
                "tyres": tyres_nomes.get(j.tyres, 'Desconhecido'),
                "tyresAgeLaps": j.tyresAgeLaps,
                "delta_to_leader": delta,
                "num_laps": total_voltas
                

            })
            dados_da_SESSION.append({
                "clima": clima,
                "tempo_ar":tempo_ar,
                "tempo_pista":tempo_pista,
                "rain_porcentagem": rain_porcentagem,
                "safety_car_status": SafetyCarStatus,
                "Sessao": sessao,
                "flag": flag,
                "maior_speed_geral":maior_speed_geral



            })
            dados_telemetria.append({
                "nome": j.name,
                "numero": num ,
                "position": j.position,
                "speed": maior_speed

            })
        with open("dados_telemetria.json","w",encoding="utf-8") as f:
            json.dump(dados_telemetria, f, indent=2, ensure_ascii=False)

        with open("dados_dano.json","w",encoding="utf-8") as f:
            json.dump(dados_dano, f, indent=2, ensure_ascii=False)
          
        with open("dados_dos_pneus.json","w",encoding="utf-8") as f:
            json.dump(dados_dos_pneus, f, indent=2, ensure_ascii=False)

        with open("dados_de_voltas.json", "w", encoding="utf-8") as f:
            json.dump(dados_de_voltas, f, indent=2, ensure_ascii=False)

        with open("dados_pra_o_painel.json", "w", encoding="utf-8") as f:
             json.dump(dados_pra_o_painel, f, indent=2, ensure_ascii=False)
             
        with open("dados_da_SESSION.json","w",encoding="utf-8") as f:
            json.dump(dados_da_SESSION, f, indent=2, ensure_ascii=False)

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
async def pneusv(ctx,*, piloto: str = None):
    await comando_pneusv(ctx, piloto=piloto)
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

@bot.command()
async def media_lap(ctx):
  await comando_media(ctx)

_cloudflared_proc = None
url = None

def _start_cloudflared(port=5000, cloudflared_path="cloudflared"):
    """Inicia cloudflared e retorna o objeto subprocess e o public_url lido da saída."""
    global _cloudflared_proc

    # Verifica se o executável está acessível
    if not shutil.which(cloudflared_path):
        raise FileNotFoundError(f"cloudflared não encontrado em: {cloudflared_path}")

    cmd = [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"]
    _cloudflared_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    public = None
    logs = []
    start = time.time()
    url_regex = r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com"

    while True:
        if _cloudflared_proc.stdout is None:
            break
        line = _cloudflared_proc.stdout.readline()
        if line:
            logs.append(line)
            print("[cloudflared]", line.strip())
            match = re.search(url_regex, line)
            if match:
                public = match.group(0)
                break

        if public or (time.time() - start) > 10:
            break

    if not public:
        print("⚠️ Não detectei o URL público automaticamente. Verifique manualmente o output do cloudflared acima.")
        print("🔍 Logs completos:")
        print("".join(logs))

    return _cloudflared_proc, public

def _stop_cloudflared():
    global _cloudflared_proc
    try:
        if _cloudflared_proc:
            print("Encerrando cloudflared...")
            _cloudflared_proc.terminate()
            try:
                _cloudflared_proc.wait(timeout=3)
            except Exception:
                _cloudflared_proc.kill()
    except Exception as e:
        print("Erro ao encerrar cloudflared:", e)
    finally:
        _cloudflared_proc = None

def iniciar_painel_e_cloudflared():
    from painel.app import app
    global url

    cloudflared_path = "cloudflared"  # ou caminho absoluto

    try:
        proc, url = _start_cloudflared(port=5000, cloudflared_path=cloudflared_path)
        if url:
            print(f"✅ Tunnel criado: {url}")
        else:
            print("⚠️ Não foi possível detectar URL do cloudflared automaticamente.")
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
    except Exception as e:
        print("❌ Erro ao iniciar painel/cloudflared:", e)
    finally:
        _stop_cloudflared()

# Comandos do bot
@bot.command()
async def painel(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel disponível em: {url}")

@bot.command()
async def pneusp(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel dos pneus disponível em: {url}/pnues")


if __name__ == "__main__":
    import threading
    from Bot.parser2024 import start_udp_listener
    threading.Thread(target=start_udp_listener, daemon=True).start()
    threading.Thread(target=iniciar_painel_e_cloudflared, daemon=True).start()    

 #python Bot/bot_discord.py pra ativar

