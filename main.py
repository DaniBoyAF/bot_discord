import discord
from discord.ext import commands
import asyncio
import threading
import time
import sqlite3

import threading
from comandos.pneusv import comando_pneusv
from comandos.delta import comando_delta  # se o nome correto for esse
from Bot.parser2024 import start_udp_listener
from comandos.clima import comando_clima
from comandos.pilotos import commando_piloto
from comandos.danos import danos as comandos_danos
from comandos.media import comando_media 
from dados.voltas import gerar_boxplot
from Bot.Session import SESSION


from Javes.modelo_ml import analisar_dados_auto

import PyPDF2

import json                   
from threading import Thread
import subprocess
import os
import shutil
import re
from painel.app import app

TEMPO_INICIO = False
TEMPO_INICIO_TABELA = False
TEMPO_INICIO_VOLTAS = False
TEMPO_INICIO_TABELA_Q = False
sessao_id_atual = None
public_url = None
_cloudflared_proc = None
inicio= time.time()
tempo_maximo = 600 * 60 
# Corrige o caminho para importar módulos de fora da pasta
intents =discord.Intents.default()
intents.message_content=True
bot =commands.Bot(command_prefix=".", intents=intents)
@bot.event
async def on_ready():
    global TEMPO_INICIO_VOLTAS
    TEMPO_INICIO_VOLTAS = True
    print("Bot on")
    bot.loop.create_task(volta_salvar(bot))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `.comando` para ver a lista de comandos.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumento obrigatório ausente. Verifique o comando e tente novamente.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Este comando está em cooldown. Tente novamente em {error.retry_after:.2f} segundos.")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")
@bot.event
async def on_member_join(membro:discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} entrou no servidor !!")

@bot.event
async def on_member_remove(membro: discord.Member):
    canal = bot.get_channel(1375265281630539846)
    await canal.send(f"{membro.mention} Saiu do servidor !!")
@bot.command()
async def ola(ctx: commands.Context):
    nome= ctx.author.name
    await ctx.reply(f"Olá, {nome}! tudo bem?")
@bot.command()
async def bem(ctx: commands.Context):
    nome=ctx.author.name
    await ctx.reply(f"Que bom {nome}! Digite '.comando' pra mais informações")
@bot.command()
async def Jarves_on(ctx):
    resultado = analisar_dados_auto()
    canal_id = 1413993963072782436
    canal = bot.get_channel(canal_id)
    if not canal:
        await ctx.send("❌ Canal de texto não encontrado.")
        return
    await ctx.send("⚠️ Deseja continuar? Responda com `sim` ou `não`.")
    def check(m):# isso ver a mensagem sim ou não
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["sim", "não"]

    resposta = await bot.wait_for("message", check=check)
    if resposta.content.lower() == "sim":
        await ctx.send("✅ Continuando...")
        await ctx.send(resultado)
    else:
        await ctx.send("❌ Análise cancelada.")


@bot.command()
async def comando(ctx: commands.Context):
    await ctx.reply("""📋 **Lista de Comandos:**

**Básicos:**
.ola            - O bot cumprimenta você
.bem            - Responde positivamente
.sobre          - Informações sobre o bot

**Telemetria:**
.status         - Status de um piloto
.clima          - Informações do clima
.delta          - Delta de tempo dos pilotos
.pneusv         - Informações dos pneus
.danos          - Danos do carro
.velocidade     - Piloto mais rápido no speed trap
.ranking        - Top 10 da corrida

**Voltas & Análise:**
.voltas         - Tempos de volta de um piloto
.setor          - Gráfico de setores (3 em 1)
.grafico        - Gráfico de tempos de volta
.corrida        - Boxplot da corrida
.media_lap      - Média de tempo de volta

**Pilotos & Sessões:**
.pilotos        - Lista pilotos da sessão
.historico      - Últimas 10 sessões salvas

**Automação:**
.salvar_dados   - Inicia salvamento automático
.parar_salvar   - Para salvamento automático
.tabela         - Tabela ao vivo
.parar_tabela   - Para tabela

**Regras & Clips:**
.regras         - Salva PDF de regras no banco
.ver_regras     - Lista regras salvas (se implementado)
.clip           - Salva vídeo no banco
.ver_clips      - Lista clips salvos
.info_clip <ID> - Detalhes de um clip
.deletar_clip <ID> - Remove clip

**Web/Painel:**
.painel         - Link do painel web
.pneusp         - Painel de pneus
.grafico_web    - Gráfico web
.media_HD       - Média HD
.pit_stop       - Análise de pit stops

**IA:**
.Jarves_on      - Análise com IA (experimental)

💡 Use `.comando` para ver esta lista novamente.""")
@bot.command()
async def sobre(ctx:commands.Context):
 await ctx.reply("Sou um bot que pode falar com radio e criar pdf.")
