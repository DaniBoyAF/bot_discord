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
from gtts import gTTS
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
    ".gerarpdf\n")
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

