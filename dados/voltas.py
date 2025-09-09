import json
import plotly.graph_objects as go
from utils.dictionnaries import teams_color_dictionary

# A função agora recebe uma lista de caminhos de arquivos JSON
def gerar_boxplot(arquivos_json):
    fig = go.Figure()

    for arquivo in arquivos_json:
        with open(arquivo, "r") as f:
            dados = json.load(f)

        piloto_nome = dados["nome_piloto"]
        id_team = dados["id_team"]
        
        # Cria uma lista apenas com os tempos de volta para o boxplot
        tempos_voltas = [volta["lap_time_in_ms"] / 1000.0 for volta in dados["voltas"]]
        
        # Pega a cor do time usando o dicionário
        cor_time = teams_color_dictionary.get(id_team, "black")
        
        fig.add_trace(go.Box(
            y=tempos_voltas,
            name=piloto_nome,
            boxmean="sd",
            marker_color=cor_time,
            line=dict(width=1),
            whiskerwidth=1
        ))

    fig.update_layout(
        title="Boxplot de tempos por piloto",
        yaxis_title="Tempo (s)",
        boxmode="group",
        showlegend=False
    )

    fig.write_image("corrida.png")