@bot.command()
async def voltas(ctx,*,piloto: str):
    from Bot.jogadores import get_jogadores
    jogadores= get_jogadores()
    piloto = piloto.lower()
    for j in jogadores:
        if piloto in j.name.lower():
            todas_voltas = getattr(j,"todas_voltas_setores",[])
            voltas = [f"Volta {v['volta']}: {v['tempo_total']:.3f}s" for v in todas_voltas]
            texto ="\n".join(voltas) or "não a dados sobre os registradas."
            await ctx.send(f"📊 Tempos de volta de {j.name}:\n```{texto}```")
            return
    await ctx.send("❌ Piloto não encontrado.")
@bot.command()#pronto
async def velocidade(ctx):#pronto
    """Comando para mostrar o piloto mais rápido no speed trap."""
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()

    m_rapido = max(jogadores, key=lambda j: j.speed_trap)
    await ctx.send(f"🚀 {m_rapido.name} foi o mais rápido no speed trap: {m_rapido.speed_trap:.2f} km/h")
@bot.command()
async def setor(ctx):
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Pega a sessão mais recente
    cursor.execute('SELECT MAX(id) FROM sessoes')
    sessao_id = cursor.fetchone()[0]
    
    if not sessao_id:
        await ctx.send("❌ Nenhuma sessão encontrada.")
        conn.close()
        return
    
    # Pega dados dos pilotos e voltas
    cursor.execute('''
    SELECT p.nome, v.numero_volta, v.tempo_volta, v.setor1, v.setor2, v.setor3
    FROM pilotos p
    JOIN voltas v ON p.id = v.piloto_id
    WHERE p.sessao_id = ?
    ORDER BY p.nome, v.numero_volta
    ''', (sessao_id,))
    
    dados = cursor.fetchall()
    conn.close()
    
    if not dados:
        await ctx.send("❌ Nenhum dado de voltas encontrado.")
        return
    
    # Organiza dados por piloto
    pilotos_dict = {}
    for nome, volta, tempo, s1, s2, s3 in dados:
        if nome not in pilotos_dict:
            pilotos_dict[nome] = {
                'nome': nome,
                'voltas': [],
                'todas_voltas_setores': []
            }
        pilotos_dict[nome]['todas_voltas_setores'].append({
            'volta': volta,
            'tempo_total': tempo,
            'setor1': s1,
            'setor2': s2,
            'setor3': s3
        })
    
    pilotos = list(pilotos_dict.values())
    
    # Classe temporária para transformar dicionário em objeto
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d
    
    pilotos_obj = [PilotoTemp(p) for p in pilotos]
    
    # Gera o gráfico
    from dados.setor import melhor_setor_gap
    melhor_setor_gap(pilotos_obj, nome_arquivo="grafico_melhor_setor.png")
    await ctx.send(file=discord.File("grafico_melhor_setor.png"))
@bot.command()
async def ranking(ctx):# pronto
    from Bot.jogadores import get_jogadores
    jogadores = get_jogadores()
    top10 = sorted(jogadores,key=lambda j: j.position )[:10]
    texto="\n".join([f"{j.position}º - {j.name} - {j.speed_trap} km/h" for j in top10])
    await ctx.send(f"🏆 Top 10 da corrida:\n```{texto}```")
@bot.command()
async def grafico(ctx):
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Pega a sessão mais recente
    cursor.execute('SELECT MAX(id) FROM sessoes')
    sessao_id = cursor.fetchone()[0]
    
    if not sessao_id:
        await ctx.send("❌ Nenhuma sessão encontrada.")
        return
    
    # Pega total de voltas
    cursor.execute('SELECT total_voltas FROM sessoes WHERE id = ?', (sessao_id,))
    total_voltas = cursor.fetchone()[0]
    
    # Pega dados dos pilotos e voltas
    cursor.execute('''
    SELECT p.nome, v.numero_volta, v.tempo_volta, v.setor1, v.setor2, v.setor3
    FROM pilotos p
    JOIN voltas v ON p.id = v.piloto_id
    WHERE p.sessao_id = ?
    ORDER BY p.nome, v.numero_volta
    ''', (sessao_id,))
    
    dados = cursor.fetchall()
    conn.close()
    
    # Organiza dados
    pilotos_dict = {}
    for nome, volta, tempo, s1, s2, s3 in dados:
        if nome not in pilotos_dict:
            pilotos_dict[nome] = {'nome': nome, 'voltas': []}
        pilotos_dict[nome]['voltas'].append({
            'volta': volta,
            'tempo_total': tempo,
            'setor1': s1,
            'setor2': s2,
            'setor3': s3
        })
    
    pilotos = list(pilotos_dict.values())
    
    # Cria objetos temporários
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d
    
    pilotos_obj = [PilotoTemp(p) for p in pilotos]
    
    # Gera gráfico
    from dados.telemetria_pdf import mostra_graficos_geral
    mostra_graficos_geral(pilotos_obj, total_voltas=total_voltas, nome_arquivo="grafico_tempos.png")
    await ctx.send(file=discord.File("grafico_tempos.png"))
