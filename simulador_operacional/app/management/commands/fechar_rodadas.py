import logging
import random
from collections import defaultdict
from decimal import Decimal
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from app.parametros import (
    CUSTO_ARMAZENAGEM_PERCENT,
    CUSTO_OPERADOR_POR_RODADA,
    PESOS_EIXOS,
)
from app.services.eventos import (
    efeito_absoluto,
    evento_estado_ativo,
    eventos_da_rodada,
    fator_percentual,
    lista_de_eventos,
    sortear_evento,
)
from app.services.suprimentos import processar_recebimentos_materia_prima
from app.services.distribuicao_service import executar_expedicao
from app.services.producao import executar_producao, garantir_capacidades_grupo
from app.services.marketing import fator_marketing
from app.services.pontuacao import calcular_eixos, coletar_insumos, pontuacao_total
from app.services.perecibilidade import lote_vencido
from app.services.retencao import aplicar_retencao_de_entregas
from app.models import (
    AplicacaoFinanceiraGrupo,
    CapacidadeProdutoGrupo,
    ConsolidadoRodadaGrupo,
    DemandaCidadeProduto,
    Distribuicao,
    EstoqueMateriaPrima,
    EstoqueProduto,
    Evento,
    EventoRodada,
    ExecucaoJob,
    GameConfig,
    Grupo,
    IndicadorRodadaGrupo,
    Investimento,
    MarketShareCidadeProduto,
    ResultadoFinanceiro,
    Rodada,
)

logger = logging.getLogger("agendamentos")



