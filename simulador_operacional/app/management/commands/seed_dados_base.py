from decimal import Decimal

from django.core.management.base import BaseCommand

from app.models import (
    Cidade,
    ComposicaoProduto,
    DemandaCidadeProduto,
    Evento,
    GameConfig,
    Jogo,
    MateriaPrima,
    Produto,
)


class Command(BaseCommand):
    help = "Popula dados base do simulador (idempotente)."

    def handle(self, *args, **options):
        config, _ = GameConfig.objects.get_or_create(
            id=1,
            defaults={
                "capital_inicial": 1000000,
                "estoque_inicial": 0,
                "maquinas_iniciais": 40,
                "capacidade_maquina": 100,
                "modulo_producao": True,
                "modulo_distribuicao": True,
                "modulo_financeiro": True,
                "ranking_pesos": {
                    "lucro": 0.4,
                    "market_share": 0.3,
                    "atendimento": 0.2,
                    "eficiencia_estoque": 0.1,
                },
            },
        )
        if not config.ranking_pesos:
            config.ranking_pesos = {
                "lucro": 0.4,
                "market_share": 0.3,
                "atendimento": 0.2,
                "eficiencia_estoque": 0.1,
            }
            config.save(update_fields=["ranking_pesos"])

        Jogo.objects.get_or_create(
            nome="Jogo Principal",
            defaults={"config": config, "ativo": True},
        )

        materias_primas = [
            ("MP1", "Materia-Prima 1", 3.00),
            ("MP2", "Materia-Prima 2", 5.50),
            ("MP3", "Materia-Prima 3", 8.00),
            ("MP4", "Materia-Prima 4", 15.00),
        ]
        for codigo, nome, preco in materias_primas:
            MateriaPrima.objects.update_or_create(
                codigo=codigo,
                defaults={"nome": nome, "preco_unitario": preco, "ativa": True},
            )

        produtos = [
            ("A", "Produto A", False, 0, 2),
            ("B", "Produto B", True, 1, 4),
            ("C", "Produto C", False, 0, 5),
        ]
        for codigo, nome, perecivel, validade, tempo in produtos:
            Produto.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nome": nome,
                    "perecivel": perecivel,
                    "validade_rodadas": validade,
                    "tempo_producao_min": tempo,
                    "ativo": True,
                },
            )

        composicoes = [
            ("A", "MP1", 120),
            ("A", "MP2", 40),
            ("A", "MP3", 60),
            ("A", "MP4", 80),
            ("B", "MP1", 360),
            ("B", "MP2", 160),
            ("B", "MP3", 110),
            ("C", "MP1", 280),
            ("C", "MP2", 280),
            ("C", "MP4", 90),
        ]
        for produto_codigo, mp_codigo, quantidade in composicoes:
            produto = Produto.objects.get(codigo=produto_codigo)
            mp = MateriaPrima.objects.get(codigo=mp_codigo)
            ComposicaoProduto.objects.update_or_create(
                produto=produto,
                materia_prima=mp,
                defaults={"quantidade_por_unidade": quantidade},
            )

        cidades = [
            ("Sao Paulo", 2896, 27000),
            ("Rio de Janeiro", 2588, 15000),
            ("Recife", 290, 4000),
            ("Joao Pessoa", 181, 2000),
            ("Aracaju", 782, 1000),
            ("Fortaleza", 527, 6000),
            ("Goiania", 1949, 3000),
            ("Belem", 1952, 3000),
            ("Maceio", 542, 2000),
            ("Porto Alegre", 4034, 3000),
        ]
        for nome, distancia, demanda in cidades:
            Cidade.objects.update_or_create(
                nome=nome,
                defaults={"distancia_km": distancia, "demanda": demanda},
            )

        for cidade in Cidade.objects.all():
            for produto in Produto.objects.filter(ativo=True):
                if produto.codigo == "A":
                    fator = Decimal("0.50")
                elif produto.codigo == "B":
                    fator = Decimal("0.30")
                else:
                    fator = Decimal("0.20")
                demanda_maxima = int(Decimal(cidade.demanda) * fator)
                DemandaCidadeProduto.objects.update_or_create(
                    cidade=cidade,
                    produto=produto,
                    defaults={"demanda_maxima": demanda_maxima},
                )

        eventos = [
            (
                "Greve de caminhoneiros",
                "custo_transporte",
                "percentual",
                "",
                1,
                30,
                "Paralisacao parcial do transporte rodoviario.",
            ),
            (
                "Bloqueio portuario",
                "custo_transporte",
                "percentual",
                "",
                1,
                25,
                "Atrasos em cargas elevam custos de distribuicao.",
            ),
            (
                "Aumento do diesel",
                "custo_transporte",
                "percentual",
                "",
                1,
                18,
                "Combustivel mais caro pressiona a malha logistica.",
            ),
            (
                "Melhoria de infraestrutura rodoviaria",
                "custo_transporte",
                "percentual",
                "",
                1,
                -12,
                "Fluxo logistico mais eficiente reduz gastos de transporte.",
            ),
            (
                "Crise de abastecimento",
                "custo_producao",
                "percentual",
                "",
                1,
                30,
                "Insumos ficaram mais caros nesta rodada.",
            ),
            (
                "Disputa global por insumos",
                "custo_producao",
                "percentual",
                "",
                1,
                22,
                "Fornecedores elevaram tabelas de preco.",
            ),
            (
                "Renegociacao com fornecedores",
                "custo_producao",
                "percentual",
                "",
                1,
                -10,
                "Contratos melhores reduziram o custo de producao.",
            ),
            (
                "Superoferta agricola",
                "custo_producao",
                "percentual",
                "",
                1,
                -20,
                "Oferta acima do esperado barateou materias-primas.",
            ),
            (
                "Boom de consumo",
                "demanda",
                "percentual",
                "",
                1,
                15,
                "A demanda aumentou no mercado.",
            ),
            (
                "Campanha de incentivo ao consumo",
                "demanda",
                "percentual",
                "",
                1,
                12,
                "O varejo acelerou pedidos para reposicao.",
            ),
            (
                "Queda de confianca do consumidor",
                "demanda",
                "percentual",
                "",
                1,
                -14,
                "Consumidores reduziram compras nesta rodada.",
            ),
            (
                "Estabilidade economica",
                "demanda",
                "percentual",
                "",
                1,
                0,
                "Mercado estavel nesta rodada.",
            ),
            (
                "Pane em linha de producao",
                "custo_producao",
                "estado",
                "bloqueio_producao",
                1,
                100,
                "Uma rodada com bloqueio parcial de producao.",
            ),
            (
                "Embargo temporario de entregas",
                "demanda",
                "estado",
                "retencao_entrega",
                1,
                50,
                "Entregas retidas reduzem a demanda atendivel.",
            ),
            (
                "Quebra de armazenamento",
                "custo_producao",
                "estado",
                "quebra_estoque",
                1,
                10,
                "Perdas de estoque por falha operacional.",
            ),
            (
                "Interdicao de fornecedor",
                "custo_producao",
                "estado",
                "atraso_mp",
                2,
                100,
                "Recebimentos de MP atrasam temporariamente.",
            ),
        ]
        for nome, tipo, modo, efeito_estado, duracao, impacto, descricao in eventos:
            Evento.objects.update_or_create(
                nome=nome,
                defaults={
                    "tipo": tipo,
                    "modo_aplicacao": modo,
                    "efeito_estado": efeito_estado,
                    "duracao_rodadas": duracao,
                    "impacto_percentual": impacto,
                    "probabilidade": 0,
                    "descricao": descricao,
                },
            )

        total_eventos = Evento.objects.count()
        if total_eventos > 0:
            prob_igual = round(1 / total_eventos, 6)
            Evento.objects.all().update(probabilidade=prob_igual)

        self.stdout.write(self.style.SUCCESS("Dados base populados com sucesso."))
