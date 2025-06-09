from utils.audios import gerar_audio
from utils.dictionnaries import tyres_dictionnary, ERS_dictionary
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

async def comando_status(ctx, *, piloto: str = None):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em uma call.")
        return

    canal = ctx.author.voice.channel

    if ctx.voice_client and ctx.voice_client.channel != canal:
        await ctx.voice_client.disconnect()

    vc = ctx.voice_client or await canal.connect()

    jogadores = get_jogadores()
    selecionado = None

    # Buscar piloto por posição (ex: ".status 1")
    if piloto and piloto.isdigit():
        pos = int(piloto)
        selecionado = next((j for j in jogadores if j.position == pos), None)
    elif piloto:
        # Buscar por nome parcial (ex: ".status leclerc")
        selecionado = next((j for j in jogadores if piloto.lower() in j.name.lower()), None)

    if not selecionado:
        await ctx.send("❌ Piloto não encontrado. Use o número da posição ou parte do nome.")
        await vc.disconnect()
        return

    nome = selecionado.name
    pos = selecionado.position
    pneus = tyres_dictionnary.get(selecionado.tyres, "desconhecido")
    voltas_pneu = selecionado.tyresAgeLaps
    melhor_volta = selecionado.bestLapTime
    energia = ERS_dictionary.get(selecionado.ERS_mode, "desconhecido")
    percentual_ers = f"{selecionado.ERS_pourcentage:.0f}%"
    combustivel = round(selecionado.fuelRemainingLaps, 2)

    texto = (
        f"📻 Status de {nome}: posição {pos}, com pneu {pneus} há {voltas_pneu} voltas. "
        f"Melhor volta em {melhor_volta:.3f} segundos. "
        f"ERS em {percentual_ers}, modo {energia}. "
        f"Combustível restante para {combustivel} voltas."
    )

    try:
        gerar_audio_gtts(texto)
        vc.play(discord.FFmpegPCMAudio("saida.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
    except Exception as e:
        await ctx.send(f"❌ Erro ao reproduzir áudio: {e}")
    finally:
        await vc.disconnect()

  