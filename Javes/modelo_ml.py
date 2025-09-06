import json 
import time
def dados_geral():
    with open("dados_dos_pneus.json", "r", encoding="utf-8") as f:
        data1 = json.load(f)
    with open("dados_de_voltas.json","r",encoding="utf-8") as f:
        data2 = json.load(f)
    with open("dados_dano.json","r",encoding="utf-8") as f:
        data3 = json.load(f)
    with open("dados_da_SESSION.json", "r", encoding="utf-8") as f:
        dados_sessao = json.load(f)
    with open("dados_telemetria.json", "r", encoding="utf-8") as f:
        dados_telemetria = json.load(f)
    with open("dados_pra_o_painel.json", "r", encoding="utf-8") as f:  # ⚠️ corrigido para leitura
        painel_data = json.load(f)

    return {
        "pneus": data1,
        "voltas": data2,
        "dano": data3,
        "sessao": dados_sessao,
        "telemetria": dados_telemetria,
        "painel": painel_data
    }

#como tirar do json 
# for piloto in dados["pneus"]:
    #print(piloto["nome"], piloto["tyres"], piloto["tyre_wear"])
while True:
 def taxa_desgaste(dados):
    desgaste_por_piloto = {}
    pior_piloto = None
    pior_media = -1

    for piloto, info in dados["pneus","sessao"].items():
        nome = info.get("nome", piloto)
        tipo = info.get("tyres", "Desconhecido")
        pista = info.get("nome_pista")
        desgaste = info.get("tyre_wear", [])  # ✅ corrigido

        if desgaste:
            media = sum(desgaste) / len(desgaste)
            pior_desgaste = max(desgaste)

            # salva os dados no dicionário
            desgaste_por_piloto[piloto] = {
                "nome": nome,
                "composto": tipo,
                "media_desgaste": media,
                "pior_pneu": pior_desgaste,
                "valores": desgaste,
                "pista": pista
            }

            # verifica quem tem maior desgaste médio
            if media > pior_media:
                pior_media = media
                pior_piloto = piloto
    time.sleep(10)
    return desgaste_por_piloto, pior_piloto, pior_media

     
