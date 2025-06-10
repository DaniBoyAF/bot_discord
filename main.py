import discord
from discord.ext import commands
import asyncio
import threading
from comandos.pneusv import comando_pneusv
from comandos.delta import comando_delta  # se o nome correto for esse
from comandos.gap import comando_gap
from comandos.pitstop import pitstop
from comandos.status import comando_status
from Bot.parser2024 import start_udp_listener
from comandos.clima import comando_clima
from comandos.pilotos import commando_piloto
from comandos.danos import danos
import os
import json
from gtts import gTTS
TEMPO_INICIO = False
# Corrige o caminho para importar módulos de fora da pasta
intents =discord.Intents.default()
intents.message_content=True
bot =commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print("Bot on")

@bot.event
async def on_member_join(membro:discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} entrou no servidor !!")

@bot.event
async def on_member_remove(membro: discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} Saiu do servidor !!")

@bot.command()
async def enviarpdf(ctx: commands.Context):
    caminho_2 = "relatorio_de_corrida_completo.pdf"
    if not os.path.exists(caminho_2):
        await ctx.send("❌ O arquivo PDF ainda não foi gerado.\nUse o comando `.gerarpdf` após a corrida.")
        return
    with open("relatorio_de_corrida_completo.pdf","rb") as pdf :
        await ctx.send("O pdf estar :",file=discord.File(pdf,"relatorio_de_corrida_completo.pdf"))
        
@bot.command()
async def telemetriapdf(ctx: commands.Context):
    caminho = "telemetria geral.pdf"
    if not os.path.exists(caminho):
        await ctx.send("❌ O arquivo PDF ainda não foi gerado.")
        return
    with open("telemetria geral.pdf","rb")as pdf :

        await ctx.send("O pdf estar :",file=discord.File(pdf,"telemetria geral.pdf"))
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
    ".ola\n"
    ".gap\n"
    ".pitstop\n"
    ".status\n"
    ".clima\n"
    ".gerar_audio\n"
    ".delta\n"
    ".telemetriapdf\n"
    ".enviarpdf\n"
    ".pneusv\n"
    ".danos\n"
    ".pilotos\n"
    ".gerarpdf\n"
    ".sobre\n"
    ".voltas\n"
    ".volta_chat\n"
    ".pararvoltas\n"
    ".velocidade\n"
    ".ranking\n")
@bot.command()
async def sobre(ctx:commands.Context):
 await ctx.reply("Sou um bot que pode falar com radio e criar pdf.")
@bot.command()
async def voltas(ctx,*,piloto: str):
    from Bot.jogadores import get_jogadores
    jogadores=get_jogadores
    piloto = piloto.lower()
    for j in jogadores:
        if piloto in j.name.lower():
            voltas = [f"Volta {i+1}: {tempo/1000:.3f}s" for i, tempo in enumerate(j.currentLapTime)]
            texto ="\n".join(voltas) or "não a dados sobre os registradas."
            await ctx.send(f"📊 Tempos de volta de {j.name}:\n```{texto}```")
            return
    await ctx.send("❌ Piloto não encontrado.")
@bot.command()
async def velocidade(ctx):
    from Bot.jogadores import get_jogadores
    jogadores =get_jogadores()
    M_rapido =max(jogadores,key=lambda j: j.speed_trap)
    await ctx.send(f"🚀 {M_rapido.name} foi o mais rápido no speed trap: {M_rapido.speed_trap} km/h")
@bot.command
async def ranking(ctx):
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()
    top10 = sorted(jogadores,key=lambda j: j.position )[:10]
    texto="\n".join([f"{j.position}º - {j.name}" for j in top10])
    await ctx.send(f"🏆 Top 10 da corrida:\n```{texto}```")
@bot.command()
async def grafico(ctx):
    from dados.telemetria_pdf import mostra_graficos_geral
    from Bot.jogadores import get_jogadores

    jogadores = get_jogadores()
    mostra_graficos_geral(jogadores, nome_arquivo="grafico_tempos.png")
    
    await ctx.send(file=discord.File("grafico_tempos.png"))
@bot.command()
async def tabela(ctx):
    global TEMPO_INICIO
    TEMPO_INICIO = True
    from Bot.jogadores import get_jogadores
    canal_id = 1381831375006601328
    canal = bot.get_channel(canal_id)
    if not canal:   
        await ctx.send("❌ Canal de voz não encontrado.")
        return
    mensagem = "🔄 Iniciando o envio de mensagens da tabela ao vivo..."
    while TEMPO_INICIO:
        jogador = get_jogadores()  # Atualiza a lista a cada ciclo
        jogador= sorted(jogador, key=lambda j: j.position)
        linhas = ["P  #  NAME           GAP    TYRES"]
        for j in jogador:
            delta_to_leader = getattr(j, "delta_to_leader", "—")  # Ajuste conforme seu atributo de gap
            linhas.append(f"{j.position:<2} {j.numero:<2} {j.name:<14} {j.delta_to_leader} {j.tyres}")
        tabela = "```\n" + "\n".join(linhas) + "\n```"
        await mensagem.edit(content=tabela)
        await canal.send(tabela,delete_after=10)
        await asyncio.sleep(3)  # Intervalo de atualização, ajuste conforme necessário