@bot.command()
async def corrida(ctx):
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Pega a sessão mais recente
    cursor.execute('SELECT MAX(id) FROM sessoes')
    sessao_id = cursor.fetchone()[0]
    
    if not sessao_id:
        await ctx.send("❌ Nenhuma sessão encontrada.")
        conn.close()
        return
    
    # Pega dados da sessão
    cursor.execute('SELECT total_voltas, nome_pista FROM sessoes WHERE id = ?', (sessao_id,))
    resultado = cursor.fetchone()
    total_voltas, nome_pista = resultado
    
    # Pega dados dos pilotos e voltas
    cursor.execute('''
    SELECT p.nome, v.numero_volta, v.tempo_volta, v.setor1, v.setor2, v.setor3
    FROM pilotos p
    JOIN voltas v ON p.id = v.piloto_id
    WHERE p.sessao_id = ?
    ORDER BY p.nome, v.numero_volta
    ''', (sessao_id,))
    
    dados = cursor.fetchall()
    conn.close()
    
    if not dados:
        await ctx.send("❌ Nenhum dado de voltas encontrado.")
        return
    
    # Organiza dados por piloto
    pilotos_dict = {}
    for nome, volta, tempo, s1, s2, s3 in dados:
        if nome not in pilotos_dict:
            pilotos_dict[nome] = {
                'nome': nome,
                'voltas': []
            }
        pilotos_dict[nome]['voltas'].append({
            'volta': volta,
            'tempo_total': tempo,
            'setor1': s1,
            'setor2': s2,
            'setor3': s3
        })
    
    pilotos = list(pilotos_dict.values())
    
    # Classe temporária
    class PilotoTemp:
        def __init__(self, d):
            self.__dict__ = d
    
    pilotos_obj = [PilotoTemp(p) for p in pilotos]
    
    # Gera gráfico boxplot
    from dados.voltas import gerar_boxplot
    gerar_boxplot(pilotos_obj, nome_pista=nome_pista or "Unknown Track", 
                 total_voltas=total_voltas or 0, nome_arquivo="corrida.png")
    await ctx.send(file=discord.File("corrida.png"))
@bot.command()
async def tabela(ctx):  # pronto
    global TEMPO_INICIO_TABELA
    TEMPO_INICIO_TABELA = True
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary
    canal_id = 1381831375006601328
    canal = bot.get_channel(canal_id)
    if not canal:
        await ctx.send("❌ Canal de voz não encontrado.")
        return

    mensagem = await canal.send("🔄 Iniciando o envio de mensagens da tabela ao vivo...")
    while TEMPO_INICIO_TABELA:
        jogador = get_jogadores()
        tyres_nomes = tyres_dictionnary
        jogador = sorted(jogador, key=lambda j: j.position)

        linhas = ["P  #  NAME           GAP      TYRES       TYRES_AGE PIT   "]
        for j in jogador:
            delta_to_leader = getattr(j, "delta_to_leader", "—")
            current_lap = getattr(j, "current_lap", 0)
            if isinstance(current_lap, (int, float)) and current_lap > 0:
                delta_to_leader = f"+{int(current_lap)}L"

            nome = str(getattr(j, "name", "SemNome"))[:14]
            linhas.append(
                f"{j.position:<2} {getattr(j, 'numero', '--'):<2} {nome:<14} "
                f"{str(delta_to_leader):<8} "
            f"{tyres_nomes.get(j.tyres, 'Desconhecido'):<12}{j.tyresAgeLaps}         {'Sim' if j.pit else 'Não':<3}"
            )

        tabela = "```\n" + "\n".join(linhas) + "\n```"
        try:
            await mensagem.edit(content=tabela)
        except Exception as e:
            print(f"Erro ao atualizar tabela: {e}")
            break

        await asyncio.sleep(0.5) # Intervalo de atualização, ajuste conforme necessário
@bot.command()# pronto
async def parar_tabela(ctx):
    global TEMPO_INICIO_TABELA
    TEMPO_INICIO_TABELA = False
    await ctx.send("🛑 Envio automático da tabela parado.")
@bot.command()
async def salvar_dados(ctx):
    await ctx.send("🔄 Salvando dados dos pilotos...")
    bot.loop.create_task(volta_salvar(bot))
