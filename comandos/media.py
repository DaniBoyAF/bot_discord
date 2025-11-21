import sqlite3

async def comando_media(ctx, sessao_id: int | None):
    """Exibe médias de voltas para uma sessão.
    Uso: .media            -> usa última sessão
         .media <sessao_id> -> usa sessão específica
    """
    conn = sqlite3.connect("f1_telemetry.db")
    cursor = conn.cursor()

    # se não recebeu sessao_id, pega a última
    if sessao_id is None:
        cursor.execute("SELECT id, nome_pista FROM sessoes ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            await ctx.send("Nenhuma sessão encontrada no banco.")
            conn.close()
            return
        sessao_id = row[0]
        sessao_nome = row[1] if len(row) > 1 else f"#{sessao_id}"
    else:
        # valida se a sessão existe
        cursor.execute("SELECT id, nome_pista FROM sessoes WHERE id = ?", (sessao_id,))
        row = cursor.fetchone()
        if not row:
            await ctx.send(f"Sessão #{sessao_id} não encontrada.")
            conn.close()
            return
        sessao_nome = row[1] if len(row) > 1 else f"#{sessao_id}"

    cursor.execute("""
        SELECT p.nome, v.tempo_volta, v.setor1, v.setor2, v.setor3
        FROM voltas v
        JOIN pilotos p ON p.id = v.piloto_id
        WHERE v.sessao_id = ? AND v.tempo_volta > 0
    """, (sessao_id,))
    tempos = {}
    for nome, total, s1, s2, s3 in cursor.fetchall():
        try:
            s1f = None if s1 is None else float(s1)
            s2f = None if s2 is None else float(s2)
            s3f = None if s3 is None else float(s3)
            if s1f is None or s2f is None or s3f is None:
                continue
            if s1f <= 0 or s2f <= 0 or s3f <= 0:
                continue
            totalf = float(total)
        except Exception:
            continue
        tempos.setdefault(nome, []).append(totalf)
    conn.close()

    if not tempos:
        await ctx.send(f"Nenhum dado de média encontrado para a sessão {sessao_nome} (id={sessao_id}).")
        return

    medias = {n: sum(ts)/len(ts) for n, ts in tempos.items()}
    medias_ordenadas = sorted(medias.items(), key=lambda x: x[1])
    melhor = medias_ordenadas[0][1]
    linhas = [f"Médias — Sessão: {sessao_nome} (id={sessao_id})", "---------------------------------"]
    for idx, (nome, media) in enumerate(medias_ordenadas, 1):
        label = "Quickest" if idx == 1 else f"+{media - melhor:.2f} s/lap"
        linhas.append(f"{idx}) {nome:<15} {label}")
    await ctx.send("```\n" + "\n".join(linhas) + "\n```")