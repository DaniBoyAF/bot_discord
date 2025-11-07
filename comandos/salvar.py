import json
import os
import time
from datetime import datetime

async def salvar(ctx):
    try:
        # 📁 Cria pasta "salvamentos" se ainda não existir
        pasta_salvamentos = "salvamentos"
        os.makedirs(pasta_salvamentos, exist_ok=True)

        # 🕒 Nome com data/hora para evitar sobrescrita
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 🗂️ Lista de arquivos a salvar
        arquivos = [
            "dados_dos_pneus.json",
            "dados_dano.json",
            "dados_telemetria.json",
            "dados_de_voltas.json",
            "dados_da_SESSION.json",
            "dados_pra_o_painel.json"
        ]

        # 🧠 Salva cópia de cada um
        for nome_arquivo in arquivos:
            if os.path.exists(nome_arquivo):
                with open(nome_arquivo, "r", encoding="utf-8") as f:
                    dados = json.load(f)

                novo_nome = f"{pasta_salvamentos}/salvamento_{timestamp}_{nome_arquivo}"
                with open(novo_nome, "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=2, ensure_ascii=False)
            else:
                await ctx.send(f"⚠️ Arquivo não encontrado: {nome_arquivo}")

        await ctx.send("✅ Todos os dados foram salvos com sucesso!")

    except json.JSONDecodeError as e:
        await ctx.send(f"❌ Erro ao ler arquivos JSON: {e}")
    except Exception as e:
        await ctx.send(f"⚠️ Erro inesperado: {e}")
