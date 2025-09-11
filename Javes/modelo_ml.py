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

def analise_desgaste(df):
    # 1. Maior e menor desgaste por piloto
    resumo = df.groupby("nome")["desgaste"].agg(["max", "min"]).reset_index()
    print("Maior e menor desgaste por piloto:")
    print(resumo)

    # 2. Mostrar o desgaste de todos
    print("\nDesgaste de todos os pneus de todos os pilotos:")
    print(df)

    # 4. Salvar cada piloto em um arquivo separado
    for nome, grupo in df.groupby("nome"):
        grupo.to_csv(f"{nome}_desgaste.csv", index=False)

    return resumo, df