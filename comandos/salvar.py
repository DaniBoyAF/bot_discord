import sys
import os
import time
import json
async def salvar(ctx):
   texto="salvos com sucesso!"
   try:
     with open("dados_dos_pneus.json", "r", encoding="utf-8") as f:
       pneu_data = json.load(f)
     with open("dados_dano.json", "r", encoding="utf-8")as f:
        dano_data =json.load(f)
     with open("dados_telemetria.json","r", encoding="utf-8")as f:
        telemetria_data =json.load(f)
     with open("dados_de_voltas.json","r", encoding="utf-8")as f:
        voltas_data =json.load(f)
     with open("dados_da_SESSION.json","r",encoding="utf-8")as f:
      session_data =json.load(f)
     with open("dados_pra_o_painel.json","r",encoding="utf-8")as f:
      painel_data =json.load(f)
     dados_completos ={
      "pneus": pneu_data,
      "dano": dano_data,
      "telemetria": telemetria_data,
       "voltas": voltas_data,
      "session": session_data,
      "painel": painel_data
     }
     with open("dados_Zip.json", "w", encoding="utf-8") as f:
        json.dump(dados_completos, f, indent=2, ensure_ascii=False)
     await ctx.send(texto)
   except json.JSONDecodeError as e:
        return f"❌ Erro ao ler arquivos JSON: {e}"
   except Exception as e:
        return f"⚠️ Erro inesperado: {e}"
  