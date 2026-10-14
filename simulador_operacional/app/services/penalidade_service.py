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


def registrou_decisao(grupo, rodada: int) -> bool:
    """11.2 -- a equipe informou alguma decisao nesta rodada?

    O 11.2 se chama "Tratamento de Decisoes Nao Informadas" e dispara
    "caso o grupo nao tenha submetido SUAS DECISOES ate o prazo-limite".
    O objeto da frase sao as decisoes, nao o formulario.

    Ate 14/10/2026 a multa olhava so a existencia da linha de submissao,
    criada pelo botao "Enviar submissao". Quem clicava sem registrar nada
    recebia o tratamento do 11.2 -- repeticao automatica dos valores da
    rodada anterior -- SEM a multa que o 11.2 impoe junto. O botao sozinho
    anulava a penalidade.

    As variaveis decisorias sao as que o 11.2 lista: "producao, compras,
    vendas, investimentos, precos". Venda e o envio, que carrega o preco.
    """
    from ..models import CompraMateriaPrima, Distribuicao, Investimento, Producao

    # Quantidade zero nao e decisao: seria a forma trivial de burlar a
    # multa -- registrar uma ordem de producao de 0 unidade e clicar em
    # enviar. O 11.2 fala em variaveis decisorias informadas, e informar
    # zero e o mesmo que nao informar.
    return (
        CompraMateriaPrima.objects.filter(
            grupo=grupo, rodada_pedido=rodada, quantidade_kg__gt=0
        ).exists()
        or Producao.objects.filter(
            grupo=grupo, rodada=rodada, quantidade_planejada__gt=0
        ).exists()
        or Distribuicao.objects.filter(
            grupo=grupo, rodada=rodada, quantidade__gt=0
        ).exists()
        or Investimento.objects.filter(
            grupo=grupo, rodada=rodada, valor__gt=0
        ).exists()
    )
