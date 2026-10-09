import time
from Bot.Session import SESSION
from utils.dictionnaries import track_dictionary

vistos = set()

while True:
    try:
        tid   = getattr(SESSION, 'm_track_id', None)
        tname = getattr(SESSION, 'track_name', None)

        if tid is not None and tid not in vistos:
            vistos.add(tid)
            dict_nome = track_dictionary.get(tid, ("?",))[0]
            print(f"🏁 ID {tid:>3} | jogo='{tname}' | dict='{dict_nome}'")
    except Exception:
        pass

    time.sleep(2)