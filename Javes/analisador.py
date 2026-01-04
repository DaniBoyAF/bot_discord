import PyPDF2
import requests
import json
import base64
API_KEY = "sk-31be9203603441c4be227e0b09e6daa3"
def analisar_clipe(caminho_video):
    with open("regras/Regulamento_Midnight_Racers1.pdf", "rb") as f:
        pdf_bytes = f.read()
    with open(caminho_video, "rb") as v:
        video_bytes = base64.b64encode(v.read()).decode("utf-8")

    resposta = API_KEY.chat.completions.create(
        model="gpt-5-vision",
        messages=[
            {"role": "system", "content": "Você é um comissário de corrida da FIA."},
            {"role": "user", "content": [
                {"type": "text", "text": "Analise o clipe e o regulamento e diga quem causou a infração e a penalidade correta."},
                {"type": "input_file", "input": pdf_bytes, "mime_type": "application/pdf"},
                {"type": "input_file", "input": video_bytes, "mime_type": "video/mp4"}
            ]}
        ]
    )

    return resposta.choices[0].message["content"]
