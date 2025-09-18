# 🏎️ F1 24 Telemetry Discord Bot

Um bot para Discord que transmite dados de telemetria do F1 24 em tempo real, gera relatórios, gráficos e permite interações rápidas durante corridas.

---

## ✨ Funcionalidades

- **Comandos ao vivo:** Gap, delta, pneus, pitstops, clima, status detalhado e mais.
- **Relatórios em PDF:** Geração automática de relatórios completos e telemetria bruta.
- **Gráficos:** Visualização dos tempos de volta de todos os pilotos.
- **Totalmente integrado ao F1 24 via UDP.**

---

## 📋 Comandos Principais

| Comando               | Descrição                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| `.ola`                | O bot cumprimenta você.                                                   |
| `.status [nome]`      | Mostra o status de um piloto (ex: em pista, no pit, etc).                 |
| `.clima`              | Mostra informações do clima atual.                                        |
| `.delta`              | Mostra o delta de tempo dos pilotos.                                      |
| `.pneusv`             | Mostra informações dos pneus dos pilotos.                                 |
| `.danos [nome]`       | Mostra os danos do carro de um piloto.                                    |
| `.pilotos`            | Lista os pilotos da sessão.                                               |
| `.Tabela_Qualy`       | Mostra os melhores tempos da qualificação.                                |
| `.sobre`              | Mostra informações sobre o bot.                                           |
| `.voltas [nome]`      | Mostra os tempos de volta de um piloto.                                   |
| `.salvar_dados`       | Envia mensagens automáticas com setores e pneus dos pilotos.              |
| `.parar_salvar`       | Para o envio automático de dados.                                         |
| `.velocidade`         | Mostra o piloto mais rápido no speed trap.                                |
| `.ranking`            | Mostra o top 10 da corrida.                                               |
| `.grafico`            | Envia o gráfico dos tempos de volta.                                      |
| `.grafico_midspeed`   | Envia o gráfico da velocidade média dos pilotos.                          |
| `.media_setor`        | Mostra a média de tempo de setor dos pilotos.                             |
| `.grafico_maxspeed`   | Envia o gráfico da velocidade máxima dos pilotos.                         |
| `.media_lap`          | Mostra a média de tempo de volta dos pilotos.                             |
| `.tabela`             | Envia a tabela ao vivo dos pilotos.                                       |
| `.parartabela`        | Para o envio automático da tabela.                                        |
| `.painel`             | Faz um HTML do painel sem delay grande.                                   |
| `.pneusp`             | Faz um HTML dos pneus sem delay grande.                                   |
| `.setor`              | Envia gráfico dos melhores setores de cada piloto.                        |
| `.melhores_setores`   | Mostra os melhores setores de cada piloto no chat.                        |
| `.grafico_velocidade` | Envia gráfico de barras das velocidades dos pilotos.                      |
---

## 📄 Relatórios

- **Relatório Completo:**  
  - Informações da sessão  
  - Dados de todos os pilotos (melhor volta, ERS, pneus, etc)  
  - Estatísticas finais (pitstops, melhor volta)  
  - Gráfico de tempos de volta

- **Telemetria Bruta:**  
  - PDF com dados crus da sessão

---

## 🚀 Como Executar

1. Instale os requisitos:
    ```bash
    pip install -r requirements.txt
    ```
2. Certifique-se de que o F1 24 está enviando dados UDP para o IP da sua máquina.
3. Inicie o listener UDP (caso necessário):
    ```python
    start_udp_listener()
    ```
4. Execute o bot:
    ```bash
    python main.py
    ```

---

## 🌐 Requisitos

- Python 3.9+
- [discord.py](https://github.com/Rapptz/discord.py)
- matplotlib
- reportlab
- plotly

---

## 📝 Observações

- O bot precisa estar em um servidor Discord com permissões para ler e escrever mensagens.
- Para comandos de gráficos e relatórios, os arquivos são enviados diretamente no chat.

---

## 📧 Suporte

Dúvidas ou sugestões? Abra uma issue ou entre em contato pelo Discord!