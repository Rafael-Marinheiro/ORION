"""Apaga de vez as pracas da base regional que o 9.1 substituiu.

O `seed_dados_base` aposenta essas pracas zerando a demanda, mas nao apaga
as que tem movimento: `Distribuicao.cidade` e CASCADE, entao apagar a
cidade leva junto o historico de envios, e o seed nao pode destruir dado
como efeito colateral de popular a base.

Este comando existe para o outro caso -- quando o historico e descartavel,
como o que sobrou dos ensaios anteriores. Ele NAO apaga nada sem
`--confirmar`: sem a opcao, so mostra o que sairia.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import (
    Cidade,
    CompraMateriaPrima,
    DemandaCidadeProduto,
    Distribuicao,
    Investimento,
    MarketShareCidadeProduto,
)
from app.management.commands.seed_dados_base import PRACAS_DA_BASE_REGIONAL


class Command(BaseCommand):
    help = (
        "Apaga as pracas da base regional anterior ao 9.1, com o historico "
        "que depende delas. Sem --confirmar, apenas relata."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Executa a remocao. Sem esta opcao o comando so relata.",
        )

    def handle(self, *args, **options):
        cidades = list(Cidade.objects.filter(nome__in=PRACAS_DA_BASE_REGIONAL))
        if not cidades:
            self.stdout.write("Nenhuma praça da base regional no banco.")
            return

        total = {"envios": 0, "market_share": 0, "demanda_produto": 0, "compras": 0,
                 "investimentos": 0}
        for cidade in cidades:
            dependentes = self.dependentes(cidade)
            for chave, valor in dependentes.items():
                total[chave] += valor
            self.stdout.write(
                "  {:<16} {:>5} km  ".format(cidade.nome, cidade.distancia_km)
                + "  ".join(f"{k}={v}" for k, v in dependentes.items())
            )

        if total["compras"] or total["investimentos"]:
            # Sao PROTECT/registro financeiro: apagar aqui mascararia caixa
            # ja debitado. Quem tiver isso precisa decidir caso a caso.
            self.stdout.write(self.style.ERROR(
                "Há compras de matéria-prima ou investimentos apontando para "
                "essas praças. O comando não apaga: isso mexeria em caixa já "
                "debitado. Resolva esses registros antes."
            ))
            return

        if not options["confirmar"]:
            self.stdout.write(
                "\n{} praça(s) e {} envio(s), {} linha(s) de market share e {} de "
                "demanda por produto seriam apagados.\nRode de novo com "
                "--confirmar para executar.".format(
                    len(cidades), total["envios"], total["market_share"],
                    total["demanda_produto"],
                )
            )
            return

        with transaction.atomic():
            for cidade in cidades:
                cidade.delete()  # CASCADE leva envios, market share e demanda

        self.stdout.write(self.style.SUCCESS(
            "{} praça(s) da base regional removidas, com {} envio(s) de "
            "histórico.".format(len(cidades), total["envios"])
        ))

    @staticmethod
    def dependentes(cidade):
        return {
            "envios": Distribuicao.objects.filter(cidade=cidade).count(),
            "market_share": MarketShareCidadeProduto.objects.filter(cidade=cidade).count(),
            "demanda_produto": DemandaCidadeProduto.objects.filter(cidade=cidade).count(),
            "compras": CompraMateriaPrima.objects.filter(cidade_fornecedora=cidade).count(),
            "investimentos": Investimento.objects.filter(cidade=cidade).count(),
        }
