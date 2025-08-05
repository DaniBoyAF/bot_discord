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

| Comando           | Descrição                                                                 |
|-------------------|---------------------------------------------------------------------------|
| `.ola`            | Saúda o usuário.                                                          |
| `.comando`        | Lista todos os comandos disponíveis.                                      |
| `.delta`          | Mostra o piloto mais rápido no momento.                                   |                                  
| `.pneusv`         | Mostra pneus e voltas dos 5 mais rápidos.                                 |             
| `.status [nome]`  | Mostra status detalhado de um piloto.                                     |
| `.clima`          | Mostra clima, tipo de sessão e voltas completas.                          |
| `.voltas [nome]`  | Mostra os tempos de volta de um piloto.                                   |
| `.grafico`        | Envia o gráfico dos tempos de volta.                                      |
| `.tabela`         | Envia a tabela ao vivo dos pilotos.                                       |
| `.Tabela_Qualy`   | Mostra os melhores tempos da qualificação.                                |
| `.media_lap`      | Mostra a média de tempo de volta dos pilotos.                             |
| `.danos [nome]`   | Mostra os danos do carro de um piloto.                                    |                                           
| `.parar_tabela`   | Para o envio automático da tabela.                                        |
| `.parar_voltas`   | Para o envio automático de voltas.                                        |
|  `.painel`        | Faz um html sem deley grande                                              |
| `.pneusp`         | Faz um html do pneus sem deley grande                                     |
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

---

## 📝 Observações

- O bot precisa estar em um servidor Discord com permissões para ler e escrever mensagens.
- Para comandos de gráficos e relatórios, os arquivos são enviados diretamente no chat.

---

## 📧 Suporte

Dúvidas ou sugestões? Abra uma issue ou entre em contato pelo Discord!