import sqlite3

async def comando_media(ctx):
    conn = sqlite3.connect("f1_telemetry.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sessoes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        await ctx.send("Nenhuma sessão encontrada no banco.")
        conn.close()
        return
    sessao_id = row[0]

    cursor.execute("""
        SELECT p.nome, v.tempo_volta, v.setor1, v.setor2, v.setor3
        FROM voltas v
        JOIN pilotos p ON p.id = v.piloto_id
        WHERE v.sessao_id = ? AND v.tempo_volta > 0
    """, (sessao_id,))
    tempos = {}
    for nome, total, s1, s2, s3 in cursor.fetchall():
        if min(s1, s2, s3) <= 0:
            continue
        tempos.setdefault(nome, []).append(total)
    conn.close()

    if not tempos:
        await ctx.send("Nenhum dado de média encontrado.")
        return

    medias = {n: sum(ts)/len(ts) for n, ts in tempos.items()}
    medias_ordenadas = sorted(medias.items(), key=lambda x: x[1])
    melhor = medias_ordenadas[0][1]
    linhas = []
    for idx, (nome, media) in enumerate(medias_ordenadas, 1):
        label = "Quickest" if idx == 1 else f"+{media - melhor:.2f} s/lap"
        linhas.append(f"{idx}) {nome:<15} {label}")
    await ctx.send("```\n" + "\n".join(linhas) + "\n```")