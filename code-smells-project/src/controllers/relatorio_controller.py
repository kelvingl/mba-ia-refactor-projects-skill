from src.models import relatorio_model

_DISCOUNT_TIERS = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)


def relatorio_vendas() -> dict:
    dados = relatorio_model.dados_vendas()
    faturamento = dados["faturamento"]
    por_status = dados["por_status"]

    desconto = 0.0
    for limite, taxa in _DISCOUNT_TIERS:
        if faturamento > limite:
            desconto = faturamento * taxa
            break

    total_pedidos = dados["total_pedidos"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get("pendente", 0),
        "pedidos_aprovados": por_status.get("aprovado", 0),
        "pedidos_cancelados": por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
