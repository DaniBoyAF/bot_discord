import json
import numpy as np
import pandas as pd


def dados_geral():
    with open("dados_dos_pneus.json", "r", encoding="utf-8") as f:
        data1 = json.load(f)
    return data1

def prepara_dados_ia(dados_pneus):
    linhas=[]
    for piloto in dados_pneus:
        nome=piloto.get("tyre_wear", [0, 0, 0, 0])
        tyre=piloto["tyres"]
        tyre_wear=piloto.get("tyre_wear", [0, 0, 0, 0])
    for idx, desgaste in enumerate(tyre_wear):
            linhas.append({"nome": nome, "pneu": idx, "desgaste": desgaste})
    df = pd.DataFrame(linhas)
    return df