async def volta_salvar(bot):
    global TEMPO_INICIO_VOLTAS, sessao_id_atual
    from Bot.jogadores import get_jogadores
    from utils.dictionnaries import tyres_dictionnary, weather_dictionary, color_flag_dict, safetyCarStatusDict, session_dictionary
    from Bot.Session import SESSION
    
    canal_id = 1382050740922482892
    canal = bot.get_channel(canal_id)
    if not canal:
        print("❌ Canal não encontrado.")
        return
    
    mensagem = await canal.send("🔄 Iniciando salvamento no banco de dados...")
    
    # 🏁 Cria a sessão inicial (SE NÃO EXISTIR)
    if sessao_id_atual is None:
        conn = sqlite3.connect('f1_telemetry.db')
        cursor = conn.cursor()
        
        # Pega dados da sessão atual
        track_id = getattr(SESSION, 'm_track_id', -1)
        nome_pista = SESSION.get_track_name(track_id)
        tipo_sessao = session_dictionary.get(getattr(SESSION, 'm_session_type', 0), 'Desconhecido')
        total_voltas = getattr(SESSION, 'm_total_laps', 0)
        clima = weather_dictionary.get(getattr(SESSION, 'm_weather', 0), 'Desconhecido')
        temp_ar = getattr(SESSION, 'm_air_temperature', 0)
        temp_pista = getattr(SESSION, 'm_track_temperature', 0)
        chuva = getattr(SESSION, 'm_rain_percentage', 0)
        safety = safetyCarStatusDict.get(getattr(SESSION, 'm_safety_car_status', 0), 'Desconhecido')
        flag = color_flag_dict.get(getattr(SESSION, 'm_flag', 0), 'Desconhecido')
        
        cursor.execute('''
        INSERT INTO sessoes (nome_pista, tipo_sessao, total_voltas, clima, 
                            temperatura_ar, temperatura_pista, porcentagem_chuva,
                            safety_car_status, flag, velocidade_maxima_geral)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome_pista, tipo_sessao, total_voltas, clima, temp_ar, temp_pista, 
              chuva, safety, flag, 0))
        
        sessao_id_atual = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Sessão criada: #{sessao_id_atual} | {nome_pista} | {tipo_sessao}")
        await mensagem.edit(content=f"✅ Sessão iniciada: **{nome_pista}** ({tipo_sessao})")
    
    pit_quant = {}
    tyres_nomes = tyres_dictionnary
    
    # 🔄 Loop principal de salvamento
    while TEMPO_INICIO_VOLTAS:
        try:
            if time.time() - inicio >= tempo_maximo:
                print("⏱️ Tempo limite atingido (10 horas).")
                break
            
            jogadores = get_jogadores()
            if not jogadores:
                await asyncio.sleep(1)
                continue
            
            conn = sqlite3.connect('f1_telemetry.db')
            cursor = conn.cursor()
            
            # Atualiza velocidade máxima geral da sessão
            maior_speed_geral = 0
            for j in jogadores:
                speed = getattr(j, 'speed_trap', 0)
                if isinstance(speed, list) and speed:
                    speed = max(speed)
                if speed > maior_speed_geral:
                    maior_speed_geral = speed
            
            cursor.execute('UPDATE sessoes SET velocidade_maxima_geral = ? WHERE id = ?',
                          (maior_speed_geral, sessao_id_atual))
            
            # 📊 Salva dados de cada piloto
            for j in jogadores:
                try:
                    nome = getattr(j, 'name', '').strip()
                    if not nome:
                        continue
                    
                    # Inicializa contador de pit stops
                    if nome not in pit_quant:
                        pit_quant[nome] = 0
                    if getattr(j, 'pit', False):
                        pit_quant[nome] += 1
                    
                    # Variáveis auxiliares
                    todas_voltas = getattr(j, "todas_voltas_setores", [])
                    Gas = getattr(j, "fuelRemainingLaps", 0)
                    delta = getattr(j, "delta_to_leader", "—")
                    num = getattr(j, 'numero', 0)
                    
                    speed_trap = getattr(j, 'speed_trap', 0)
                    if isinstance(speed_trap, list) and speed_trap:
                        maior_speed = max(speed_trap)
                    else:
                        maior_speed = speed_trap if isinstance(speed_trap, (int, float)) else 0
                    
                    # 1. Insere ou atualiza piloto
                    cursor.execute('''
                    INSERT OR REPLACE INTO pilotos (sessao_id, nome, numero, posicao)
                    VALUES (?, ?, ?, ?)
                    ''', (sessao_id_atual, nome, num, getattr(j, 'position', 0)))
                    
                    # Pega o ID do piloto
                    cursor.execute('SELECT id FROM pilotos WHERE sessao_id = ? AND nome = ?',
                                  (sessao_id_atual, nome))
                    piloto_id = cursor.fetchone()[0]
                    
                    # 2. Salva voltas
                    for volta in todas_voltas:
                        cursor.execute('''
                        INSERT OR REPLACE INTO voltas (sessao_id, piloto_id, numero_volta, tempo_volta, setor1, setor2, setor3)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            sessao_id_atual, piloto_id,
                            volta.get('volta', 0),
                            volta.get('tempo_total', 0),
                            volta.get('setor1', 0),
                            volta.get('setor2', 0),
                            volta.get('setor3', 0)
                        ))
                    
                    # 3. Salva dados de pneus
                    tyre_wear = getattr(j, 'tyre_wear', [0, 0, 0, 0])
                    temp_inner = getattr(j, 'tyres_temp_inner', [0, 0, 0, 0])
                    temp_surface = getattr(j, 'tyres_temp_surface', [0, 0, 0, 0])
                    
                    cursor.execute('''
                    INSERT INTO pneus (sessao_id, piloto_id, tipo_pneu, idade_voltas,
                                     desgaste_RL, desgaste_RR, desgaste_FL, desgaste_FR,
                                     temp_interna_RL, temp_interna_RR, temp_interna_FL, temp_interna_FR,
                                     temp_superficie_RL, temp_superficie_RR, temp_superficie_FL, temp_superficie_FR,
                                     vida_util, tyre_set_data, lap_delta_time, pit_stops)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sessao_id_atual, piloto_id,
                        tyres_nomes.get(getattr(j, 'tyres', 0), 'Desconhecido'),
                        getattr(j, 'tyresAgeLaps', 0),
                        tyre_wear[0], tyre_wear[1], tyre_wear[2], tyre_wear[3],
                        temp_inner[0], temp_inner[1], temp_inner[2], temp_inner[3],
                        temp_surface[0], temp_surface[1], temp_surface[2], temp_surface[3],
                        getattr(j, 'tyre_life', 100),
                        getattr(j, 'tyre_set_data', 0),
                        getattr(j, 'm_lap_delta_time', 0),
                        pit_quant[nome]
                    ))
                    
                    # 4. Salva danos
                    cursor.execute('''
                    INSERT INTO danos (sessao_id, piloto_id, delta_to_leader, combustivel_restante,
                                     dano_asa_esquerda, dano_asa_direita, dano_asa_traseira,
                                     dano_assoalho, dano_difusor, dano_sidepods)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sessao_id_atual, piloto_id, str(delta), Gas,
                        getattr(j, 'FrontLeftWingDamage', 0),
                        getattr(j, 'FrontRightWingDamage', 0),
                        getattr(j, 'rearWingDamage', 0),
                        getattr(j, 'floorDamage', 0),
                        getattr(j, 'diffuserDamage', 0),
                        getattr(j, 'sidepodDamage', 0)
                    ))
                    
                    # 5. Salva telemetria
                    cursor.execute('''
                    INSERT INTO telemetria (sessao_id, piloto_id, velocidade)
                    VALUES (?, ?, ?)
                    ''', (sessao_id_atual, piloto_id, maior_speed))
                
                    # 6. Salva stints de pneus
                    stints = getattr(j, 'pneu_stints', [])
                    for stint in stints:
                        cursor.execute('''
                        INSERT OR REPLACE INTO pneu_stints 
                        (sessao_id, piloto_id, stint_numero, tipo_pneu, composto_real, 
                         volta_inicio, volta_fim, total_voltas)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            sessao_id_atual, piloto_id,
                            stint['stint_numero'],
                            stint['tipo_pneu'],
                            stint['composto_real'],
                            stint['volta_inicio'],
                            stint['volta_fim'],
                            stint['total_voltas']
                        ))
                
                except Exception as e:
                    print(f"❌ Erro ao salvar piloto {nome}: {e}")
                    continue
            
            # ✅ Commit APÓS processar todos os pilotos
            conn.commit()
            conn.close()
            
            await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"❌ Erro crítico no salvamento: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(2)
            continue
    
    
    await mensagem.edit(content=f"🏁 Salvamento finalizado! Sessão #{sessao_id_atual}")
@bot.command()
async def parar_salvar(ctx):#pronto
    global TEMPO_INICIO_VOLTAS
    TEMPO_INICIO_VOLTAS = False
    await ctx.send("🛑 Envio automático de voltas parado.")
@bot.command()
async def delta(ctx):
    await comando_delta(ctx)
@bot.command()
async def pneusv(ctx,*, piloto: str = None):
    await comando_pneusv(ctx, piloto=piloto)
@bot.command()
async def clima(ctx):#pronto
    await comando_clima(ctx)
@bot.command()
async def pilotos(ctx):
    await commando_piloto(ctx)
@bot.command()
async def danos(ctx, piloto: str = None):
    await comandos_danos(ctx, piloto=piloto)

@bot.command()
async def media_lap(ctx):
  await comando_media(ctx)
def salvar_sessao_no_banco(pacote_session):
    import sqlite3
    
    track_id = pacote_session.m_track_id
    nome_pista = SESSION.get_track_name(track_id)
    total_laps = pacote_session.m_total_laps
    clima = pacote_session.m_weather
    
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO sessoes (nome_pista, total_voltas, clima, temperatura_ar, temperatura_pista)
    VALUES (?, ?, ?, ?, ?)
    ''', (nome_pista, total_laps, clima, pacote_session.m_air_temperature, pacote_session.m_track_temperature))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Sessão salva: {nome_pista} ({total_laps} voltas)")
