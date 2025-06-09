from gtts import gTTS
from utils.dictionnaries import tyres_dictionnary  
import asyncio
import discord
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Bot.jogadores import get_jogadores

def gerar_audio_gtts(texto, filename="saida.mp3", lang="pt"):
    tts = gTTS(text=texto, lang=lang)
    tts.save(filename)

async def comando_pneusv(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em uma call.")
        return

    canal = ctx.author.voice.channel
    vc = ctx.voice_client or await canal.connect()

    jogadores = get_jogadores()
    top5 = sorted([p for p in jogadores if not p.hasRetired], key=lambda x: x.position)[:5]

    mensagens = []
    for p in top5:
        tipo = tyres_dictionnary.get(p.tyres, "Desconhecido")
        mensagens.append(f"{p.name}: {p.tyresAgeLaps} voltas com pneu {tipo}")

    texto = "📻 Situação dos pneus dos 5 primeiros: " + ". ".join(mensagens)
    
    try:
        gerar_audio_gtts(texto)  # gera saida.mp3 com gTTS
        vc.play(discord.FFmpegPCMAudio("saida.mp3"))

        while vc.is_playing():
            await asyncio.sleep(1)

    except Exception as e:
        await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    finally:
        await vc.disconnect()