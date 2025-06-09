from rest_framework import serializers
from .models import (
    Grupo,
    Decisao,
    Distribuicao,
    ResultadoFinanceiro,
    Evento,
    EventoRodada,
    Rodada,
    Cidade,
    GameConfig,
    Jogo,
    Investimento,
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo.membros.field.model  # User model
        fields = ["id_usuario", "nome_usuario", "email_usuario", "tipo_usuario", "status_usuario"]

class GrupoSerializer(serializers.ModelSerializer):
    jogo = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Grupo
        fields = ["id", "nome", "capital", "estoque", "jogo"]

class ResultadoFinanceiroSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField()

    class Meta:
        model = ResultadoFinanceiro
        fields = [
            "grupo",
            "rodada",
            "receita",
            "custos",
            "lucro",
            "saldo_caixa",
        ]


class DecisaoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Decisao
        fields = "__all__"


class DistribuicaoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField(read_only=True)
    cidade = serializers.StringRelatedField()

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


class GameConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameConfig
        fields = "__all__"


class JogoSerializer(serializers.ModelSerializer):
    config = serializers.StringRelatedField()

    class Meta:
        model = Jogo
        fields = "__all__"


class InvestimentoSerializer(serializers.ModelSerializer):
    grupo = serializers.StringRelatedField()

    class Meta:
        model = Investimento
        fields = "__all__"