def criar_tabela_regras():
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS regras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo TEXT,
        conteudo TEXT,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Executa ao iniciar
criar_tabela_regras()
def criar_tabela_clips():
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo TEXT,
        tamanho_bytes INTEGER,
        duracao_segundos REAL,
        resolucao TEXT,
        formato TEXT,
        caminho_arquivo TEXT,
        analise_ia TEXT,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Executa ao iniciar
criar_tabela_clips()
def criar_tabelas():
    """Cria todas as tabelas necessárias no banco"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Tabela de sessões
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_pista TEXT,
        tipo_sessao TEXT,
        total_voltas INTEGER,
        clima TEXT,
        temperatura_ar REAL,
        temperatura_pista REAL,
        porcentagem_chuva REAL,
        safety_car_status TEXT,
        flag TEXT,
        velocidade_maxima_geral REAL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabela de pilotos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pilotos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        nome TEXT,
        numero INTEGER,
        posicao INTEGER,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        UNIQUE(sessao_id, nome)
    )
    ''')
    
    # Tabela de voltas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voltas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        numero_volta INTEGER,
        tempo_volta REAL,
        setor1 REAL,
        setor2 REAL,
        setor3 REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id),
        UNIQUE(sessao_id, piloto_id, numero_volta)
    )
    ''')
    
    # Tabela de pneus
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pneus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        tipo_pneu TEXT,
        idade_voltas INTEGER,
        desgaste_RL REAL,
        desgaste_RR REAL,
        desgaste_FL REAL,
        desgaste_FR REAL,
        temp_interna_RL REAL,
        temp_interna_RR REAL,
        temp_interna_FL REAL,
        temp_interna_FR REAL,
        temp_superficie_RL REAL,
        temp_superficie_RR REAL,
        temp_superficie_FL REAL,
        temp_superficie_FR REAL,
        vida_util REAL,
        tyre_set_data INTEGER,
        lap_delta_time REAL,
        pit_stops INTEGER,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de danos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS danos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        delta_to_leader TEXT,
        combustivel_restante REAL,
        dano_asa_esquerda REAL,
        dano_asa_direita REAL,
        dano_asa_traseira REAL,
        dano_assoalho REAL,
        dano_difusor REAL,
        dano_sidepods REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de telemetria
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        velocidade REAL,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id)
    )
    ''')
    
    # Tabela de estágios de pneus
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pneu_stints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        piloto_id INTEGER,
        stint_numero INTEGER,
        tipo_pneu TEXT,
        composto_real INTEGER,  # ← ERA TEXT, CORRIJA PARA INTEGER
        volta_inicio INTEGER,
        volta_fim INTEGER,
        total_voltas INTEGER,
        FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
        FOREIGN KEY (piloto_id) REFERENCES pilotos(id),
        UNIQUE(sessao_id, piloto_id, stint_numero)
    )
    ''')
    
    conn.commit()
    conn.close()

# Executa ao iniciar
criar_tabelas()
criar_tabela_regras()
criar_tabela_clips()
@bot.command()
async def historico(ctx):
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, nome_pista, tipo_sessao, total_voltas, data_hora
    FROM sessoes
    ORDER BY data_hora DESC
    LIMIT 10
    ''')
    
    sessoes = cursor.fetchall()
    conn.close()
    
    if not sessoes:
        await ctx.send("❌ Nenhuma sessão registrada.")
        return
    
    texto = "🏁 **Últimas 10 Sessões:**\n"
    for id, pista, tipo, voltas, data in sessoes:
        texto += f"#{id} - {pista} | {tipo} | {voltas} voltas | {data}\n"
    
    await ctx.send(texto)

@bot.command()
async def ver_clips(ctx):
    """Lista todos os clips salvos no banco"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, nome_arquivo, tamanho_bytes, duracao_segundos, resolucao, data_upload
    FROM clips
    ORDER BY data_upload DESC
    LIMIT 10
    ''')
    
    clips = cursor.fetchall()
    conn.close()
    
    if not clips:
        await ctx.send("❌ Nenhum clip encontrado no banco.")
        return
    
    texto = "🎬 **Clips Salvos:**\n"
    for id, nome, tamanho, duracao, resolucao, data in clips:
        tamanho_mb = tamanho / (1024 * 1024)
        duracao_str = f"{int(duracao // 60)}:{int(duracao % 60):02d}" if duracao > 0 else "N/A"
        texto += (f"#{id} - `{nome}` | {tamanho_mb:.1f}MB | "
                 f"{duracao_str} | {resolucao} | {data}\n")
    
    texto += "\n💡 Use `.info_clip <ID>` para ver detalhes"
    await ctx.send(texto)
@bot.command()
async def clip(ctx):
    if not ctx.message.attachments:
        await ctx.send("🎞️ Envie o vídeo junto com o comando `.clip`!")
        return

    arquivo = ctx.message.attachments[0]
    
    # Verifica se é vídeo
    extensoes_video = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']
    if not any(arquivo.filename.lower().endswith(ext) for ext in extensoes_video):
        await ctx.send("❌ Por favor, envie apenas arquivos de vídeo (MP4, MOV, AVI, etc).")
        return
    
    # Cria pasta se não existir
    os.makedirs("clips", exist_ok=True)
    caminho = f"clips/{arquivo.filename}"
    
    await ctx.send(f"📥 Baixando vídeo `{arquivo.filename}`...")
    await arquivo.save(caminho)
    
    # Extrai metadados do vídeo (usando ffprobe se disponível)
    try:
        import subprocess
        resultado = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration,size:stream=width,height', 
             '-of', 'json', caminho],
            capture_output=True,
            text=True
        )
        
        if resultado.returncode == 0:
            import json
            info = json.loads(resultado.stdout)
            duracao = float(info.get('format', {}).get('duration', 0))
            tamanho = int(info.get('format', {}).get('size', 0))
            
            streams = info.get('streams', [])
            resolucao = "Desconhecida"
            if streams:
                width = streams[0].get('width', 0)
                height = streams[0].get('height', 0)
                resolucao = f"{width}x{height}" if width and height else "Desconhecida"
        else:
            # Fallback: usa tamanho do arquivo
            duracao = 0
            tamanho = os.path.getsize(caminho)
            resolucao = "Desconhecida"
    except Exception:
        # Se ffprobe não estiver disponível
        duracao = 0
        tamanho = os.path.getsize(caminho)
        resolucao = "Desconhecida"
    
    formato = os.path.splitext(arquivo.filename)[1].lstrip('.')
    
    # Salva no banco de dados
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO clips (nome_arquivo, tamanho_bytes, duracao_segundos, 
                      resolucao, formato, caminho_arquivo, analise_ia)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (arquivo.filename, tamanho, duracao, resolucao, formato, caminho, 
          "⚙️ Análise pendente"))
    
    clip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Formata informações
    tamanho_mb = tamanho / (1024 * 1024)
    duracao_str = f"{int(duracao // 60)}:{int(duracao % 60):02d}" if duracao > 0 else "N/A"
    
    await ctx.send(
        f"✅ Vídeo salvo no banco de dados! (ID: {clip_id})\n"
        f"📄 Arquivo: `{arquivo.filename}`\n"
        f"📊 Tamanho: {tamanho_mb:.2f} MB\n"
        f"⏱️ Duração: {duracao_str}\n"
        f"📐 Resolução: {resolucao}\n"
        f"🔍 Formato: {formato.upper()}\n"
        f"💡 Use `.ver_clips` para listar todos os vídeos salvos"
    )
@bot.command()
async def regras(ctx):
    if not ctx.message.attachments:
        await ctx.send("📄 Envie o PDF das regras junto com o comando `.regras`")
        return

    arquivo = ctx.message.attachments[0]
    
    # Verifica se é PDF
    if not arquivo.filename.lower().endswith('.pdf'):
        await ctx.send("❌ Por favor, envie apenas arquivos PDF.")
        return
    
    # Salva temporariamente
    caminho_temp = f"temp_{arquivo.filename}"
    await arquivo.save(caminho_temp)

    try:
        # Extrai texto do PDF
        with open(caminho_temp, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            texto = " ".join([page.extract_text() for page in reader.pages])

        # Salva no banco de dados
        conn = sqlite3.connect('f1_telemetry.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO regras (nome_arquivo, conteudo)
        VALUES (?, ?)
        ''', (arquivo.filename, texto))
        
        regra_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Remove arquivo temporário
        os.remove(caminho_temp)

        await ctx.send(f"✅ Regras salvas no banco de dados! (ID: {regra_id})\n"
                      f"📄 Arquivo: `{arquivo.filename}`\n"
                      f"📊 Total de caracteres: {len(texto)}")

    except Exception as e:
        await ctx.send(f"❌ Erro ao processar PDF: {e}")
        if os.path.exists(caminho_temp):
            os.remove(caminho_temp)
