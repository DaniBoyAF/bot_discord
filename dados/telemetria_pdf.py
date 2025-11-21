import matplotlib.pyplot as plt
import random

def gerar_cor_aleatoria():
    """Gera cores vibrantes aleatórias"""
    cores_vivas = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
        '#FF6600', '#FF0066', '#66FF00', '#0066FF', '#6600FF', '#00FF66',
        '#FF3366', '#33FF66', '#3366FF', '#FF6633', '#66FF33', '#6633FF'
    ]
    return random.choice(cores_vivas)

def mostra_graficos_geral(jogadores, total_voltas=None, nome_arquivo="graficos_geral.png"):
    """
    Gera gráfico de linha com tempos de volta por piloto.
    Estilo F1 com fundo escuro.
    
    Args:
        jogadores: Lista de objetos com atributo 'voltas' e 'nome'
        total_voltas: Total de voltas da corrida
        nome_arquivo: Nome do arquivo de saída
    """
    from utils.dictionnaries import tyres_dictionnary
    
    # Configuração do estilo F1
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_facecolor('#1a1a1a')
    
    melhor_tempo = float('inf')
    melhor_volta = None
    melhor_piloto = ''
    melhor_tyres = ''

    # Encontra melhor volta
    for j in jogadores:
        voltas = getattr(j, "voltas", [])
        if len(voltas) >= 2:
            for v in voltas:
                tempo = v.get("tempo_total", 0)
                if tempo > 0 and tempo < melhor_tempo:
                    melhor_tempo = tempo
                    melhor_volta = v.get("volta", None)
                    melhor_piloto = getattr(j, "nome", "Piloto")
                    # valida chave antes de usar .get para evitar passar None
                    chave_tyres = getattr(j, "tyres", None)
                    if chave_tyres is None:
                        melhor_tyres = "N/A"
                    else:
                        # cast seguro para int (ajuste se sua chave for str ou outro tipo)
                        try:
                            melhor_tyres = tyres_dictionnary.get(int(chave_tyres), "N/A")
                        except (ValueError, TypeError):
                            melhor_tyres = tyres_dictionnary.get(chave_tyres, "N/A") 

    # Plota linhas
    max_volta_global = 0
    for j in jogadores:
        voltas = getattr(j, "voltas", [])
        if len(voltas) >= 2:
            tempos = [v.get("tempo_total", 0) for v in voltas if v.get("tempo_total", 0) > 0]
            voltas_num = [v.get("volta", i + 1) for i, v in enumerate(voltas) if v.get("tempo_total", 0) > 0]
            nome = getattr(j, "nome", "Piloto")
            
            if voltas_num:
                max_volta_global = max(max_volta_global, max(voltas_num))
                cor = gerar_cor_aleatoria()
                ax.plot(voltas_num, tempos, label=nome, linewidth=2.5, 
                       marker='o', markersize=4, color=cor, alpha=0.9)

    # Configurações dos eixos
    ax.set_xlabel("Voltas", fontsize=14, fontweight='bold', color='white')
    ax.set_ylabel("Tempo (s)", fontsize=14, fontweight='bold', color='white')
    ax.tick_params(colors='white', labelsize=11)
    
    # Grid
    ax.grid(True, alpha=0.2, linestyle='-', color='#444444', linewidth=0.8)
    ax.set_axisbelow(True)
    
    # Remove bordas
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Título
    if total_voltas:
        titulo = f"LAP TIMES ANALYSIS ({total_voltas} LAPS)"
    else:
        titulo = "LAP TIMES ANALYSIS"
    
    ax.text(0.5, 1.05, titulo, transform=ax.transAxes, 
           fontsize=20, fontweight='black', ha='center', va='center',
           color='black',
           bbox=dict(boxstyle='square,pad=0.5', facecolor='#FFD700', edgecolor='none'))

    # Melhor volta
    if melhor_volta is not None:
        minutos = int(melhor_tempo // 60)
        segundos = int(melhor_tempo % 60)
        milissegundos = int((melhor_tempo - int(melhor_tempo)) * 1000)
        
        texto_melhor = f"🏆 FASTEST LAP: #{melhor_volta} | {melhor_piloto} | {minutos:02}:{segundos:02}.{milissegundos:03} | {melhor_tyres}"
        fig.text(0.5, 0.96, texto_melhor, fontsize=12, color='#00FF00', 
                ha='center', va='top', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))

    # Ajusta limites do eixo X
    if max_volta_global > 0:
        ax.set_xlim(1, max_volta_global)
    
    # Legenda
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9, 
             facecolor='#2a2a2a', edgecolor='white', labelcolor='white')
    
    plt.tight_layout()
    plt.savefig(nome_arquivo, dpi=300, facecolor='#0a0a0a', edgecolor='none')
    plt.close()
    
    print(f"✅ Gráfico salvo: {nome_arquivo}")