from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def export_pdf_corrida_final(filepath, jogadores, session):
    from Bot.jogadores import get_jogadores
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 40  # posição vertical inicial

    # Título
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "🏁 Relatório Final da Corrida")
    y -= 30

    # Sessão
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Informações da Sessão:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Tipo: {getattr(session, 'm_session_type', '?')} | Voltas: {getattr(session, 'm_total_laps', '?')}")
    y -= 15
    c.drawString(40, y, f"Clima: {session.m_weather} | Ar: {session.m_air_temperature}°C | Pista: {session.m_track_temperature}°C")
    y -= 30

    # Dados dos pilotos
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Pilotos:")
    y -= 20
    c.setFont("Helvetica", 10)

    jogadores_ordenados = sorted(jogadores, key=lambda x: x.position)
    vencedor = jogadores_ordenados[0]
    # Quem mais fez pitstops
    max_pits = max(jogadores, key=lambda j: j.pit)
    nome_max_pits = getattr(max_pits, "nome", getattr(max_pits, "name", "Desconhecido"))
    c.drawString(40, y, f"🔧 Mais pitstops: {nome_max_pits} ({max_pits.pit} vezes)")
    y -= 15

    # Quem teve a melhor volta
    melhor_volta = min(jogadores, key=lambda j: j.bestLapTime if j.bestLapTime > 0 else float('inf'))
    nome_melhor_volta = getattr(melhor_volta, "nome", getattr(melhor_volta, "name", "Desconhecido"))
    c.drawString(40, y, f"🏁 Melhor volta: {nome_melhor_volta} ({melhor_volta.bestLapTime:.3f}s)")
    y -= 15

    # Lista dos pilotos
    for j in jogadores_ordenados:
        nome = getattr(j, "nome", getattr(j, "name", "Desconhecido"))
        estrela = "⭐" if j == vencedor else ""
        linha = f"{j.position}º {nome} {estrela} | Melhor Volta: {j.bestLapTime:.3f}s | Última: {j.lastLapTime:.3f}s | Pneus: {j.tyresAgeLaps} |"
        c.drawString(40, y, linha)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 40

    # Gráfico
    if os.path.exists("grafico_corrida.png"):
        c.showPage()
        c.drawImage("grafico_corrida.png", 50, 250, width=500, height=300)

    c.save()
