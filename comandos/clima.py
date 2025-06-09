import sys
import os
import time
import asyncio
import discord
from gtts import gTTS

# Corrige o caminho para importar módulos de fora da pasta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Bot.Session import SESSION  # Supondo que SESSION está em Bot/Session.py
from utils.dictionnaries import session_dictionary, weather_dictionary

TEMPO_INICIO = time.time()

def gerar_audio_gtts(texto, filename="saida.mp3", lang="pt"):
    tts = gTTS(text=texto, lang=lang)
    tts.save(filename)

async def comando_clima(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz.")
        return

    canal = ctx.author.voice.channel
    vc = ctx.voice_client or await canal.connect()

    session = SESSION  # Objeto com os dados da sessão

    tempo_rolando = int(time.time() - TEMPO_INICIO)
    minutos = tempo_rolando // 60
    segundos = tempo_rolando % 60

    # Acessa os dados da sessão do F1 corretamente
    tempo_ar = getattr(session, "airTemperature", 0)
    tempo_pista = getattr(session, "trackTemperature", 0)
    clima = weather_dictionary.get(getattr(session, "weather", 0), "desconhecido")
    tipo_sessao = session_dictionary.get(getattr(session, "Seance", 0), "desconhecida")
    volta_atual = getattr(session, "currentLap", 0)
    total_voltas = getattr(session, "nbLaps", 0)

    texto = (
        f"Sessão: {tipo_sessao}. Já se passaram {minutos} minutos e {segundos} segundos. "
        f"Temperatura do ar: {tempo_ar} graus. Temperatura da pista: {tempo_pista} graus. "
        f"Clima atual: {clima}. Volta {volta_atual} de {total_voltas}."
    )

    try:
        gerar_audio_gtts(texto)
        vc.play(discord.FFmpegPCMAudio("saida.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
    except Exception as e:
        await ctx.send(f"❌ Erro no áudio: {e}")
    finally:
        await vc.disconnect()