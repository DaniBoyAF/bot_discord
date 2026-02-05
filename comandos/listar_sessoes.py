import sqlite3

async def listar_sessoe(ctx, limit: int = 10):
    """Lista sessões recentes com id para uso no comando .media <id>"""
    conn = sqlite3.connect("f1_telemetry.db")
    cursor = conn.cursor()
    
    # ← CORRIGE: coluna é "data_hora", não "created_at"
    cursor.execute("""
        SELECT id, nome_pista, tipo_sessao, data_hora 
        FROM sessoes 
        ORDER BY id DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await ctx.send("Nenhuma sessão encontrada.")
        return
    
    linhas = ["**Sessões recentes:**", "```"]
    linhas.append("ID  | Pista            | Tipo        | Data")
    linhas.append("-" * 55)
    for r in rows:
        linhas.append(f"{r[0]:<3} | {(r[1] or 'Unknown')[:16]:<16} | {(r[2] or '??')[:10]:<10} | {r[3] or '??'}")
    linhas.append("```")
    
    await ctx.send("\n".join(linhas))