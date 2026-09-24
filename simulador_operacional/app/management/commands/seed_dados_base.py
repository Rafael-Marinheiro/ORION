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
    default_ranking_pesos,
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
                "modulo_producao": True,
                "modulo_distribuicao": True,
                "modulo_financeiro": True,
                "ranking_pesos": default_ranking_pesos(),
            },
        )
        if not config.ranking_pesos:
            config.ranking_pesos = default_ranking_pesos()
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

        # 9: "A unidade produtiva de cada grupo participante esta localizada
        # na cidade de Natal-RN, de onde partem todos os envios". Natal nao e
        # praca de venda: e a fabrica. As dez pracas abaixo sao a tabela do
        # 9.1, com a distancia ate Natal e o teto de absorcao por rodada.
        #
        # A coluna do 9.1 e "Demanda Maxima (unid./PRODUTO)": o teto vale
        # para cada produto, nao e um total a ser rateado entre A, B e C.
        cidades = [
            # (nome, distancia_km ate Natal, demanda maxima por produto)
            ("São Paulo", 2896, 27000),
            ("Rio de Janeiro", 2588, 15000),
            ("Recife", 290, 4000),
            ("João Pessoa", 181, 2000),
            ("Aracaju", 782, 1000),
            ("Fortaleza", 527, 6000),
            ("Goiânia", 1949, 3000),
            ("Belém", 1952, 3000),
            ("Maceió", 542, 2000),
            ("Porto Alegre", 4034, 3000),
        ]
        for nome, distancia, demanda in cidades:
            Cidade.objects.update_or_create(
                nome=nome,
                defaults={"distancia_km": distancia, "demanda": demanda},
            )

        # 9.1: o mesmo teto para cada produto ativo.
        for nome, _, demanda in cidades:
            cidade = Cidade.objects.get(nome=nome)
            for produto in Produto.objects.filter(ativo=True):
                DemandaCidadeProduto.objects.update_or_create(
                    cidade=cidade,
                    produto=produto,
                    defaults={"demanda_maxima": demanda},
                )

        # Os 6 eventos do 8.4, com a manchete, o impacto e a probabilidade
        # que o documento define. As probabilidades somam 100%: sempre ha
        # exatamente um evento por rodada (decisao B4).
        eventos = [
            (
                "Greve de caminhoneiros",
                "O país enfrenta uma greve geral no setor de transporte rodoviário.",
                "custo_transporte",
                "percentual",
                "",
                1,
                30,
                30,
                15,
                "Paralisação do transporte rodoviário nacional. Custo logístico sobe "
                "30% e 30% das entregas ficam retidas; o perecível retido é perdido.",
            ),
            (
                "Crise de abastecimento",
                "A seca afetou a produção agrícola, encarecendo os insumos.",
                "custo_producao",
                "percentual",
                "",
                1,
                30,
                0,
                20,
                "Seca prolongada compromete a produção de insumos agrícolas.",
            ),
            (
                "Boom de consumo",
                "O mercado está aquecido e os consumidores estão comprando mais.",
                "demanda",
                "percentual",
                "",
                1,
                15,
                0,
                20,
                "Otimismo do mercado impulsiona as vendas.",
            ),
            (
                "Enchentes nas regiões",
                "As enchentes interromperam as principais rotas logísticas.",
                "custo_transporte",
                "percentual",
                "",
                1,
                0,
                20,
                15,
                "Chuvas interrompem as rotas. 20% das entregas ficam retidas para a "
                "próxima rodada; o perecível retido é perdido.",
            ),
            (
                "Estabilidade econômica",
                "O mercado está estável, sem grandes alterações previstas.",
                "demanda",
                "percentual",
                "",
                1,
                0,
                0,
                15,
                "Período de normalidade econômica e previsibilidade.",
            ),
            (
                "Superoferta agrícola",
                "A safra foi abundante, reduzindo o custo dos insumos.",
                "custo_producao",
                "percentual",
                "",
                1,
                -20,
                0,
                15,
                "Colheita excepcional reduz o custo dos insumos.",
            ),
        ]
        # O 8.4 e a lista fechada de eventos. Evento que nao esteja nela sai,
        # senao a soma das probabilidades deixa de fechar em 100%.
        nomes_do_documento = [evento[0] for evento in eventos]
        Evento.objects.exclude(nome__in=nomes_do_documento).delete()

        for (
            nome,
            frase,
            tipo,
            modo,
            efeito_estado,
            duracao,
            impacto,
            retencao,
            probabilidade,
            descricao,
        ) in eventos:
            Evento.objects.update_or_create(
                nome=nome,
                defaults={
                    "frase_indicativa": frase,
                    "tipo": tipo,
                    "modo_aplicacao": modo,
                    "efeito_estado": efeito_estado,
                    "duracao_rodadas": duracao,
                    "impacto_percentual": impacto,
                    "retencao_entregas_percent": retencao,
                    "probabilidade": probabilidade,
                    "descricao": descricao,
                },
            )

        self.stdout.write(self.style.SUCCESS("Dados base populados com sucesso."))
