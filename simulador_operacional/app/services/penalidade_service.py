from decimal import Decimal

from ..models import Grupo, ResultadoFinanceiro


def aplicar_penalidade(grupo: Grupo, rodada: int, valor: Decimal) -> None:
    """Aplica penalidade financeira ao grupo e registra no resultado."""
    if valor <= 0:
        return
    grupo.capital -= valor
    grupo.save(update_fields=["capital"])
    rf, _ = ResultadoFinanceiro.objects.get_or_create(grupo=grupo, rodada=rodada)
    rf.custos += valor
    rf.penalidades += valor
    rf.saldo_caixa = grupo.capital
    rf.lucro = rf.receita - rf.custos
    rf.save(update_fields=["custos", "penalidades", "saldo_caixa", "lucro"])
