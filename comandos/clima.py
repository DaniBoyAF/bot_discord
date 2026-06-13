import sys
import os
import time

# Corrige o caminho para importar módulos de fora da pasta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Bot.Session import SESSION
from utils.dictionnaries import session_dictionary, weather_dictionary, safetyCarStatusDict

# Variável global para armazenar o tempo de início da sessão
TEMPO_INICIO = time.time()

async def comando_clima(ctx):
    # Padronizamos usando a variável em minúsculo para todo o bloco
    session = SESSION
    
    tempo_rolando = int(time.time() - TEMPO_INICIO)
    minutos = tempo_rolando // 60
    segundos = tempo_rolando % 60

    # Acessa os dados principais da sessão
    tempo_ar = getattr(session, "m_air_temperature", getattr(session, "m_airTemperature", 0))
    tempo_pista = getattr(session, "m_track_temperature", getattr(session, "m_trackTemperature", 0))
    
    clima_id = getattr(session, "m_weather", 0)
    clima = weather_dictionary.get(clima_id, "Desconhecido")
    
    tipo_sessa = getattr(session, "m_session_type", getattr(session, "m_sessionType", 0))
    tipo_sessao = session_dictionary.get(tipo_sessa, "Sessão Desconhecida")
    
    total_voltas = getattr(session, "m_total_laps", getattr(session, "m_totalLaps", 0))
    
    carro_de_segurança = getattr(session, "m_safety_car_status", getattr(session, "m_safetyCarStatus", 0))
    safety_car_status = safetyCarStatusDict.get(carro_de_segurança, "Nenhum")

    # --- CORREÇÃO: PORCENTAGEM DE CHUVA ---
    rain_porcentagem = 0
    amostras_clima = getattr(session, "m_weatherForecastSamples", getattr(session, "m_weather_forecast_samples", []))
    if len(amostras_clima) > 0:
        amostra_atual = amostras_clima[0] # Pega a previsão imediata (índice 0)
        rain_porcentagem = getattr(amostra_atual, "m_rainPercentage", getattr(amostra_atual, "m_rain_percentage", 0))

    # --- CORREÇÃO: BANDEIRA (MARSHAL ZONES) ---
    bandeira = "Verde"
    zonas = getattr(session, "m_marshalZones", getattr(session, "m_marshal_zones", []))
    if len(zonas) > 0:
        zona_atual = zonas[0] # Simplificação: olhando a primeira zona (você pode iterar pelo setor do piloto futuramente)
        flag_id = getattr(zona_atual, "m_zoneFlag", getattr(zona_atual, "m_zone_flag", -1))
        if flag_id == 1: bandeira = "Verde"
        elif flag_id == 2: bandeira = "Azul"
        elif flag_id == 3: bandeira = "Amarela"
        elif flag_id == 4: bandeira = "Vermelha"
        else: bandeira = "Desconhecida"
    
    texto = (
        f"🏁 **Sessão**: {tipo_sessao}\n"
        f"⏱️ **Tempo decorrido**: {minutos}min {segundos}s\n"
        f"🌡️ **Temperatura do ar**: {tempo_ar}°C\n"
        f"🌡️ **Temperatura da pista**: {tempo_pista}°C\n"
        f"☁️ **Clima atual**: {clima}\n"
        f"🌧️ **Porcentagem de chuva**: {rain_porcentagem}%\n"
        f"🏎️ **Voltas totais**: {total_voltas}\n"
        f"🚗 **Safety Car**: {safety_car_status}\n"
        f"🏴 **Bandeira**: {bandeira}"
    )

    await ctx.send(texto)