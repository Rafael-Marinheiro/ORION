from rest_framework import serializers

from .models import (
    AplicacaoFinanceiraGrupo,
    AuditoriaSubmissaoRodada,
    CapacidadeProdutoGrupo,
    CEOGrupoRodada,
    Cidade,
    ConsolidadoRodadaGrupo,
    DemandaCidadeProduto,
    CompraMateriaPrima,
    ComposicaoProduto,
    Decisao,
    Distribuicao,
    EstoqueProduto,
    EstoqueMateriaPrima,
    Evento,
    EventoRodada,
    ExecucaoJob,
    GameConfig,
    Grupo,
    IndicadorRodadaGrupo,
    Investimento,
    Jogo,
    Mercado,
    MarketShareCidadeProduto,
    MateriaPrima,
    Producao,
    Produto,
    ResultadoFinanceiro,
    Rodada,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo.membros.field.model
        fields = ["id_usuario", "nome_usuario", "email_usuario", "tipo_usuario", "status_usuario"]


class GrupoSerializer(serializers.ModelSerializer):
    jogo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Grupo
        fields = [
            "id",
            "nome",
            "capital",
            "estoque",
            "materia_prima",
            "jogo",
            "total_lucro",
            "market_share_medio",
            "saldo_caixa_final",
            "total_penalidades",
        ]


class ResultadoFinanceiroSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField()
    custo_envio = serializers.DecimalField(
        source="custo_envio_total", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = ResultadoFinanceiro
        fields = ["grupo", "rodada", "receita", "custos", "lucro", "saldo_caixa"]


class DecisaoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Decisao
        fields = "__all__"


class DistribuicaoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    cidade = serializers.StringRelatedField()
    produto = serializers.StringRelatedField()

    class Meta:
        model = Distribuicao
        fields = "__all__"


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = "__all__"


class EventoRodadaSerializer(serializers.ModelSerializer):
    evento = serializers.StringRelatedField()

    class Meta:
        model = EventoRodada
        fields = "__all__"


class RodadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rodada
        fields = "__all__"


class CidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cidade
        fields = "__all__"


class MercadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mercado
        fields = "__all__"


class GameConfigSerializer(serializers.ModelSerializer):
    produtos_habilitados = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    regra_eventos = serializers.JSONField(required=False)

    class Meta:
        model = GameConfig
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["produtos_habilitados"] = (
            instance.produtos_habilitados.split(",")
            if instance.produtos_habilitados
            else []
        )
        return rep

    def create(self, validated_data):
        produtos = validated_data.pop("produtos_habilitados", [])
        validated_data["produtos_habilitados"] = ",".join(produtos)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        produtos = validated_data.pop("produtos_habilitados", None)
        if produtos is not None:
            validated_data["produtos_habilitados"] = ",".join(produtos)
        return super().update(instance, validated_data)


class JogoSerializer(serializers.ModelSerializer):
    config = serializers.StringRelatedField()

    class Meta:
        model = Jogo
        fields = "__all__"


class InvestimentoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField()
    cidade = serializers.StringRelatedField()

    class Meta:
        model = Investimento
        fields = "__all__"


class MateriaPrimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriaPrima
        fields = "__all__"


class ProdutoSerializer(serializers.ModelSerializer):
    custo_unitario_estimado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Produto
        fields = "__all__"


class ComposicaoProdutoSerializer(serializers.ModelSerializer):
    produto = serializers.StringRelatedField(read_only=True)
    materia_prima = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ComposicaoProduto
        fields = "__all__"


class ProducaoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    produto = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Producao
        fields = "__all__"


class EstoqueMateriaPrimaSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    materia_prima = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = EstoqueMateriaPrima
        fields = "__all__"


class CompraMateriaPrimaSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    materia_prima = serializers.StringRelatedField(read_only=True)
    cidade_fornecedora = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CompraMateriaPrima
        fields = "__all__"


class EstoqueProdutoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    produto = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = EstoqueProduto
        fields = "__all__"


class MarketShareCidadeProdutoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    cidade = serializers.StringRelatedField(read_only=True)
    produto = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = MarketShareCidadeProduto
        fields = "__all__"


class IndicadorRodadaGrupoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = IndicadorRodadaGrupo
        fields = "__all__"


class CapacidadeProdutoGrupoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    produto = serializers.StringRelatedField(read_only=True)
    capacidade_unidades_rodada = serializers.IntegerField(read_only=True)

    class Meta:
        model = CapacidadeProdutoGrupo
        fields = "__all__"


class ConsolidadoRodadaGrupoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ConsolidadoRodadaGrupo
        fields = "__all__"


class CEOGrupoRodadaSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CEOGrupoRodada
        fields = "__all__"


class AuditoriaSubmissaoRodadaSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)
    decisao = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AuditoriaSubmissaoRodada
        fields = "__all__"


class DemandaCidadeProdutoSerializer(serializers.ModelSerializer):
    cidade = serializers.StringRelatedField(read_only=True)
    produto = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = DemandaCidadeProduto
        fields = "__all__"


class AplicacaoFinanceiraGrupoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AplicacaoFinanceiraGrupo
        fields = "__all__"


class ExecucaoJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecucaoJob
        fields = "__all__"
