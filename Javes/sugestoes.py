import Javes.modelo_ml as ml

def analisador_desgaste(dados_geral):
    while True:
        resultado = ml.taxa_desgaste(dados_geral)
        if not resultado:
            break
    return resultado