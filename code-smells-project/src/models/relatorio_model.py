from src.models.database import get_db


def dados_vendas():
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos").fetchone()[0]
    por_status = {
        row["status"]: row["count"]
        for row in db.execute(
            "SELECT status, COUNT(*) AS count FROM pedidos GROUP BY status"
        ).fetchall()
    }
    return {
        "total_pedidos": total_pedidos,
        "faturamento": float(faturamento),
        "por_status": por_status,
    }
