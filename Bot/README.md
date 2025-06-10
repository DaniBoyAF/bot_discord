# F1 24 Telemetry Application Bot discord

##
Este documento lista os principais comandos que podem ser utilizados em um bot do Discord para transmitir e interagir com dados de telemetria da F1 24. Ideal para acompanhar corridas ao vivo, gerar relatórios e interagir com informações da corrida em tempo real.

✨ Comandos Gerais

.ola

Responde com uma saudação personalizada ao usuário.

.comando

Lista todos os comandos disponíveis do bot.

.gerar_audio

Fala uma mensagem de exemplo com voz gerada via Google TTS.

.listar_vozes

Lista vozes disponíveis na sua conta ElevenLabs (se configurado).

⚡ Comandos de Corrida ao Vivo

.delta

Informa qual piloto está com o melhor tempo na pista no momento.

.gap

Informa a diferença de tempo entre os 5 primeiros colocados.

.pneusv

Informa o tipo de pneu e quantidade de voltas dos 5 pilotos mais rápidos.

.pitstop

Lista os pilotos que fizeram pitstops e quantas vezes pararam.

.status [nome]

Mostra o status detalhado de um piloto (ERS, pneus, danos, etc).

.clima

Informa o tipo de sessão, clima, temperatura da pista/ar e voltas completas.

📄 Geração e Envio de Relatórios

.gerarpdf

Gera um PDF com:

Informações da sessão

Dados de todos os pilotos (melhor volta, ERS, pneus, etc)

Estatísticas finais (quem mais fez pitstops, melhor volta)

Gráfico de tempos de volta

.enviarpdf

Envia o PDF relatorio_de_corrida_completo.pdf para o chat, se existir.

.telemetriapdf

Envia o PDF telemetria geral.pdf com informações brutas da telemetria.

🌊 Integração com Voz (Google TTS)

Ao usar comandos como .delta, .gap, .clima, você pode fazer o bot falar usando a biblioteca gTTS.

A voz é gerada localmente e enviada no canal de voz onde o usuário está conectado.

🚀 Execução

Execute o bot com:

python main.py

Certifique-se que:

O jogo F1 24 esteja enviando os dados UDP para o IP da sua máquina

O listener UDP esteja ativo via start_udp_listener()

🌐 Requisitos

Python 3.9+

discord.py

matplotlib

gTTS

reportlab
##
