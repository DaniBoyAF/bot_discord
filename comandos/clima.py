import sys
import os
import time
import asyncio
import discord
# Corrige o caminho para importar módulos de fora da pasta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Bot.Session import SESSION  # Supondo que SESSION está em Bot/Session.py
from utils.dictionnaries import session_dictionary, weather_dictionary
# Variável global para armazenar o tempo de início da sessão
TEMPO_INICIO = time.time()

async def comando_clima(ctx):
    session = SESSION  # Objeto com os dados da sessão

    tempo_rolando = int(time.time() - TEMPO_INICIO)
    minutos = tempo_rolando // 60
    segundos = tempo_rolando % 60

    # Acessa os dados da sessão do F1 corretamente
    tempo_ar = getattr(SESSION, "m_air_temperature", 0)
    tempo_pista = getattr(SESSION, "m_track_temperature", 0)
    clima = weather_dictionary.get(getattr(SESSION, "m_weather", 0), "desconhecido")
    tipo_sessao = session_dictionary.get(getattr(session, "m_session_type", 0), "desconhecida")
    volta_atual = getattr(session, "m_currentLap", 0)
    total_voltas = getattr(session, "m_total_laps", 0)

    texto = (
        f"Sessão: {tipo_sessao}. Já se passaram {minutos} minutos e {segundos} segundos. "
        f"Temperatura do ar: {tempo_ar} graus. Temperatura da pista: {tempo_pista} graus. "
        f"Clima atual: {clima}. Volta {volta_atual} de {total_voltas}."
    )

    await ctx.send(texto)  # Envia a mensagem no canal de texto