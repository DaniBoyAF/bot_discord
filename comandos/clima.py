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
    session = SESSION  # Objeto com os dados da sessão
    tempo_rolando = int(time.time() - TEMPO_INICIO)
    minutos = tempo_rolando // 60
    segundos = tempo_rolando % 60

    # Acessa os dados da sessão do F1 corretamente
    tempo_ar = getattr(SESSION, "m_air_temperature", 0)
    tempo_pista = getattr(SESSION, "m_track_temperature", 0)
    clima_id = getattr(SESSION, "m_weather", 0)
    clima = weather_dictionary.get(clima_id, "Desconhecido")  # ← CORRIGIDO (era {set})
    tipo_sessa = getattr(SESSION, "m_session_type", 0)
    total_voltas = getattr(session, "m_total_laps", 0)
    rain_porcentagem = getattr(session, "rainPercentage", 0)
    carro_de_segurança = getattr(session, "m_safety_car_status", 0)
    safety_car_status = safetyCarStatusDict.get(carro_de_segurança, "Nenhum")  # ← TRADUZ
    bandeira = getattr(session, "m_zone_flag", "Verde")  # ← ADICIONA BANDEIRA
    
    tipo_sessao = session_dictionary.get(tipo_sessa, "Sessão Desconhecida")
    
    # ← REMOVE O IF (já traduzido acima)
    
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