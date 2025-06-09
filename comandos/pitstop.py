from Bot.jogadores import get_jogadores
from utils.audios import gerar_audio
import discord
import asyncio
from gtts import gTTS
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores
estado_pneu_anterior={}
def gerar_audio_gtts(texto, filename="saida.mp3", lang="pt"):
    tts = gTTS(text=texto, lang=lang)
    tts.save(filename)

async def pitstop(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz.")
        return

    canal = ctx.author.voice.channel
    if ctx.voice_client and ctx.voice_client.channel != canal:
        await ctx.voice_client.disconnect()

    vc = ctx.voice_client or await canal.connect()

    jogadores = get_jogadores()
    pitaram = []

    for p in jogadores:
        if p.name not in estado_pneu_anterior:
            estado_pneu_anterior[p.name] = p.tyresAgeLaps
        else:
            if p.tyresAgeLaps < estado_pneu_anterior[p.name]:
                pitaram.append(p.name)
            estado_pneu_anterior[p.name] = p.tyresAgeLaps

    if pitaram:
        texto = "Fizeram pit stop recentemente: " + ", ".join(pitaram)
    else:
        texto = "Nenhum pit stop recente detectado."

    try:
        gerar_audio_gtts(texto)
        vc.play(discord.FFmpegPCMAudio("saida.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
    except Exception as e:
        await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    finally:
        await vc.disconnect()