@bot.command()
async def deletar_regra(ctx, regra_id: int):
    """Deleta uma regra do banco"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Verifica se existe
    cursor.execute('SELECT nome_arquivo FROM regras WHERE id = ?', (regra_id,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        await ctx.send(f"❌ Regra #{regra_id} não encontrada.")
        return
    
    nome = resultado[0]
    
    # Deleta
    cursor.execute('DELETE FROM regras WHERE id = ?', (regra_id,))
    conn.commit()
    conn.close()
    
    await ctx.send(f"🗑️ Regra #{regra_id} (`{nome}`) deletada com sucesso!")
@bot.command()
async def deletar_clip(ctx, clip_id: int):
    """Deleta um clip do banco e do disco"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    # Verifica se existe
    cursor.execute('SELECT nome_arquivo, caminho_arquivo FROM clips WHERE id = ?', (clip_id,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        await ctx.send(f"❌ Clip #{clip_id} não encontrado.")
        return
    
    nome, caminho = resultado
    
    # Deleta do banco
    cursor.execute('DELETE FROM clips WHERE id = ?', (clip_id,))
    conn.commit()
    conn.close()
    
    # Deleta arquivo do disco
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            await ctx.send(f"🗑️ Clip #{clip_id} (`{nome}`) deletado do banco e do disco!")
        else:
            await ctx.send(f"🗑️ Clip #{clip_id} (`{nome}`) deletado do banco (arquivo não encontrado no disco).")
    except Exception as e:
        await ctx.send(f"⚠️ Clip deletado do banco, mas erro ao deletar arquivo: {e}")

@bot.command()
async def info_clip(ctx, clip_id: int):
    """Mostra informações detalhadas de um clip"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT nome_arquivo, tamanho_bytes, duracao_segundos, resolucao, 
           formato, caminho_arquivo, analise_ia, data_upload
    FROM clips
    WHERE id = ?
    ''', (clip_id,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if not resultado:
        await ctx.send(f"❌ Clip #{clip_id} não encontrado.")
        return
    
    nome, tamanho, duracao, resolucao, formato, caminho, analise, data = resultado
    
    tamanho_mb = tamanho / (1024 * 1024)
    duracao_str = f"{int(duracao // 60)}:{int(duracao % 60):02d}" if duracao > 0 else "N/A"
    
    embed = discord.Embed(
        title=f"🎬 Clip #{clip_id}",
        description=f"**{nome}**",
        color=discord.Color.red()
    )
    embed.add_field(name="📊 Tamanho", value=f"{tamanho_mb:.2f} MB", inline=True)
    embed.add_field(name="⏱️ Duração", value=duracao_str, inline=True)
    embed.add_field(name="📐 Resolução", value=resolucao, inline=True)
    embed.add_field(name="🔍 Formato", value=formato.upper(), inline=True)
    embed.add_field(name="📅 Upload", value=data, inline=True)
    embed.add_field(name="📂 Caminho", value=f"`{caminho}`", inline=False)
    embed.add_field(name="🤖 Análise IA", value=analise, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def ver_regras(ctx):
    """Mostra a lista de regras salvas no banco"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, nome_arquivo, data_upload
    FROM regras
    ORDER BY data_upload DESC
    LIMIT 10
    ''')
    
    regras = cursor.fetchall()
    conn.close()
    
    if not regras:
        await ctx.send("❌ Nenhuma regra encontrada no banco.")
        return
    
    texto = "📚 **Regras Salvas:**\n"
    for id, nome, data in regras:
        texto += f"#{id} - `{nome}` | Upload: {data}\n"
    
    texto += "\n💡 Use `.ler_regra <ID>` para ver o conteúdo"
    await ctx.send(texto)

@bot.command()
async def ler_regra(ctx, regra_id: int):
    """Mostra o conteúdo de uma regra por ID"""
    conn = sqlite3.connect('f1_telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT nome_arquivo, conteudo, data_upload
    FROM regras
    WHERE id = ?
    ''', (regra_id,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if not resultado:
        await ctx.send(f"❌ Regra #{regra_id} não encontrada.")
        return
    
    nome, conteudo, data = resultado
    
    # Discord tem limite de 2000 caracteres
    if len(conteudo) > 1900:
        await ctx.send(f"📄 **{nome}** (Upload: {data})\n\n```{conteudo[:1900]}...```\n⚠️ Conteúdo muito longo (mostrados primeiros 1900 caracteres)")
    else:
        await ctx.send(f"📄 **{nome}** (Upload: {data})\n\n```{conteudo}```")
#coisa HTTP e html pra baixo
_cloudflared_proc = None
url = None

def _start_cloudflared(port=5000, cloudflared_path="cloudflared"):
    """Inicia cloudflared e retorna o objeto subprocess e o public_url lido da saída."""
    global _cloudflared_proc

    # Verifica se o executável está acessível
    if not shutil.which(cloudflared_path):
        raise FileNotFoundError(f"cloudflared não encontrado em: {cloudflared_path}")

    cmd = [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"]
    _cloudflared_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    public = None
    logs = []
    start = time.time()
    url_regex = r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com"

    while True:
        if _cloudflared_proc.stdout is None:
            break
        line = _cloudflared_proc.stdout.readline()
        if line:
            logs.append(line)
            print("[cloudflared]", line.strip())
            match = re.search(url_regex, line)
            if match:
                public = match.group(0)
                break

        if public or (time.time() - start) > 10:
            break

    if not public:
        print("⚠️ Não detectei o URL público automaticamente. Verifique manualmente o output do cloudflared acima.")
        print("🔍 Logs completos:")
        print("".join(logs))

    return _cloudflared_proc, public

def _stop_cloudflared():
    global _cloudflared_proc
    try:
        if _cloudflared_proc:
            print("Encerrando cloudflared...")
            _cloudflared_proc.terminate()
            try:
                _cloudflared_proc.wait(timeout=3)
            except Exception:
                _cloudflared_proc.kill()
    except Exception as e:
        print("Erro ao encerrar cloudflared:", e)
    finally:
        _cloudflared_proc = None

def iniciar_painel_e_cloudflared():
    from painel.app import app
    global url

    cloudflared_path = "cloudflared"  # ou caminho absoluto

    try:
        proc, url = _start_cloudflared(port=5000, cloudflared_path=cloudflared_path)
        if url:
            print(f"✅ Tunnel criado: {url}")
        else:
            print("⚠️ Não foi possível detectar URL do cloudflared automaticamente.")
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
    except Exception as e:
        print("❌ Erro ao iniciar painel/cloudflared:", e)
    finally:
        _stop_cloudflared()

# Comandos do bot
@bot.command()
async def painel(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel disponível em: {url}")

@bot.command()
async def pneusp(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel dos pneus disponível em: {url}/pnues")
@bot.command()
async def grafico_web(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel disponível em: {url}/graf")
@bot.command()
async def media_HD(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel disponível em: {url}/g")
@bot.command()
async def pit_stop(ctx):
    if not url:
        await ctx.send("❌ O painel ainda não está disponível. Tente novamente em alguns segundos.")
        return
    await ctx.send(f"🔗 Painel disponível em: {url}/pit")
if __name__ == "__main__":
    import threading
    from Bot.parser2024 import start_udp_listener
    threading.Thread(target=start_udp_listener, daemon=True).start()
    threading.Thread(target=iniciar_painel_e_cloudflared, daemon=True).start()    

 #python Bot/bot_discord.py pra ativar

