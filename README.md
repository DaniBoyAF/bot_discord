# 🏎️ F1 24 Telemetry Discord Bot & Web Dashboard

Um ecossistema completo para telemetria do F1 24 em tempo real. Inclui um bot para Discord para comandos rápidos e um Painel Web avançado para análise de engenharia de corrida.

---

## ✨ Funcionalidades

- **🆕 Telemetria de Engenharia:** Acesso a dados de Setup (asas, diferencial, freios), monitoramento de combustível (kg e voltas) e SOC da bateria (ERS).
- **📈 Análise de Pneus Pro:** Gráficos de degradação com regressão linear, cálculo de R² (precisão), remoção automática de outliers e suporte a todos os compostos (incluindo **Super Macio**).
- **⚔️ Comparação de Pilotos:** Interface web para comparar ritmo e desgaste entre dois pilotos simultaneamente.
- **📊 Relatórios Automáticos:** Geração de PDFs de sessão, boxplots de consistência e tabelas de tempos de setores.
- **🌐 Dashboard Web:** Painel em tempo real sem delay via Flask/React.

---

## 📋 Comandos Principais

### 🔧 Telemetria de Engenharia
| Comando | Descrição |
| :--- | :--- |
| `.setup [nome]` | Mostra o setup atual: asas, diferencial, freios, suspensão e pressões. |
| `.ver_fuel` | Monitoramento de combustível (kg), voltas restantes e mapa de mistura. |
| `.desgastes` | Desgaste físico em tempo real (0-100%) dos 4 pneus e idade da borracha. |
| `.ver_ers` | Status da bateria (%), modo de deploy e disponibilidade de DRS. |
| `.status [nome]` | Visão consolidada do piloto (posição, tempos, ERS, pneus). |

### 🏁 Gestão de Prova
| Comando | Descrição |
| :--- | :--- |
| `.ranking` | Top 10 atualizado com intervalos de tempo. |
| `.delta` | Diferença de tempo (Gaps) entre todos os pilotos do grid. |
| `.pneusv` | Composto atual (Visual) e quantos quilômetros/voltas o pneu possui. |
| `.danos [nome]` | Relatório de danos: asas, assoalho, sidepods e desgaste de motor. |

### 📊 Análise & Web
| Comando | Descrição |
| :--- | :--- |
| `.pit_stop` | Link para análise web de estratégia e degradação (Modo Grid/Comparação). |
| `.painel` | Link para o dashboard de telemetria live. |
| `.setor` | Gráfico comparativo dos melhores tempos de cada setor. |
| `.corrida` | Boxplot de consistência para análise de ritmo de prova. |

---

## 🚀 Como Executar

1. **Instale os requisitos:**
    ```bash
    pip install -r requirements.txt
    ```
2. **Configure o F1 24:**
    - Vá em Opções de Telemetria.
    - Ative o envio UDP para o IP da sua máquina na porta `20777`.
3. **Inicie o sistema:**
    ```bash
    python main.py
    ```
4. **Acesse a Web:** O painel estará disponível em `http://localhost:5000`.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask, SQLite3, Ctypes (UDP Parser).
- **Frontend:** React, Tailwind CSS, Chart.js.
- **Relatórios:** ReportLab, Matplotlib, Plotly.
- **Integração:** Discord.py.

---

## 📝 Análise de Degradação (Matemática)

O bot utiliza **Regressão Linear Simples** com filtragem de **Outliers (IQR)** para calcular a perda de performance por volta ($\Delta/lap$). O valor de **R²** indica a confiabilidade dos dados (ex: tráfego ou erros de pilotagem baixam o R²).

---

**GitHub Copilot** | **Gemini 3 Flash (Preview)**