@bot.command()
async def volta_chat(ctx):
    global TEMPO_INICIO
    TEMPO_INICIO = True
    from Bot.jogadores import get_jogadores
    canal_id = 1373049532983804014
    canal = bot.get_channel(canal_id)
    if not canal:
        await ctx.send("❌ Canal de voz não encontrado.")
        return
    await ctx.send("🔄 Iniciando o envio de mensagens de volta...")

    while TEMPO_INICIO:
        jogadores = get_jogadores()  # Atualiza a lista a cada ciclo
        mensagens = []
        dados_salvar = []
        # Ordena os jogadores por posição
        for j in jogadores:
            if not j.name.strip():
                continue
            setores = j.bestLapSectors

            # Agora mostra todos os setores, inclusive zeros
            tempo_total = sum(setores)
            minutos = int(tempo_total // 60)
            segundos = int(tempo_total % 60)
            texto = (
                f"🏎️ {j.name} - S1: {setores[0]:.3f}s | S2: {setores[1]:.3f}s | S3: {setores[2]:.3f}s | "
                f"Tempo total: ⏱️ {minutos}m {segundos}s"
            )
            mensagens.append(texto)
            dados_salvar.append({
                "nome": j.name,
                "setores": setores,
                "tempo_total": tempo_total,

            })
        with open("dados_salvar.json", "w",encoding="utf-8") as f:
            json.dump(dados_salvar, f, ensure_ascii=False, indent=4)
        if mensagens:
            await canal.send("📊 **Setores por piloto:**\n" + "\n".join(mensagens))
        
        await asyncio.sleep(4)
@bot.command()
async def arquivo(ctx):
    caminho = "dados_salvar.json"
    if not os.path.exists(caminho):
        await ctx.send("❌ O arquivo JSON ainda não foi gerado.\nUse o comando `.volta_chat` para gerar.")
        return
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    await ctx.send("📁 Dados do arquivo JSON carregados com sucesso!",file=discord.File(caminho))
@bot.command()
async def pararvoltas(ctx):
    global TEMPO_INICIO
    TEMPO_INICIO = False
    await ctx.send("🛑 Envio automático de voltas/parado.")
@bot.command()
async def delta(ctx):
    await comando_delta(ctx)
@bot.command()
async def pneusv(ctx):
    await comando_pneusv(ctx)
@bot.command(name='gap')
async def gap(ctx):
    await comando_gap(ctx)
@bot.command()
async def pitstop(ctx):
    await pitstop(ctx)
@bot.command()
async def status(ctx,*, piloto: str = None):
     await comando_status(ctx, piloto=piloto)
@bot.command()
async def clima(ctx):
    await comando_clima(ctx)
@bot.command()
async def pilotos(ctx):
    await commando_piloto(ctx)
@bot.command()
async def danos(ctx, *, piloto: str = None):
    await danos(ctx, piloto = piloto)
import uuid

def gerar_audio_gtts(texto, idioma="pt", nome_arquivo=None):

    if nome_arquivo is None:
        nome_arquivo = f"saida_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=texto, lang=idioma)
    tts.save(nome_arquivo)
    return nome_arquivo
@bot.command()
async def gerar_audio(ctx):
    if ctx.author.voice:
        canal = ctx.author.voice.channel
        vc = ctx.voice_client or await canal.connect()

        texto = "Esse é um teste com a voz do Google."
        nome_audio = gerar_audio_gtts(texto)

        vc.play(discord.FFmpegPCMAudio(nome_audio))
        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
    else:
        await ctx.send("❌ Você precisa estar em um canal de voz.")
@bot.command()
async def gerarpdf(ctx):
    from dados.export_pdf import export_pdf_corrida_final
    from dados.telemetria_pdf import mostra_graficos_geral
    from Bot.jogadores import get_jogadores
    from Bot.Session import SESSION

    jogadores = get_jogadores()
    mostra_graficos_geral(jogadores)  # gera imagem do gráfico
    export_pdf_corrida_final("relatorio_de_corrida_completo.pdf", jogadores, SESSION)
    await ctx.send("✅ PDF gerado com sucesso!")

if __name__ == "__main__":
    import threading
    from Bot.parser2024 import start_udp_listener
    threading.Thread(target=start_udp_listener, daemon=True).start()    
bot.run("")
 #python Bot/bot_discord.py pra ativar

