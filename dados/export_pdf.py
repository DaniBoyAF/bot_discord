from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def export_pdf_corrida_final(filepath, jogadores, session):
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
    c.drawString(40, y, f"Tipo: {session.Seance} | Voltas: {session.currentLap}/{session.nbLaps}")
    y -= 15
    c.drawString(40, y, f"Clima: {session.weather} | Ar: {session.airTemperature}°C | Pista: {session.trackTemperature}°C")
    y -= 30

    # Dados dos pilotos
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Pilotos:")
    y -= 20
    c.setFont("Helvetica", 10)

    jogadores_ordenados = sorted(jogadores, key=lambda x: x.position)
    vencedor = jogadores_ordenados[0]

    for j in jogadores_ordenados:
        estrela = "⭐" if j == vencedor else ""
        linha = f"{j.position}º {j.name} {estrela} | Melhor Volta: {j.bestLapTime:.3f}s | Última: {j.lastLapTime:.3f}s | Pneus: {j.tyresAgeLaps} | ERS: {j.ERS_pourcentage}%"
        c.drawString(40, y, linha)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 40
            y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "📊 Estatísticas:")
        y -= 20
        c.setFont("Helvetica", 10)

    # Quem mais fez pitstops
        max_pits = max(jogadores, key=lambda j: j.pit)
        c.drawString(40, y, f"🔧 Mais pitstops: {max_pits.name} ({max_pits.pit} vezes)")
        y -= 15

    # Quem teve a melhor volta
        melhor_volta = min(jogadores, key=lambda j: j.bestLapTime if j.bestLapTime > 0 else float('inf'))
        c.drawString(40, y, f"🏁 Melhor volta: {melhor_volta.name} ({melhor_volta.bestLapTime:.3f}s)")
        y -= 15


    # Gráfico de tempos por volta
    if os.path.exists("grafico_tempos.png"):
        c.showPage()
        c.drawImage("grafico_tempos.png", 50, 250, width=500, height=300)

    # Salvar PDF
    c.save()
    print(f"✅ PDF salvo em: {filepath}")