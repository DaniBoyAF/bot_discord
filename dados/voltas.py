import json
import plotly.graph_objects as go
import random
def gerar_cor_aleatoria():
    return "rgb({},{},{})".format(random.randint(0,255), random.randint(0,255), random.randint(0,255))
def gerar_boxplot(arquivos_json , nome_pista=""):
    fig = go.Figure()
    pilotos = []
    melhores_voltas = []
    cores_aleatorias = []

    # Primeiro, colete os melhores tempos para calcular o gap
    for arquivo in arquivos_json:
        with open(arquivo, "r") as f:
            dados = json.load(f)
        piloto_nome = dados["nome_piloto"]
        tempos_voltas = [volta["lap_time_in_ms"] / 1000.0 for volta in dados["voltas"]]
        if tempos_voltas:
            melhor_volta = min(tempos_voltas)
            pilotos.append(piloto_nome)
            melhores_voltas.append(melhor_volta)
        else:
            pilotos.append(piloto_nome)
            melhores_voltas.append(None)
        # Gera cor aleatória para cada piloto
        cores_aleatorias.append(gerar_cor_aleatoria())

    melhor_absoluto = min([v for v in melhores_voltas if v is not None])

    # Agora, adicione os boxplots
    for idx, arquivo in enumerate(arquivos_json):
        with open(arquivo, "r") as f:
            dados = json.load(f)
        piloto_nome = dados["nome_piloto"]
        tempos_voltas = [volta["lap_time_in_ms"] / 1000.0 for volta in dados["voltas"]]
        cor_time = cores_aleatorias[idx]
        fig.add_trace(go.Box(
            y=tempos_voltas,
            name=piloto_nome,
            boxmean="sd",
            marker_color=cor_time,
            line=dict(width=1),
            whiskerwidth=1,
            boxpoints="outliers"
        ))

        # Adiciona anotação com melhor volta e gap
        if melhores_voltas[idx] is not None:
            gap = melhores_voltas[idx] - melhor_absoluto
            fig.add_annotation(
                x=piloto_nome,
                y=melhor_absoluto - 0.5,
                text=f"{melhores_voltas[idx]:.2f}s<br>+{gap:.2f}",
                showarrow=False,
                font=dict(size=12),
                align="center"
            )

    fig.update_layout(
        title={
        "text": "Smoothed Laptime (s)<br><span style='font-size:16px;color:gray;'>Seu texto extra aqui</span>",
        "x":0.5,
        "xanchor": "center"
    },
        yaxis_title="Tempo de volta (s)",
        boxmode="group",
        showlegend=False,
        font=dict(size=14),
        margin=dict(l=40, r=40, t=60, b=120),
        xaxis=dict(tickangle=0)
    )

    fig.write_image("corrida.png")