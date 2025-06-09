from discord.ext import commands
from Bot.jogadores import get_jogadores
from utils.audios import gerar_audio
import asyncio
import discord
from gtts import gTTS
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores
def gerar_audio_gtts(texto, filename="saida.mp3", lang="pt"):
    tts = gTTS(text=texto, lang=lang)
    tts.save(filename)

async def comando_delta(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em uma call.")
        return
    canal = ctx.author.voice.channel
    vc = ctx.voice_client or await canal.connect()

    jogadores = get_jogadores()
    validos = [p for p in jogadores if not p.hasRetired and p.bestLapTime > 0]

    if not validos:
        texto = "Nenhum piloto com volta válida ainda."
    else:
        melhor = min(validos, key=lambda p: p.bestLapTime)
        tempo = melhor.bestLapTime / 1000
        minutos = int(tempo // 60)
        segundos = tempo % 60
        texto = (f"{melhor.name} é o mais rápido da pista com {minutos} minuto e {segundos:.3f} segundos.")
    
    try:
     gerar_audio_gtts(texto)
     vc.play(discord.FFmpegPCMAudio("saida.mp3"))
     while vc.is_playing():
        await asyncio.sleep(1)
     await vc.disconnect()
    except Exception as e:
       await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    finally:
       await vc.disconnect()