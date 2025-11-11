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

def melhor_setor_gap(pilotos, nome_arquivo="grafico_melhor_setor.png"):
    """
    Gera 1 PNG com 3 subplots verticais (estilo F1 Data Analysis).
    """
    num_setores = 3
    
    # Cria figura com 3 subplots VERTICAIS (3 linhas, 1 coluna)
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    fig.patch.set_facecolor('#0a0a0a')  # Fundo preto total

    for setor_idx in range(num_setores):
        ax = axes[setor_idx]
        ax.set_facecolor('#1a1a1a')  # Fundo do subplot cinza escuro
        
        nomes_pilotos = []
        melhores_setores = []
        
        for piloto in pilotos:
            nome = getattr(piloto, 'nome', 'Desconhecido')
            todas_voltas = getattr(piloto, 'todas_voltas_setores', [])
            
            # Pega todos os tempos desse setor
            tempos_setor = []
            for volta in todas_voltas:
                if setor_idx == 0:
                    tempo = volta.get('setor1', None)
                elif setor_idx == 1:
                    tempo = volta.get('setor2', None)
                else:
                    tempo = volta.get('setor3', None)
                
                if tempo and tempo > 0:
                    tempos_setor.append(tempo)
            
            if tempos_setor:
                melhor = min(tempos_setor)
                nomes_pilotos.append(nome)
                melhores_setores.append(melhor)
        
        if not melhores_setores:
            ax.text(0.5, 0.5, f'NO DATA\nSECTOR {setor_idx + 1}', 
                   ha='center', va='center', fontsize=18, color='#FF00FF', 
                   fontweight='bold', style='italic')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            continue
        
        # Calcula o gap
        melhor_absoluto = min(melhores_setores)
        gaps = [s - melhor_absoluto for s in melhores_setores]
        
        # Ordena por gap
        pilotos_gaps = sorted(zip(nomes_pilotos, gaps), key=lambda x: x[1])
        nomes_ordenados = [x[0] for x in pilotos_gaps]
        gaps_ordenados = [x[1] for x in pilotos_gaps]
        
        # Gera cores vibrantes
        cores_aleatorias = [gerar_cor_aleatoria() for _ in nomes_ordenados]
        
        # Plota barras
        bars = ax.bar(nomes_ordenados, gaps_ordenados, color=cores_aleatorias, 
                     edgecolor='none', linewidth=0, alpha=1.0, width=0.8)
        
        # Configurações do eixo Y
        ax.set_ylabel("GAP (s)", fontsize=14, fontweight='bold', color='white', 
                     labelpad=10)
        max_gap = max(gaps_ordenados) if gaps_ordenados else 1
        ax.set_ylim(0, max_gap * 1.2)
        
        # Configurações do eixo X
        ax.set_xlabel("")
        ax.tick_params(axis='x', rotation=0, labelsize=11, colors='white', 
                      pad=5, length=0)
        ax.tick_params(axis='y', labelsize=11, colors='white', length=0)
        
        # Grid horizontal sutil
        ax.grid(axis='y', alpha=0.2, linestyle='-', color='#444444', linewidth=0.8)
        ax.set_axisbelow(True)
        
        # Remove todas as bordas dos eixos
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Adiciona valores NO TOPO das barras
        for bar, gap, nome in zip(bars, gaps_ordenados, nomes_ordenados):
            altura = bar.get_height()
            # Valor numérico
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                altura + (max_gap * 0.03),
                f"{gap:.3f}", 
                ha='center', 
                va='bottom', 
                fontsize=10,
                fontweight='bold',
                color='white'
            )
        
        # Título estilo F1 (caixa amarela no topo)
        titulo_y = 1.12 if setor_idx == 0 else 1.08
        ax.text(0.02, titulo_y, f" {setor_idx + 1}) ", 
               transform=ax.transAxes, 
               fontsize=20, fontweight='black', ha='left', va='center',
               color='black',
               bbox=dict(boxstyle='square,pad=0.4', facecolor='#FFD700', 
                        edgecolor='none'))
        
        ax.text(0.12, titulo_y, f"BEST SECTORS", 
               transform=ax.transAxes, 
               fontsize=20, fontweight='black', ha='left', va='center',
               color='black',
               bbox=dict(boxstyle='square,pad=0.4', facecolor='#FFD700', 
                        edgecolor='none'))
        
        # Adiciona marca d'água (opcional)
        if setor_idx == 0:
            ax.text(0.98, 1.12, '@YourDataAnalysis', 
                   transform=ax.transAxes, 
                   fontsize=10, ha='right', va='center',
                   color='white', alpha=0.6, style='italic')
    
    # Ajusta espaçamento
    plt.subplots_adjust(hspace=0.4, top=0.96, bottom=0.04)
    
    # Salva
    plt.savefig(nome_arquivo, dpi=300, bbox_inches='tight', 
               facecolor='#0a0a0a', edgecolor='none')
    plt.close()
    
    print(f"✅ Gráfico salvo: {nome_arquivo}")