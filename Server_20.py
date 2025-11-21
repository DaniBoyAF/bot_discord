import asyncio
import json
import logging
import websockets

LOG = logging.getLogger("web_server")
_clients = set()
_queue = None
_loop = None
_last_snapshot = None  # guarda último snapshot enviado

async def _handler(websocket, path):
    LOG.info("WS client connected")
    _clients.add(websocket)
    try:
        # envia último snapshot ao conectar (se disponível)
        if _last_snapshot is not None:
            try:
                await websocket.send(json.dumps(_last_snapshot, ensure_ascii=False))
            except Exception:
                pass
        await websocket.wait_closed()
    finally:
        _clients.discard(websocket)
        LOG.info("WS client disconnected")

async def _broadcaster():
    global _queue, _last_snapshot
    while True:
        snapshot = await _queue.get()
        if snapshot is None:
            continue
        _last_snapshot = snapshot
        data = json.dumps(snapshot, ensure_ascii=False)
        coros = [_safe_send(ws, data) for ws in list(_clients)]
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

async def _safe_send(ws, data):
    try:
        await ws.send(data)
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass

def notify_snapshot(snapshot: dict):
    """Chamado de outra thread (parser) para notificar novo snapshot."""
    if _loop and _queue:
        try:
            _loop.call_soon_threadsafe(_queue.put_nowait, snapshot)
        except Exception:
            LOG.exception("Falha ao notificar snapshot")

def run(host="0.0.0.0", port=6789):
    """Inicia o servidor WS (bloqueante). Rode em thread."""
    global _queue, _loop
    logging.basicConfig(level=logging.INFO)
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _queue = asyncio.Queue()
    start_server = websockets.serve(_handler, host, port)
    _loop.run_until_complete(start_server)
    _loop.create_task(_broadcaster())
    LOG.info(f"WebSocket server running on ws://{host}:{port}")
    try:
        _loop.run_forever()
    finally:
        LOG.info("WebSocket server stopping")
        _loop.close()