class Command(BaseCommand):
    help = "Fecha rodadas cujo prazo se encerrou"

    @staticmethod
    def obter_evento_rodada(rodada_numero, jogo_id=None):
        """Delega ao service, para nao existir uma segunda regra de sorteio."""
        return sortear_evento(rodada_numero, jogo_id)

    @staticmethod
    def obter_evento_estado_ativo(rodada_numero, jogo_id, efeito_estado):
        return evento_estado_ativo(
            rodada_numero=rodada_numero, efeito_estado=efeito_estado, jogo_id=jogo_id
        )

    @staticmethod
    def calcular_custo_armazenagem_mp(grupo):
        total_valor = Decimal("0")
        estoques = EstoqueMateriaPrima.objects.filter(grupo=grupo).select_related("materia_prima")
        for estoque in estoques:
            total_valor += estoque.quantidade_kg * estoque.materia_prima.preco_unitario
        # 7.4: 2% sobre o valor de compra das MPs estocadas.
        return total_valor * CUSTO_ARMAZENAGEM_PERCENT / Decimal("100")

    @staticmethod
    def calcular_custo_armazenagem_produtos(grupo):
        total_valor = Decimal("0")
        lotes = EstoqueProduto.objects.filter(
            grupo=grupo,
            produto__perecivel=False,
            quantidade__gt=0,
        ).select_related("produto")
        for lote in lotes:
            total_valor += Decimal(lote.quantidade) * lote.produto.custo_unitario_estimado
        # 6.4: 2% sobre o valor de producao unitario, so no nao perecivel.
        return total_valor * CUSTO_ARMAZENAGEM_PERCENT / Decimal("100")

    @staticmethod
    def processar_perecibilidade(grupo, rodada_numero):
        perda_total = Decimal("0")
        lotes = EstoqueProduto.objects.filter(
            grupo=grupo,
            produto__perecivel=True,
            quantidade__gt=0,
        ).select_related("produto")
        for lote in lotes:
            # 6.2: perda TOTAL, sem venda com desconto e sem reembolso --
            # ratificado pelo Dr. Pio em 24/09/2026.
            if lote_vencido(lote, rodada_numero):
                perda_total += Decimal(lote.quantidade) * lote.produto.custo_unitario_estimado
                lote.quantidade = 0
                lote.save(update_fields=["quantidade"])
        return perda_total

    @staticmethod
    def processar_quebra_estoque(grupo, evento_quebra):
        if not evento_quebra:
            return Decimal("0")
        percent = abs(Decimal(evento_quebra.impacto_percentual))
        if percent <= 0:
            percent = Decimal("10")
        perda_financeira = Decimal("0")
        lotes = EstoqueProduto.objects.filter(grupo=grupo, quantidade__gt=0).select_related("produto")
        for lote in lotes:
            quebra_qtd = int((Decimal(lote.quantidade) * percent / Decimal("100")).to_integral_value())
            quebra_qtd = min(quebra_qtd, lote.quantidade)
            if quebra_qtd <= 0:
                continue
            lote.quantidade -= quebra_qtd
            lote.save(update_fields=["quantidade"])
            perda_financeira += Decimal(quebra_qtd) * lote.produto.custo_unitario_estimado
        return perda_financeira

    @staticmethod
    def atualizar_estoque_total(grupo):
        total = (
            EstoqueProduto.objects.filter(grupo=grupo).aggregate(total=Sum("quantidade")).get("total")
            or 0
        )
        grupo.estoque = int(total)

    @staticmethod
    def calcular_peso_preco(preco, preco_medio):
        if preco_medio <= 0:
            return Decimal("1")
        diff_percentual = ((preco - preco_medio) / preco_medio) * Decimal("100")
        if diff_percentual <= Decimal("-20"):
            return Decimal("5")
        if diff_percentual <= Decimal("-10"):
            return Decimal("3")
        if diff_percentual <= Decimal("0"):
            return Decimal("2")
        if diff_percentual <= Decimal("10"):
            return Decimal("1")
        return Decimal("0.5")

    @staticmethod
    def obter_pesos_ranking(ranking_pesos):
        """Pesos dos cinco eixos do 12.4, normalizados para somar 1.

        O 12.2 admite que o professor ajuste os pesos por rodada conforme o
        foco pedagogico; `GameConfig.ranking_pesos` e onde isso entra.
        """
        padrao = dict(PESOS_EIXOS)
        if not isinstance(ranking_pesos, dict):
            return padrao

        pesos = {}
        for chave, valor_padrao in padrao.items():
            try:
                pesos[chave] = Decimal(str(ranking_pesos.get(chave, valor_padrao)))
            except Exception:
                pesos[chave] = valor_padrao

        soma = sum(pesos.values())
        if soma <= 0:
            return padrao

        return {chave: valor / soma for chave, valor in pesos.items()}

    @staticmethod
    def limitar(valor, teto=Decimal("99999.99")):
        """Encaixa o percentual no campo (max_digits=7).

        EE e um giro: com estoque medio quase zerado o indicador dispara, e
        um estouro de coluna derrubaria o fechamento inteiro da rodada.
        """
        valor = Decimal(valor).quantize(Decimal("0.01"))
        return max(-teto, min(teto, valor))

    @staticmethod
    def obter_demanda_base(cidade, produto):
        demanda = DemandaCidadeProduto.objects.filter(cidade=cidade, produto=produto).first()
        if demanda:
            return int(demanda.demanda_maxima)
        return int(cidade.demanda)

    def processar_investimentos_pendentes(self, grupo, rodada_numero):
        pendentes = Investimento.objects.filter(
            grupo=grupo,
            processado=False,
            rodada_ativacao__lte=rodada_numero,
            categoria__in=["maquinas", "rh"],
            produto__isnull=False,
        ).select_related("produto")
        custos_rh_recorrentes = Decimal("0")
        for investimento in pendentes:
            capacidade, _ = CapacidadeProdutoGrupo.objects.get_or_create(
                grupo=grupo,
                produto=investimento.produto,
                defaults={
                    "maquinas": 0,
                    "operadores": 0,
                    "minutos_por_maquina": 400,
                },
            )
            if investimento.categoria == "maquinas":
                capacidade.maquinas += int(investimento.quantidade)
            elif investimento.categoria == "rh":
                capacidade.operadores += int(investimento.quantidade)
            capacidade.save(update_fields=["maquinas", "operadores"])
            investimento.processado = True
            investimento.save(update_fields=["processado"])

        for capacidade in grupo.capacidades_produto.all():
            if capacidade.operadores > 0:
                custos_rh_recorrentes += Decimal(capacidade.operadores) * CUSTO_OPERADOR_POR_RODADA
        return custos_rh_recorrentes

    @staticmethod
    def aplicar_rendimento_financeiro(grupo):
        aplicacao, _ = AplicacaoFinanceiraGrupo.objects.get_or_create(
            grupo=grupo,
            defaults={"saldo_aplicado": Decimal("0"), "taxa_juros_rodada": Decimal("0.015")},
        )
        if aplicacao.saldo_aplicado <= 0:
            return Decimal("0")
        rendimento = aplicacao.saldo_aplicado * aplicacao.taxa_juros_rodada
        aplicacao.saldo_aplicado += rendimento
        aplicacao.save(update_fields=["saldo_aplicado", "data_atualizacao"])
        return rendimento

    @staticmethod
    def caixa_base_para_penalidade(grupo, rodada_numero):
        """Retorna o caixa final da rodada anterior (DOCX 11.2).

        Na primeira rodada ainda não existe resultado consolidado; nesse caso,
        o capital inicial do grupo é a única base disponível.
        """
        resultado_anterior = (
            ResultadoFinanceiro.objects.filter(grupo=grupo, rodada__lt=rodada_numero)
            .order_by("-rodada")
            .first()
        )
        return resultado_anterior.saldo_caixa if resultado_anterior else grupo.capital

    def processar_vendas_por_demanda(self, rodada, grupos_ids, evento=None, eventos=None):
        rodada_numero = rodada.numero
        jogo_id = rodada.jogo_id
        MarketShareCidadeProduto.objects.filter(rodada=rodada_numero, grupo_id__in=grupos_ids).delete()

        # 8.4: a retencao e do evento da rodada, e um evento pode reter e
        # encarecer ao mesmo tempo (a greve faz as duas coisas).
        ativos = lista_de_eventos(eventos, evento)
        percentual_retido = max(
            [int(getattr(item, "retencao_entregas_percent", 0) or 0) for item in ativos]
            or [0]
        )

        envios = list(
            Distribuicao.objects.filter(
                rodada=rodada_numero,
                grupo_id__in=grupos_ids,
                processada=False,
                produto__isnull=False,
            ).select_related("cidade", "produto", "grupo")
        )
        if not envios:
            return {
                "receitas_por_grupo": defaultdict(lambda: Decimal("0")),
                "vendidos_por_grupo": defaultdict(int),
                "ofertados_por_grupo": defaultdict(int),
                "total_vendido_rodada": 0,
                "perdas_retencao_por_grupo": {},
            }

        perdas_retencao = aplicar_retencao_de_entregas(envios, percentual_retido, rodada_numero)
        envios = [envio for envio in envios if envio.quantidade > 0]

        buckets = defaultdict(list)
        ofertados_por_grupo = defaultdict(int)
        for envio in envios:
            buckets[(envio.cidade_id, envio.produto_id)].append(envio)
            ofertados_por_grupo[envio.grupo_id] += int(envio.quantidade)

        receitas_por_grupo = defaultdict(lambda: Decimal("0"))
        vendidos_por_grupo = defaultdict(int)
        total_vendido_rodada = 0

        for (_, _), itens in buckets.items():
            cidade = itens[0].cidade
            produto = itens[0].produto
            demanda = self.obter_demanda_base(cidade, produto)
            # O evento do professor pode valer so para algumas pracas; o do
            # 8.4 vale para o mercado inteiro. Percentual primeiro, depois o
            # absoluto -- somar antes faria o percentual incidir sobre o
            # ajuste manual.
            demanda = Decimal(demanda) * fator_percentual(ativos, "demanda", cidade.id)
            demanda += efeito_absoluto(ativos, "demanda", cidade.id)
            demanda = max(int(demanda), 0)

            if demanda == 0:
                for envio in itens:
                    envio.quantidade_vendida = 0
                    envio.quantidade_sobra = envio.quantidade
                    envio.receita_realizada = Decimal("0")
                    envio.processada = True
                    envio.save(
                        update_fields=[
                            "quantidade_vendida",
                            "quantidade_sobra",
                            "receita_realizada",
                            "processada",
                        ]
                    )
                    MarketShareCidadeProduto.objects.update_or_create(
                        grupo=envio.grupo,
                        cidade=cidade,
                        produto=produto,
                        rodada=rodada_numero,
                        defaults={"quantidade_vendida": 0, "market_share_percent": Decimal("0")},
                    )
                continue

            preco_medio = sum((envio.preco_unitario for envio in itens), Decimal("0")) / Decimal(len(itens))
            alocacoes = []
            soma_scores = Decimal("0")
            for envio in itens:
                peso_preco = self.calcular_peso_preco(envio.preco_unitario, preco_medio)
                mc = fator_marketing(envio.grupo, cidade, rodada_numero)
                score = peso_preco * Decimal(envio.quantidade) * mc
                soma_scores += score
                alocacoes.append(
                    {
                        "envio": envio,
                        "score": score,
                        "fracao": Decimal("0"),
                        "vendida": 0,
                        "capacidade": int(envio.quantidade),
                    }
                )

            if soma_scores <= 0:
                for item in alocacoes:
                    envio = item["envio"]
                    envio.quantidade_vendida = 0
                    envio.quantidade_sobra = envio.quantidade
                    envio.receita_realizada = Decimal("0")
                    envio.processada = True
                    envio.save(
                        update_fields=[
                            "quantidade_vendida",
                            "quantidade_sobra",
                            "receita_realizada",
                            "processada",
                        ]
                    )
                    MarketShareCidadeProduto.objects.update_or_create(
                        grupo=envio.grupo,
                        cidade=cidade,
                        produto=produto,
                        rodada=rodada_numero,
                        defaults={"quantidade_vendida": 0, "market_share_percent": Decimal("0")},
                    )
                continue

            demanda_restante = demanda
            for item in alocacoes:
                bruto = (Decimal(demanda) * item["score"]) / soma_scores
                base = int(bruto)
                vendida = min(base, item["capacidade"])
                item["vendida"] = vendida
                item["capacidade"] -= vendida
                item["fracao"] = bruto - Decimal(base)
                demanda_restante -= vendida

            ordem = sorted(alocacoes, key=lambda i: (i["fracao"], i["score"]), reverse=True)
            while demanda_restante > 0:
                movimentou = False
                for item in ordem:
                    if demanda_restante <= 0:
                        break
                    if item["capacidade"] <= 0:
                        continue
                    item["vendida"] += 1
                    item["capacidade"] -= 1
                    demanda_restante -= 1
                    movimentou = True
                if not movimentou:
                    break

            total_vendido_bucket = sum(int(item["vendida"]) for item in alocacoes)

            for item in alocacoes:
                envio = item["envio"]
                vendida = int(item["vendida"])
                sobra = int(envio.quantidade) - vendida
                receita = envio.preco_unitario * vendida
                market_share = (
                    (Decimal(vendida) * Decimal("100") / Decimal(total_vendido_bucket))
                    if total_vendido_bucket > 0
                    else Decimal("0")
                )

                envio.quantidade_vendida = vendida
                envio.quantidade_sobra = sobra
                envio.receita_realizada = receita
                envio.processada = True
                envio.save(
                    update_fields=[
                        "quantidade_vendida",
                        "quantidade_sobra",
                        "receita_realizada",
                        "processada",
                    ]
                )

                MarketShareCidadeProduto.objects.update_or_create(
                    grupo=envio.grupo,
                    cidade=cidade,
                    produto=produto,
                    rodada=rodada_numero,
                    defaults={"quantidade_vendida": vendida, "market_share_percent": market_share},
                )

                receitas_por_grupo[envio.grupo_id] += receita
                vendidos_por_grupo[envio.grupo_id] += vendida
                total_vendido_rodada += vendida

        return {
            "receitas_por_grupo": receitas_por_grupo,
            "vendidos_por_grupo": vendidos_por_grupo,
            "ofertados_por_grupo": ofertados_por_grupo,
            "total_vendido_rodada": total_vendido_rodada,
            "perdas_retencao_por_grupo": perdas_retencao,
        }

    def handle(self, *args, **options):
        correlation_id = uuid4().hex[:16]
        agora = timezone.now()
        rodadas = Rodada.objects.filter(fechada=False, fim__lte=agora).order_by("numero")
        if not rodadas:
            # Na turma este comando roda de segundo em segundo (ver
            # docker-compose.turma.yml). Registrar uma execucao a cada
            # chamada enterraria os fechamentos de verdade sob milhares de
            # linhas vazias na tela de execucoes de jobs -- que e onde o
            # professor procura o que aconteceu no prazo.
            logger.info("Nenhuma rodada para fechar em %s", agora, extra={"correlation_id": correlation_id})
            self.stdout.write("Nenhuma rodada para fechar")
            return

        job = None
        try:
            for rodada in rodadas:
                # Uma execucao por rodada fechada, com a turma e o numero
                # dela. O registro era um so por chamada, sem turma e sem
                # rodada: a tela de execucoes dizia que "algo rodou" e o
                # professor com duas turmas nao sabia qual.
                job = ExecucaoJob.objects.create(
                    comando="fechar_rodadas",
                    correlation_id=correlation_id,
                    jogo_id=rodada.jogo_id,
                    rodada=rodada.numero,
                    status="sucesso",
                    detalhes="",
                )
                # Uma falha deve desfazer todos os efeitos desta rodada.
                # O job permanece fora da transação para registrar a falha.
                with transaction.atomic():
                    rodada = Rodada.objects.select_for_update().get(pk=rodada.pk)
                    if rodada.fechada:
                        job.detalhes = "Rodada ja estava fechada."
                        job.finalizado_em = timezone.now()
                        job.save(update_fields=["detalhes", "finalizado_em"])
                        continue
                    config = rodada.jogo.config if rodada.jogo_id else GameConfig.objects.filter(pk=1).first()
                    pesos = self.obter_pesos_ranking(config.ranking_pesos if config else None)
                    logger.info(
                        "Fechando rodada %s",
                        rodada.numero,
                        extra={"correlation_id": correlation_id, "rodada": rodada.numero},
                    )
                    self.stdout.write(f"Fechando rodada {rodada.numero}")

                    grupos_qs = Grupo.objects.all()
                    if rodada.jogo_id:
                        grupos_qs = grupos_qs.filter(jogo_id=rodada.jogo_id)
                    else:
                        grupos_qs = grupos_qs.filter(jogo__isnull=True)

                    grupos = list(grupos_qs)
                    grupos_ids = [grupo.id for grupo in grupos]
                    # A rodada pode ter dois eventos desde 25/09/2026: o
                    # sorteado do 8.2 e o que o professor marcou na
                    # abertura. `evento` segue existindo para o que ainda le
                    # um so (a quebra de estoque, que e evento de estado).
                    self.obter_evento_rodada(rodada.numero, jogo_id=rodada.jogo_id)
                    eventos = eventos_da_rodada(rodada.numero, jogo_id=rodada.jogo_id)
                    evento = eventos[0] if eventos else None

                    # 11.3.b executa "Producao, vendas, compras, distribuicao"
                    # nesta ordem. Producao primeiro (13.7), expedicao depois
                    # -- senao a equipe nao poderia enviar o que produziu na
                    # mesma rodada, e o 6.2 exige que possa: o produto B
                    # "perde validade apos 1 rodada".
                    for grupo in grupos:
                        # 13.4/RN-02: o parque de largada existe mesmo para o
                        # grupo cujo CEO nunca abriu o painel.
                        garantir_capacidades_grupo(grupo)
                        # A producao CONSOME estoque; nao paga nada de novo.
                        # O 7.2 ja debitou a materia-prima "na rodada da
                        # compra", e o 7.5 enumera as saidas de caixa que a MP
                        # gera: "compras, armazenagem e logistica" -- consumo
                        # nao esta na lista, e o 7.3 o descreve como movimento
                        # de estoque. O custo do 13.9 fica gravado na ordem de
                        # producao, que e de onde sai o custo unitario do
                        # produto, o valor do estoque e o custo das vendas do
                        # 12.3.2. Ate 24/09/2026 ele tambem era debitado, e a
                        # mesma materia-prima saia do caixa duas vezes.
                        executar_producao(
                            grupo=grupo, rodada=rodada.numero, eventos=eventos
                        )
                        custo_frete, _ = executar_expedicao(
                            grupo=grupo, rodada=rodada.numero, eventos=eventos
                        )
                        operacional = custo_frete
                        if operacional > 0:
                            grupo.capital -= operacional
                            grupo.save(update_fields=["capital"])
                            rf_operacional, _ = ResultadoFinanceiro.objects.get_or_create(
                                grupo=grupo, rodada=rodada.numero
                            )
                            rf_operacional.custos += operacional
                            rf_operacional.saldo_caixa = grupo.capital
                            rf_operacional.lucro = (
                                rf_operacional.receita - rf_operacional.custos
                            )
                            rf_operacional.save()

                    stats_venda = self.processar_vendas_por_demanda(
                        rodada=rodada,
                        grupos_ids=grupos_ids,
                        eventos=eventos,
                    )

                    receitas_por_grupo = stats_venda["receitas_por_grupo"]
                    vendidos_por_grupo = stats_venda["vendidos_por_grupo"]
                    ofertados_por_grupo = stats_venda["ofertados_por_grupo"]
                    total_vendido_rodada = stats_venda["total_vendido_rodada"]
                    perdas_retencao = stats_venda.get("perdas_retencao_por_grupo", {})

                    evento_quebra = self.obter_evento_estado_ativo(
                        rodada_numero=rodada.numero,
                        jogo_id=rodada.jogo_id,
                        efeito_estado="quebra_estoque",
                    )

                    metricas = {}

                    for grupo in grupos:
                        custos_extras = Decimal("0")
                        motivos = []
                        penalidade_sem_submissao = Decimal("0")
                        perda_pereciveis = Decimal("0")
                        perda_quebra_estoque = Decimal("0")
                        custo_armazenagem_mp = Decimal("0")
                        custo_armazenagem_produtos = Decimal("0")

                        custo_rh_recorrente = self.processar_investimentos_pendentes(
                            grupo=grupo,
                            rodada_numero=rodada.numero,
                        )

                        receita_vendas = receitas_por_grupo.get(grupo.id, Decimal("0"))
                        if receita_vendas > 0:
                            grupo.capital += receita_vendas
                            motivos.append("receita de vendas por demanda")

                        receita_financeira = self.aplicar_rendimento_financeiro(grupo)
                        if receita_financeira > 0:
                            motivos.append("rendimento de aplicacoes financeiras")

                        if not grupo.decisoes.filter(rodada=rodada.numero).exists():
                            caixa_base = self.caixa_base_para_penalidade(grupo, rodada.numero)
                            penalidade_sem_submissao = caixa_base * Decimal("0.10")
                            custos_extras += penalidade_sem_submissao
                            motivos.append("penalidade por falta de submissao")

                        perda_pereciveis = self.processar_perecibilidade(grupo, rodada.numero)
                        if perda_pereciveis > 0:
                            custos_extras += perda_pereciveis
                            motivos.append("perda por perecibilidade")

                        perda_quebra_estoque = self.processar_quebra_estoque(grupo, evento_quebra)
                        if perda_quebra_estoque > 0:
                            custos_extras += perda_quebra_estoque
                            motivos.append("quebra de estoque por evento")

                        # 8.4: o perecivel retido na estrada e perdido
                        perda_retencao = perdas_retencao.get(grupo.id, Decimal("0"))
                        if perda_retencao > 0:
                            custos_extras += perda_retencao
                            motivos.append("perecivel perdido em entrega retida")

                        custo_armazenagem_mp = self.calcular_custo_armazenagem_mp(grupo)
                        if custo_armazenagem_mp > 0:
                            custos_extras += custo_armazenagem_mp
                            motivos.append("armazenagem de materia-prima")

                        custo_armazenagem_produtos = self.calcular_custo_armazenagem_produtos(grupo)
                        if custo_armazenagem_produtos > 0:
                            custos_extras += custo_armazenagem_produtos
                            motivos.append("armazenagem de produtos")

                        if custo_rh_recorrente > 0:
                            custos_extras += custo_rh_recorrente
                            motivos.append("custo recorrente de RH")

                        if custos_extras > 0:
                            grupo.capital -= custos_extras

                        self.atualizar_estoque_total(grupo)
                        grupo.save(update_fields=["capital", "estoque"])

                        rf, _ = ResultadoFinanceiro.objects.get_or_create(
                            grupo=grupo,
                            rodada=rodada.numero,
                        )
                        custos_operacionais = rf.custos
                        rf.receita += receita_vendas + receita_financeira
                        rf.custos += custos_extras
                        rf.saldo_caixa = grupo.capital
                        rf.lucro = rf.receita - rf.custos
                        rf.save()

                        vendidos = int(vendidos_por_grupo.get(grupo.id, 0))
                        ofertados = int(ofertados_por_grupo.get(grupo.id, 0))
                        market_share = (
                            Decimal(vendidos) * Decimal("100") / Decimal(total_vendido_rodada)
                            if total_vendido_rodada > 0
                            else Decimal("0")
                        )
                        atendimento = (
                            Decimal(vendidos) * Decimal("100") / Decimal(ofertados)
                            if ofertados > 0
                            else Decimal("0")
                        )
                        lucro_rodada = rf.lucro

                        anterior = (
                            ConsolidadoRodadaGrupo.objects.filter(
                                grupo=grupo, rodada__lt=rodada.numero
                            )
                            .order_by("-rodada")
                            .first()
                        )
                        insumos = coletar_insumos(
                            grupo=grupo,
                            rodada=rodada.numero,
                            perdas=perda_pereciveis + perda_quebra_estoque + perda_retencao,
                            lucro=rf.lucro,
                            receita=rf.receita,
                            saldo_caixa=rf.saldo_caixa,
                            valor_estoques_anterior=anterior.valor_estoques if anterior else None,
                            valor_operacional_anterior=(
                                anterior.valor_estoques_operacional if anterior else None
                            ),
                        )
                        eixos = calcular_eixos(insumos)

                        metricas[grupo.id] = {
                            "grupo": grupo,
                            "receita_rodada": receita_vendas + receita_financeira,
                            "custos_operacionais": custos_operacionais,
                            "penalidade_sem_submissao": penalidade_sem_submissao,
                            "perda_pereciveis": perda_pereciveis + perda_quebra_estoque + perda_retencao,
                            "custo_armazenagem_mp": custo_armazenagem_mp,
                            "custo_armazenagem_produtos": custo_armazenagem_produtos + custo_rh_recorrente,
                            "custos_totais": rf.custos,
                            "saldo_caixa": rf.saldo_caixa,
                            "ofertados": ofertados,
                            "vendidos": vendidos,
                            "lucro_rodada": lucro_rodada,
                            "market_share": market_share,
                            "atendimento": atendimento,
                            "eixos": eixos,
                            "valor_estoques": insumos["valor_estoques"],
                            "valor_estoques_operacional": insumos["valor_estoques_operacional"],
                        }

                        if motivos:
                            logger.info(
                                "Rodada %s - Grupo %s: receita %s, custos extras %s (%s)",
                                rodada.numero,
                                grupo.nome,
                                receita_vendas + receita_financeira,
                                custos_extras,
                                ", ".join(motivos),
                                extra={"correlation_id": correlation_id, "rodada": rodada.numero},
                            )

                    if metricas:
                        for dados in metricas.values():
                            eixos = dados["eixos"]
                            # pesos podem vir ajustados pelo professor (12.2)
                            score = self.limitar(pontuacao_total(eixos, pesos))

                            IndicadorRodadaGrupo.objects.update_or_create(
                                grupo=dados["grupo"],
                                rodada=rodada.numero,
                                defaults={
                                    "lucro_rodada": dados["lucro_rodada"],
                                    "market_share_percent": dados["market_share"],
                                    "atendimento_demanda_percent": dados["atendimento"],
                                    "eficiencia_estoque_percent": self.limitar(eixos["EE"]),
                                    "score_multicriterio": score,
                                },
                            )
                            ConsolidadoRodadaGrupo.objects.update_or_create(
                                grupo=dados["grupo"],
                                rodada=rodada.numero,
                                defaults={
                                    "eo_percent": self.limitar(eixos["EO"]),
                                    "df_percent": self.limitar(eixos["DF"]),
                                    "sd_percent": self.limitar(eixos["SD"]),
                                    "ds_percent": self.limitar(eixos["DS"]),
                                    "valor_estoques": dados["valor_estoques"],
                                    "valor_estoques_operacional": dados[
                                        "valor_estoques_operacional"
                                    ],
                                    "receita_vendas": dados["receita_rodada"],
                                    "custos_operacionais": dados["custos_operacionais"],
                                    "penalidade_sem_submissao": dados["penalidade_sem_submissao"],
                                    "perda_pereciveis": dados["perda_pereciveis"],
                                    "custo_armazenagem_mp": dados["custo_armazenagem_mp"],
                                    "custo_armazenagem_produtos": dados["custo_armazenagem_produtos"],
                                    "custos_totais": dados["custos_totais"],
                                    "lucro_rodada": dados["lucro_rodada"],
                                    "saldo_caixa": dados["saldo_caixa"],
                                    "total_ofertado": dados["ofertados"],
                                    "total_vendido": dados["vendidos"],
                                    "market_share_percent": dados["market_share"],
                                    "atendimento_demanda_percent": dados["atendimento"],
                                    "eficiencia_estoque_percent": self.limitar(eixos["EE"]),
                                    "score_multicriterio": score,
                                },
                            )

                    # 11.3.f "Preparacao da Nova Rodada": a MP pedida agora
                    # chega na rodada seguinte (7.3). Entra depois da
                    # armazenagem e dos indicadores, senao a rodada que fecha
                    # pagaria estoque que ainda nao existia nela.
                    for grupo in grupos:
                        processar_recebimentos_materia_prima(
                            grupo, rodada.numero + 1, rodada_evento=rodada.numero
                        )

                    rodada.fechada = True
                    rodada.save(update_fields=["fechada"])
                    logger.info(
                        "Rodada %s fechada",
                        rodada.numero,
                        extra={"correlation_id": correlation_id, "rodada": rodada.numero},
                    )

                job.status = "sucesso"
                job.detalhes = "Rodada fechada com sucesso."
                job.finalizado_em = timezone.now()
                job.save(update_fields=["status", "detalhes", "finalizado_em"])
        except Exception as exc:
            if job is None:
                raise
            job.status = "falha"
            job.detalhes = str(exc)
            job.finalizado_em = timezone.now()
            job.save(update_fields=["status", "detalhes", "finalizado_em"])
            logger.exception("Falha no fechamento de rodadas", extra={"correlation_id": correlation_id})
            raise
