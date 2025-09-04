import sys
import os
import time
# Corrige o caminho para importar módulos de fora da pasta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Bot.Session import SESSION # Supondo que SESSION está em Bot/Session.py

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
    clima = {weather_dictionary[getattr(SESSION, "m_weather", 0)]}
    tipo_sessao = session_dictionary.get(getattr(SESSION, "m_session_type", 0), "desconhecida")
    total_voltas = getattr(session, "m_total_laps", 0)
    rain_porcentagem = getattr(session, "m_weather_forecast_samples", 0)
    carro_de_segurança = getattr(session, "m_safety_car_status", 0)
    if carro_de_segurança == 0:
        tipo_sessao += " (sem Safety Car)"
    elif carro_de_segurança == 1:
        tipo_sessao += " (Safety Car na pista)"
    elif carro_de_segurança == 2:
        tipo_sessao += " (Virtual Safety Car)"
    texto = (
        f"Sessão: {tipo_sessao}. Já se passaram {minutos} minutos e {segundos} segundos.\n "
        f"Temperatura do ar: {tempo_ar} graus.\n Temperatura da pista: {tempo_pista} graus. "
        f"Clima atual: {clima}E porcentagem {rain_porcentagem}%.\n Volta maximas {total_voltas}."
        f"A sessão tem {len(session.weatherList)}% previsões de clima futuras.\n"
        f"Carro de segurança: {carro_de_segurança}.\n"
    )

    await ctx.send(texto)  # Envia a mensagem no canal de texto