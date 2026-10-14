from decimal import Decimal

from django.core.management.base import BaseCommand

from app.models import (
    Cidade,
    ComposicaoProduto,
    CompraMateriaPrima,
    DemandaCidadeProduto,
    Distribuicao,
    Evento,
    GameConfig,
    Jogo,
    Investimento,
    MarketShareCidadeProduto,
    MateriaPrima,
    Produto,
    default_ranking_pesos,
)


# A base regional que o 9.1 substituiu (D9.2). Nomeada, e nao deduzida por
# "tudo que nao esta no 9.1", porque o professor pode cadastrar praca propria
# e ela nao pode ser varrida junto. Recife e Fortaleza estavam nas duas bases
# com distancias diferentes -- essas o seed corrige no lugar, nao remove.
PRACAS_DA_BASE_REGIONAL = (
    "Currais Novos", "Acari", "Caico", "Santa Cruz", "Patos", "Assu",
    "Natal", "Campina Grande", "Mossoro", "Joao Pessoa",
)


class Command(BaseCommand):
    help = "Popula dados base do simulador (idempotente)."

    def aposentar_pracas_legadas(self):
        """Tira de jogo as pracas da base regional que o 9.1 substituiu.

        Praca sem movimento e apagada. Praca com movimento fica: apagar
        levaria junto o historico de envios das turmas passadas, porque
        `Distribuicao.cidade` e CASCADE. Ela sai de jogo por demanda zero,
        que e o que o fechamento consulta -- e o formulario de destino so
        oferece praca com demanda, entao ela some da tela tambem.
        """
        legadas = Cidade.objects.filter(nome__in=PRACAS_DA_BASE_REGIONAL)
        apagadas, aposentadas = [], []
        for cidade in legadas:
            tem_historico = (
                Distribuicao.objects.filter(cidade=cidade).exists()
                or CompraMateriaPrima.objects.filter(cidade_fornecedora=cidade).exists()
                or MarketShareCidadeProduto.objects.filter(cidade=cidade).exists()
                or Investimento.objects.filter(cidade=cidade).exists()
            )
            if tem_historico:
                DemandaCidadeProduto.objects.filter(cidade=cidade).update(demanda_maxima=0)
                if cidade.demanda:
                    cidade.demanda = 0
                    cidade.save(update_fields=["demanda"])
                aposentadas.append(cidade.nome)
            else:
                DemandaCidadeProduto.objects.filter(cidade=cidade).delete()
                apagadas.append(cidade.nome)
                cidade.delete()

        if apagadas:
            self.stdout.write(
                "Praças fora do §9.1 removidas: " + ", ".join(sorted(apagadas))
            )
        if aposentadas:
            self.stdout.write(
                "Praças fora do §9.1 com histórico — demanda zerada, histórico "
                "preservado: " + ", ".join(sorted(aposentadas))
            )

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

        # A base do 9.1 substitui a anterior -- nao convive com ela.
        # `update_or_create` so acrescenta, entao quem ja tinha rodado a
        # versao regional ficava com as dez pracas do 9.1 MAIS as nove
        # antigas, "Joao Pessoa" duplicando "Joao Pessoa" com outra
        # distancia e Currais Novos a 0 km -- frete zero, que anula o 9.2a.
        self.aposentar_pracas_legadas()

        # 7.1: cada MP tem fornecedores determinados. Precisa vir depois das
        # cidades, que so existem acima.
        #
        # Sem isto a compra aceitava qualquer praca, e a estrategia otima
        # virava trazer as quatro MPs da cidade mais proxima -- Joao Pessoa,
        # a 181 km --, anulando o 7.1: ninguem compraria MP1 em Fortaleza
        # (527 km) nem MP3 em Aracaju (782 km).
        fornecedores_por_mp = {
            "MP1": ["Fortaleza", "Maceió"],
            "MP2": ["Recife", "Porto Alegre"],
            "MP3": ["Rio de Janeiro", "Aracaju", "Belém"],
            "MP4": ["São Paulo", "João Pessoa", "Goiânia"],
        }
        for codigo, nomes in fornecedores_por_mp.items():
            materia = MateriaPrima.objects.filter(codigo=codigo).first()
            if not materia:
                continue
            materia.fornecedores.set(Cidade.objects.filter(nome__in=nomes))

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
        nomes_do_documento = [evento[0] for evento in eventos]

        # Pool estendido: eventos que NAO estao no 8.4, sorteados apenas
        # pelas turmas que ligarem `GameConfig.eventos_estendidos`.
        #
        # Desde 14/10/2026 o sorteio e uniforme -- todo evento elegivel tem
        # a mesma chance --, entao a coluna `probabilidade` nao pesa mais no
        # resultado. Fica igual para todos aqui, para o dado nao contradizer
        # o comportamento. Os seis do 8.4 mantem os valores do documento.
        #
        # Tres deles exercitam mecanica que ja existia e nenhum evento do
        # 8.4 acionava: `duracao_rodadas` (evento recorrente, ressalvado no
        # 8.2), `atraso_mp` e `quebra_estoque`.
        estendidos = [
            (
                "Tarifacao externa",
                "Novas tarifas de importacao elevam o custo dos insumos.",
                "custo_producao",
                "percentual",
                "",
                3,
                15,
                0,
                8,
                "Barreira tarifaria encarece o insumo importado por tres rodadas. "
                "Choque moderado e persistente, ao contrario da crise de "
                "abastecimento, que e aguda e passa.",
            ),
            (
                "Retracao de consumo",
                "O mercado esfriou e os consumidores estao segurando as compras.",
                "demanda",
                "percentual",
                "",
                1,
                -15,
                0,
                8,
                "Queda generalizada da demanda. O 8.4 traz o boom de +15% e nada "
                "simetrico: sem isto o eixo economico so empurra para cima.",
            ),
            (
                "Entrada de concorrente",
                "Um novo concorrente entrou no mercado e disputa as mesmas pracas.",
                "demanda",
                "percentual",
                "",
                2,
                -10,
                0,
                8,
                "Perda de participacao por duas rodadas.",
            ),
            (
                "Alta do combustivel",
                "O reajuste do diesel encareceu o frete rodoviario.",
                "custo_transporte",
                "percentual",
                "",
                1,
                15,
                0,
                8,
                "Custo logistico sobe sem reter entregas: versao branda da greve.",
            ),
            (
                "Atraso de fornecedores",
                "Os fornecedores comunicaram atraso na entrega dos pedidos.",
                "greve",
                "estado",
                "atraso_mp",
                1,
                0,
                0,
                8,
                "A materia-prima pedida chega uma rodada depois do previsto. "
                "Atinge o planejamento de compra, que nenhum evento do 8.4 toca.",
            ),
            (
                "Safra regular",
                "A colheita veio dentro do esperado e os insumos ficaram mais baratos.",
                "custo_producao",
                "percentual",
                "",
                1,
                -10,
                0,
                8,
                "Alivio moderado no custo de insumo: versao branda da superoferta.",
            ),
            (
                "Avaria no armazem",
                "Uma avaria no armazem comprometeu parte do estoque.",
                "perda_estoque",
                "estado",
                "quebra_estoque",
                1,
                10,
                0,
                8,
                "10% do estoque de produto acabado e perdido, com a baixa "
                "financeira correspondente.",
            ),
            (
                "Apagao na regiao",
                "Uma falha prolongada no fornecimento de energia parou o parque fabril.",
                "greve",
                "estado",
                "bloqueio_producao",
                1,
                0,
                0,
                8,
                "Sem energia nao ha producao na rodada. O estoque e as entregas "
                "seguem normalmente -- o que para e a fabrica.",
            ),
            (
                "Nova rota pavimentada",
                "A conclusao da obra na rodovia encurtou o trajeto ate as pracas.",
                "custo_transporte",
                "percentual",
                "",
                3,
                -15,
                0,
                8,
                "Melhoria permanente de malha: o frete cai por tres rodadas. "
                "Favorece quem ja tinha estrutura de distribuicao montada.",
            ),
            (
                "Acordo setorial de fretes",
                "As transportadoras fecharam acordo e reduziram as tarifas.",
                "custo_transporte",
                "percentual",
                "",
                1,
                -12,
                0,
                8,
                "Alivio de uma rodada no custo logistico.",
            ),
            (
                "Janela portuaria antecipada",
                "O porto liberou janela extra e os pedidos chegaram antes.",
                "custo_producao",
                "percentual",
                "",
                1,
                -8,
                0,
                8,
                "A antecipacao reduz o custo do insumo na rodada. Contrapeso "
                "favoravel ao atraso de fornecedores.",
            ),
            (
                "Baixa sazonal no frete",
                "A baixa temporada reduziu o preco do frete rodoviario.",
                "custo_transporte",
                "percentual",
                "",
                1,
                -10,
                0,
                8,
                "Unico evento logistico favoravel: o 8.4 so tem greve e enchente, "
                "ambos contra o grupo.",
            ),
        ]
        nomes_estendidos = [evento[0] for evento in estendidos]

        # Evento de decisao. Nao cabe na tupla dos outros: tem preco por
        # trabalhador e faixa de impacto, campos que so ele usa.
        surto, _ = Evento.objects.update_or_create(
            nome="Surto de gripe",
            defaults={
                "frase_indicativa": (
                    "Um surto de gripe avanca na regiao e o servico de saude "
                    "oferece imunizacao as empresas."
                ),
                "tipo": "greve",
                "modo_aplicacao": "decisao",
                "efeito_estado": "afastamento_equipe",
                "duracao_rodadas": 1,
                # afastamento de quem nao imunizar: igual para todas as
                # equipes que recusarem (8.2, "de maneira igual")
                "impacto_percentual": 25,
                "custo_unitario_decisao": Decimal("180.00"),
                "retencao_entregas_percent": 0,
                "probabilidade": 8,
                "descricao": (
                    "A imunizacao custa um valor por trabalhador e protege a "
                    "equipe pela rodada. Sem ela, parte da forca de trabalho "
                    "pode ser afastada, e maquina sem os dois operadores do "
                    "RN-06 nao produz."
                ),
                "extensao": True,
                # So acontece uma vez por turma: na segunda, a equipe ja
                # conhece preco e efeito, e a decisao vira conta.
                "unico_por_jogo": True,
            },
        )
        nomes_estendidos.append(surto.nome)

        # Evento fora das duas listas sai -- menos o que o professor criou
        # a mao, que nao pertence a catalogo nenhum.
        Evento.objects.filter(manual=False).exclude(
            nome__in=nomes_do_documento + nomes_estendidos
        ).delete()

        for lista, extensao in ((eventos, False), (estendidos, True)):
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
            ) in lista:
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
                        "extensao": extensao,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Dados base populados com sucesso."))
