import requests
import json

API_KEY = "sk-c737f903b2eb4115bc203fb1782609ba"
url= "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
    }
def analisar_dados_auto():
 try:
    with open("dados_dos_pneus.json", "r", encoding="utf-8") as f:
       pneu_data = json.load(f)
    with open("dados_dano.json", "r", encoding="utf-8")as f:
        dano_data =json.load(f)
    with open("dados_telemetria.json","r", encoding="utf-8")as f:
        telemetria_data =json.load(f)
    with open("dados_voltas.json","r", encoding="utf-8")as f:
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

    data = {
    "model": "deepseek-chat",
    "messages": [
        {
            "role": "system",
            "content": (
                "Você é um assistente especializado em análise de corridas de Fórmula 1. "
                "Sua função é interpretar dados de pneus, danos, telemetria e voltas, "
                "e responder de forma clara e resumida."
            )
        },
        {
            "role": "user",
            "content": (
                "Com base nos dados fornecidos, faça a análise e organize a resposta neste formato:\n\n"
                "1. 🛞 **Desgaste de Pneus**\n"
                "   - Piloto com maior desgaste (nome e valor %)\n"
                "   - Outros pilotos com desgaste relevante (se houver)\n\n"
                "2. 💥 **Danos no Carro**\n"
                "   - Piloto mais afetado (nome e tipo de dano)\n"
                "   - Outros pilotos com danos relevantes (se houver)\n\n"
                "3. ⚡ **Tipos de Pneus em Uso**\n"
                "   - Liste cada piloto e o tipo de pneu atual (Macio, Médio, Duro, Chuva)\n\n"
                "Dados completos:\n"
                f"{json.dumps(dados_completos)}"
            )
        }
       ],
       "max_tokens": 1000,
       "temperature": 0.7
      }

     # Fazer requisição para a API
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()  # Levanta exceção para erros HTTP
        
    resposta = response.json()
        
        # Verificar se a resposta tem a estrutura esperada
    if "choices" in resposta and len(resposta["choices"]) > 0:
            return resposta["choices"][0]["message"]["content"]
    else:
            return "❌ Resposta inesperada da API DeepSeek"
            
 except requests.exceptions.RequestException as e:
        return f"❌ Erro de conexão com a API: {e}"
 except json.JSONDecodeError as e:
        return f"❌ Erro ao ler arquivos JSON: {e}"
 except Exception as e:
        return f"⚠️ Erro inesperado: {e}"
