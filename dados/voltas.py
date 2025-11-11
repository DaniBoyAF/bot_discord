import plotly.graph_objects as go
import random
import plotly.io as pio 
def gerar_cor_aleatoria():
    """Gera cores RGB aleatórias"""
    return "rgb({},{},{})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def gerar_boxplot(pilotos, nome_pista="Track", total_voltas=0, nome_arquivo="corrida.png"):
    """
    Gera boxplot estilo F1 com dados de pilotos do banco.
    
    Args:
        pilotos: Lista de objetos com atributo 'voltas' e 'nome'
        nome_pista: Nome do circuito
        total_voltas: Total de voltas
        nome_arquivo: Nome do arquivo de saída
    """
    fig = go.Figure()
    
    pilotos_nomes = []
    melhores_voltas = []
    cores_aleatorias = []

    # Coleta melhores tempos para calcular gaps
    for piloto in pilotos:
        nome = getattr(piloto, "nome", "Piloto")
        voltas = getattr(piloto, "voltas", [])
        
        tempos_validos = [v.get("tempo_total", 0) for v in voltas if v.get("tempo_total", 0) > 0]
        
        if tempos_validos:
            melhor = min(tempos_validos)
            pilotos_nomes.append(nome)
            melhores_voltas.append(melhor)
        else:
            pilotos_nomes.append(nome)
            melhores_voltas.append(None)
        
        cores_aleatorias.append(gerar_cor_aleatoria())

    # Melhor tempo absoluto
    melhor_absoluto = min([v for v in melhores_voltas if v is not None]) if any(melhores_voltas) else 0

    # Adiciona boxplots
    for idx, piloto in enumerate(pilotos):
        nome = getattr(piloto, "nome", "Piloto")
        voltas = getattr(piloto, "voltas", [])
        
        tempos_validos = [v.get("tempo_total", 0) for v in voltas if v.get("tempo_total", 0) > 0]
        
        if not tempos_validos:
            continue
        
        cor = cores_aleatorias[idx]
        
        fig.add_trace(go.Box(
            y=tempos_validos,
            name=nome,
            boxmean="sd",
            marker_color=cor,
            line=dict(width=2),
            whiskerwidth=0.8,
            boxpoints="outliers",
            marker=dict(size=6, opacity=0.7)
        ))

        # Anotação com melhor volta e gap
        if melhores_voltas[idx] is not None:
            gap = melhores_voltas[idx] - melhor_absoluto
            gap_texto = f"+{gap:.3f}" if gap > 0 else "LEADER"
            
            fig.add_annotation(
                x=nome,
                y=melhor_absoluto - (max(tempos_validos) - min(tempos_validos)) * 0.05,
                text=f"<b>{melhores_voltas[idx]:.3f}s</b><br>{gap_texto}",
                showarrow=False,
                font=dict(size=11, color='white'),
                align="center",
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor='white',
                borderwidth=1,
                borderpad=4
            )

    # Layout estilo F1
    fig.update_layout(
        title={
            "text": f"<b>SMOOTHED LAPTIME ANALYSIS</b><br><span style='font-size:14px;color:#aaa;'>{nome_pista} | {total_voltas} Laps</span>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 22, "color": "white"}
        },
        yaxis_title="<b>Lap Time (s)</b>",
        boxmode="group",
        showlegend=False,
        font=dict(size=13, color='white', family='Arial'),
        margin=dict(l=60, r=60, t=100, b=80),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=12, color='white'),
            showgrid=False
        ),
        yaxis=dict(
            tickfont=dict(size=12, color='white'),
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False
        ),
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#0a0a0a'
    )
    
    # Salva imagem
    fig.write_image(nome_arquivo, width=1600, height=900, scale=2)
    print(f"✅ Boxplot salvo: {nome_arquivo}")