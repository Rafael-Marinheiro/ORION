from rest_framework import serializers
from .models import Grupo, ResultadoFinanceiro

class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = ["id", "nome", "capital", "estoque"]

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

