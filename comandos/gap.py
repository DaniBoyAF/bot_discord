from Bot.jogadores import get_jogadores
from utils.audios import gerar_audio
import discord
import asyncio
from gtts import gTTS
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def gerar_audio_gtts(texto, filename="saida.mp3", lang="pt"):
    tts = gTTS(text=texto, lang=lang)
    tts.save(filename)
async def comando_gap(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz.")
        return

    canal = ctx.author.voice.channel

    if ctx.voice_client and ctx.voice_client.channel != canal:
        await ctx.voice_client.disconnect()

    vc = ctx.voice_client or await canal.connect()

    jogadores = get_jogadores()
    top3 = sorted([p for p in jogadores if not p.hasRetired], key=lambda x: x.position)[:3]

    if len(top3) < 2:
        await ctx.send("❌ Não há pilotos suficientes.")
        await vc.disconnect()
        return

    lider = top3[0]
    falas = []
    for p in top3[1:]:
        gap = (p.bestLapTime - lider.bestLapTime)
        falas.append(f"{p.name} está a {gap:.3f} segundos de {lider.name}")

    texto = "Diferença entre os 3 primeiros: " + ". ".join(falas)

    try:
        gerar_audio_gtts(texto)
        vc.play(discord.FFmpegPCMAudio("saida.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
    except Exception as e:
        await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    finally:
        await vc.disconnect()
