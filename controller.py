# controller.py
# ─────────────────────────────────────────────────────────────────────────────
# Mini-servidor Flask que liga/desliga o bot (main.py / bot_discord.py)
# pelo navegador, sem precisar abrir terminal.
#
# Roda na porta 5001. Serve o bot-control.html na rota "/".
# ─────────────────────────────────────────────────────────────────────────────

from flask import Flask, jsonify, send_file, request
import subprocess
import os
import sys
import time
from typing import Optional
app = Flask(__name__)

# ── Caminhos ────────────────────────────────────────────────────────────────
# BASE_DIR = pasta onde este controller.py está (raiz do projeto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho do main.py (o bot em si). Ajusta se seu arquivo tiver outro nome/local.
MAIN_PATH = os.path.join(BASE_DIR,"main.py")

# Caminho do HTML da interface
CONTROL_HTML = os.path.join(BASE_DIR, "painel","templates","bot-control.html")

# ── Estado global ───────────────────────────────────────────────────────────
_proc = None   # subprocess.Popen do bot (None = parado)


# ── CORS ────────────────────────────────────────────────────────────────────
# Permite que o HTML seja aberto de qualquer origem (file://, localhost,
# IP da rede, etc.) sem o navegador bloquear o fetch.
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# ── Rota "/" — serve o HTML ─────────────────────────────────────────────────
@app.route("/", methods=["GET", "OPTIONS"])
def index():
    if request.method == "OPTIONS":
        return "", 204
    if not os.path.exists(CONTROL_HTML):
        return f"Arquivo não encontrado: {CONTROL_HTML}", 404
    return send_file(CONTROL_HTML)


# ── Rota "/status" — retorna se o bot está rodando ──────────────────────────
@app.route("/status", methods=["GET", "OPTIONS"])
def status():
    global _proc
    if request.method == "OPTIONS":
        return "", 204

    rodando = _proc is not None and _proc.poll() is None
    return jsonify({
        "rodando": rodando,
        "pid": _proc.pid if rodando and _proc is not None else None,
    })


# ── Rota "/start" — liga o bot ──────────────────────────────────────────────
@app.route("/start", methods=["POST", "OPTIONS"])
def start():
    global _proc

    if request.method == "OPTIONS":
        return "", 204

    # Já está rodando?
    if _proc is not None and _proc.poll() is None:
        return jsonify({"ok": False, "erro": "Bot já está rodando"}), 409

    # Existe o arquivo do bot?
    if not os.path.exists(MAIN_PATH):
        return jsonify({
            "ok": False,
            "erro": f"Arquivo não encontrado: {MAIN_PATH}"
        }), 404

    # No Windows, CREATE_NEW_PROCESS_GROUP permite matar a árvore toda depois
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        # Abre o bot como processo separado, redirecionando stdout/stderr
        # pra um arquivo de log (em vez de DEVNULL), pra você poder debugar
        # se algo der errado.
        log_path = os.path.join(BASE_DIR, "bot_runtime.log")
        log_file = open(log_path, "a", encoding="utf-8", errors="replace")

        _proc = subprocess.Popen(
            [sys.executable, MAIN_PATH],
            cwd=BASE_DIR,
            creationflags=flags,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        # Pequena espera — se o main.py falhar imediatamente (ex: erro de
        # import), queremos detectar e reportar em vez de dizer "ok" enganoso.
        time.sleep(0.6)

        if _proc.poll() is not None:
            return jsonify({
                "ok": False,
                "erro": f"Bot saiu com código {_proc.returncode}. Veja bot_runtime.log"
            }), 500

        return jsonify({"ok": True, "pid": _proc.pid})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "erro": str(e)}), 500


# ── Rota "/stop" — desliga o bot ────────────────────────────────────────────
@app.route("/stop", methods=["POST", "OPTIONS"])
def stop():
    global _proc

    if request.method == "OPTIONS":
        return "", 204

    if _proc is None or _proc.poll() is not None:
        _proc = None
        return jsonify({"ok": False, "erro": "Bot não está rodando"}), 409

    try:
        if os.name == "nt":
            # No Windows, o main.py abre threads + subprocess (cloudflared).
            # taskkill /T mata a árvore inteira.
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(_proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            _proc.terminate()

        _proc.wait(timeout=5)

    except subprocess.TimeoutExpired:
        try:
            _proc.kill()
        except Exception:
            pass
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        _proc = None

    return jsonify({"ok": True})


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🎛️  BOT CONTROLLER")
    print("=" * 60)
    print(f"📁 BASE_DIR:      {BASE_DIR}")
    print(f"🤖 MAIN_PATH:     {MAIN_PATH}")
    print(f"   existe?        {'✅ sim' if os.path.exists(MAIN_PATH) else '❌ NÃO'}")
    print(f"🌐 CONTROL_HTML:  {CONTROL_HTML}")
    print(f"   existe?        {'✅ sim' if os.path.exists(CONTROL_HTML) else '❌ NÃO'}")
    print()
    print("🌍 Acesso:")
    print("   Local:  http://localhost:5001")
    print("   Rede:   http://<seu-ip>:5001")
    print()
    print("💡 Deixe este terminal ABERTO enquanto usa o botão.")
    print("   Ctrl+C para encerrar.")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)