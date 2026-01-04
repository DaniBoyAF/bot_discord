import json
import asyncio
import logging
from websockets.server import serve
from utils.dictionnaries import weather_dictionary

LOG = logging.getLogger("web_server")
_clients = set()

# Variável global para armazenar dados dos pilotos
dados_live = {"pilotos": [], "sessao": {}}

async def ws_handler(websocket):
    _clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        _clients.discard(websocket)

async def broadcast(data):
    if _clients:
        msg = json.dumps(data)
        await asyncio.gather(*[c.send(msg) for c in _clients], return_exceptions=True)

async def start_websocket_server():
    async with serve(ws_handler, "0.0.0.0", 8765):
        LOG.info("WebSocket server rodando em ws://0.0.0.0:8765")
        await asyncio.Future()

async def _ws_daemon(host: str, port: int):
    async with serve(ws_handler, host, port):
        LOG.info("WebSocket rodando em ws://%s:%s", host, port)
        await asyncio.Future()

def run(host: str = "0.0.0.0", port: int = 6789):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_ws_daemon(host, port))
    finally:
        loop.close()

def atualizar_dados_live(jogadores, sessao_info=None):
    """Chamado pelo parser para atualizar dados e enviar via WebSocket.
    Suporta objetos com atributos ou dicts."""
    global dados_live

    def _get(x, key, default=None):
        try:
            return getattr(x, key)
        except Exception:
            try:
                return x.get(key, default)
            except Exception:
                return default

    pilotos = []
    for j in jogadores:
        try:
            raw_wear = _get(j, "tyre_wear", None) or []
            if isinstance(raw_wear, tuple):
                raw_wear = list(raw_wear)
            if len(raw_wear) >= 4:
                tyre_wear = [raw_wear[2], raw_wear[3], raw_wear[0], raw_wear[1]]
            else:
                tyre_wear = [0, 0, 0, 0]

            raw_inner = _get(j, "tyres_temp_inner", []) or []
            if isinstance(raw_inner, tuple):
                raw_inner = list(raw_inner)
            if len(raw_inner) >= 4:
                tyres_temp_inner = [raw_inner[2], raw_inner[3], raw_inner[0], raw_inner[1]]
            else:
                tyres_temp_inner = [0, 0, 0, 0]

            raw_surface = _get(j, "tyres_temp_surface", []) or []
            if isinstance(raw_surface, tuple):
                raw_surface = list(raw_surface)
            if len(raw_surface) >= 4:
                tyres_temp_surface = [raw_surface[2], raw_surface[3], raw_surface[0], raw_surface[1]]
            else:
                tyres_temp_surface = [0, 0, 0, 0]

            fuel_laps = _get(j, "fuelRemainingLaps", _get(j, "combustivel_restante", 0))
            pit_flag = bool(_get(j, "pit", None) or (_get(j, "pit_stops", 0) and int(_get(j, "pit_stops", 0)) > 0))

            pilotos.append({
                "nome": _get(j, "name", "Unknown"),
                "numero": _get(j, "numero", 0),
                "position": _get(j, "position", 99),
                "tyres": _get(j, "tyres", "Unknown"),
                "tyresAgeLaps": _get(j, "tyresAgeLaps", 0),
                "delta_to_leader": _get(j, "delta_to_leader", 0),
                "fuelRemainingLaps": fuel_laps,
                "pit": pit_flag,
                "tyre_wear": tyre_wear,
                "tyres_temp_inner": tyres_temp_inner,
                "tyres_temp_surface": tyres_temp_surface,
            })
        except Exception:
            continue

    dados_live = {
        "pilotos": pilotos,
        "sessao": sessao_info or {}
    }

    try:
        asyncio.create_task(broadcast(dados_live))
    except Exception:
        pass

def atualizar_sessao_info(pista, tipo_sessao, volta_atual, total_voltas, clima_info, flag="Verde", safety_car="Nenhum"):
    """
    Atualiza informações da sessão e envia via WebSocket.
    
    Parâmetros:
        pista: nome do circuito
        tipo_sessao: ex. "Corrida", "Classificação"
        volta_atual: volta atual da sessão
        total_voltas: total de voltas
        clima_info: dict com clima, temperatura_ar, temperatura_pista, previsao_chuva, umidade
        flag: bandeira atual (Verde, Amarela, Vermelha, etc.)
        safety_car: status do safety car
    """
    global dados_live
    
    # Extrai valores de clima_info com fallback
    clima_id = clima_info.get("m_weather", "Desconhecido") if isinstance(clima_info, dict) else "Desconhecido"
    clima = weather_dictionary.get(clima_id, "Desconhecido")
    temp_ar = clima_info.get("temperatura_ar", 0) if isinstance(clima_info, dict) else 0
    temp_pista = clima_info.get("temperatura_pista", 0) if isinstance(clima_info, dict) else 0
    previsao_chuva = clima_info.get("rainPercentage", 0) if isinstance(clima_info, dict) else 0
    umidade = clima_info.get("umidade", 0) if isinstance(clima_info, dict) else 0
    
    dados_live["sessao"] = {
        "pista": pista,
        "tipo_sessao": tipo_sessao,
        "volta_atual": volta_atual,
        "total_voltas": total_voltas,
        "clima": clima,
        "temperatura_ar": temp_ar,
        "temperatura_pista": temp_pista,
        "previsao_chuva": ,
        "umidade": umidade,
        "flag": flag,
        "safety_car": safety_car
    }
    
    try:
        asyncio.create_task(broadcast(dados_live))
    except Exception:
        pass

# Este módulo apenas define funções utilitárias para atualizar e enviar dados via WebSocket.