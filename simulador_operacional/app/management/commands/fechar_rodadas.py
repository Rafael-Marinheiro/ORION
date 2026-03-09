import logging
import random
from collections import defaultdict
from decimal import Decimal
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

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
EVENTO_COOLDOWN_RODADAS = 2
CUSTO_OPERADOR_POR_RODADA = Decimal("2000")
RETENCAO_PADRAO_PERCENT = Decimal("50")


class Command(BaseCommand):
    help = "Fecha rodadas cujo prazo se encerrou"

    @staticmethod
    def obter_evento_rodada(rodada_numero, jogo_id=None):
        base_qs = EventoRodada.objects.select_related("evento")
        if jogo_id:
            base_qs = base_qs.filter(jogo_id=jogo_id)
        else:
            base_qs = base_qs.filter(jogo__isnull=True)

        existente = base_qs.filter(rodada=rodada_numero).first()
        if existente:
            return existente.evento

        eventos = list(Evento.objects.all())
        if not eventos:
            return None

        rodadas_bloqueadas = [
            rodada_numero - i for i in range(1, EVENTO_COOLDOWN_RODADAS + 1) if rodada_numero - i > 0
        ]
        bloqueados = set(base_qs.filter(rodada__in=rodadas_bloqueadas).values_list("evento_id", flat=True))
        candidatos = [evento for evento in eventos if evento.id not in bloqueados] or eventos

        escolhido = random.choice(candidatos)
        EventoRodada.objects.create(rodada=rodada_numero, jogo_id=jogo_id, evento=escolhido)
        return escolhido

    @staticmethod
    def obter_evento_estado_ativo(rodada_numero, jogo_id, efeito_estado):
        historico = EventoRodada.objects.filter(rodada__lte=rodada_numero).select_related("evento")
        if jogo_id:
            historico = historico.filter(jogo_id=jogo_id)
        else:
            historico = historico.filter(jogo__isnull=True)
        for evento_rodada in historico.order_by("-rodada"):
            evento = evento_rodada.evento
            if evento.modo_aplicacao != "estado" or evento.efeito_estado != efeito_estado:
                continue
            fim_vigencia = evento_rodada.rodada + max(evento.duracao_rodadas, 1) - 1
            if rodada_numero <= fim_vigencia:
                return evento
        return None

    @staticmethod
    def calcular_custo_armazenagem_mp(grupo):
        total_valor = Decimal("0")
        estoques = EstoqueMateriaPrima.objects.filter(grupo=grupo).select_related("materia_prima")
        for estoque in estoques:
            total_valor += estoque.quantidade_kg * estoque.materia_prima.preco_unitario
        return total_valor * Decimal("0.02")

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
        return total_valor * Decimal("0.02")

    @staticmethod
    def processar_perecibilidade(grupo, rodada_numero):
        perda_total = Decimal("0")
        lotes = EstoqueProduto.objects.filter(
            grupo=grupo,
            produto__perecivel=True,
            quantidade__gt=0,
        ).select_related("produto")
        for lote in lotes:
            validade = lote.produto.validade_rodadas or 1
            if rodada_numero >= lote.rodada_entrada + validade:
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
        padrao = {
            "lucro": Decimal("0.4"),
            "market_share": Decimal("0.3"),
            "atendimento": Decimal("0.2"),
            "eficiencia_estoque": Decimal("0.1"),
        }
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
    def normalizar_lucro(lucro, lucro_min, lucro_max):
        if lucro_max == lucro_min:
            return Decimal("100")
        return (lucro - lucro_min) * Decimal("100") / (lucro_max - lucro_min)

    @staticmethod
    def obter_demanda_base(cidade, produto):
        demanda = DemandaCidadeProduto.objects.filter(cidade=cidade, produto=produto).first()
        if demanda:
            return int(demanda.demanda_maxima)
        return int(cidade.demanda)

    @staticmethod
    def fator_marketing(grupo, cidade, rodada_numero):
        total_marketing = (
            Investimento.objects.filter(
                grupo=grupo,
                categoria="marketing",
                cidade=cidade,
                rodada_ativacao__lte=rodada_numero,
            )
            .aggregate(total=Sum("valor"))
            .get("total")
            or Decimal("0")
        )
        config = GameConfig.objects.order_by("id").first()
        regras = config.regra_eventos if config and isinstance(config.regra_eventos, dict) else {}
        marketing_cfg = regras.get("marketing", {}) if isinstance(regras.get("marketing", {}), dict) else {}
        base_valor = Decimal(str(marketing_cfg.get("base_valor", 10000)))
        ganho_por_base = Decimal(str(marketing_cfg.get("ganho_por_base", 0.02)))
        max_fator = Decimal(str(marketing_cfg.get("max_fator", 1.30)))
        if base_valor <= 0:
            base_valor = Decimal("10000")
        fator = Decimal("1") + (Decimal(total_marketing) / base_valor) * ganho_por_base
        return min(fator, max_fator)

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

    def processar_vendas_por_demanda(self, rodada, grupos_ids, evento):
        rodada_numero = rodada.numero
        jogo_id = rodada.jogo_id
        MarketShareCidadeProduto.objects.filter(rodada=rodada_numero, grupo_id__in=grupos_ids).delete()

        evento_retencao = self.obter_evento_estado_ativo(
            rodada_numero=rodada_numero,
            jogo_id=jogo_id,
            efeito_estado="retencao_entrega",
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
            }

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
            if evento and evento.modo_aplicacao == "percentual" and evento.tipo == "demanda":
                demanda = int(
                    Decimal(demanda)
                    * (Decimal("1") + Decimal(evento.impacto_percentual) / Decimal("100"))
                )
            if evento_retencao:
                reducao = abs(Decimal(evento_retencao.impacto_percentual))
                if reducao <= 0:
                    reducao = RETENCAO_PADRAO_PERCENT
                demanda = int(Decimal(demanda) * (Decimal("1") - reducao / Decimal("100")))
            demanda = max(demanda, 0)

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
                fator_marketing = self.fator_marketing(envio.grupo, cidade, rodada_numero)
                score = peso_preco * Decimal(envio.quantidade) * fator_marketing
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
        }

    def handle(self, *args, **options):
        correlation_id = uuid4().hex[:16]
        job = ExecucaoJob.objects.create(
            comando="fechar_rodadas",
            correlation_id=correlation_id,
            status="sucesso",
            detalhes="",
        )
        try:
            agora = timezone.now()
            rodadas = Rodada.objects.filter(fechada=False, fim__lte=agora).order_by("numero")
            if not rodadas:
                logger.info("Nenhuma rodada para fechar em %s", agora, extra={"correlation_id": correlation_id})
                self.stdout.write("Nenhuma rodada para fechar")

            config = GameConfig.objects.order_by("id").first()
            pesos = self.obter_pesos_ranking(config.ranking_pesos if config else None)

            for rodada in rodadas:
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
                evento = self.obter_evento_rodada(rodada.numero, jogo_id=rodada.jogo_id)
                stats_venda = self.processar_vendas_por_demanda(
                    rodada=rodada,
                    grupos_ids=grupos_ids,
                    evento=evento,
                )

                receitas_por_grupo = stats_venda["receitas_por_grupo"]
                vendidos_por_grupo = stats_venda["vendidos_por_grupo"]
                ofertados_por_grupo = stats_venda["ofertados_por_grupo"]
                total_vendido_rodada = stats_venda["total_vendido_rodada"]

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
                        penalidade_sem_submissao = grupo.capital * Decimal("0.10")
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
                    eficiencia = (
                        Decimal(vendidos) * Decimal("100") / Decimal(vendidos + grupo.estoque)
                        if (vendidos + grupo.estoque) > 0
                        else Decimal("0")
                    )
                    lucro_rodada = rf.lucro

                    metricas[grupo.id] = {
                        "grupo": grupo,
                        "receita_rodada": receita_vendas + receita_financeira,
                        "custos_operacionais": custos_operacionais,
                        "penalidade_sem_submissao": penalidade_sem_submissao,
                        "perda_pereciveis": perda_pereciveis + perda_quebra_estoque,
                        "custo_armazenagem_mp": custo_armazenagem_mp,
                        "custo_armazenagem_produtos": custo_armazenagem_produtos + custo_rh_recorrente,
                        "custos_totais": rf.custos,
                        "saldo_caixa": rf.saldo_caixa,
                        "ofertados": ofertados,
                        "vendidos": vendidos,
                        "lucro_rodada": lucro_rodada,
                        "market_share": market_share,
                        "atendimento": atendimento,
                        "eficiencia": eficiencia,
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
                    lucros = [dados["lucro_rodada"] for dados in metricas.values()]
                    lucro_min = min(lucros)
                    lucro_max = max(lucros)

                    for dados in metricas.values():
                        lucro_norm = self.normalizar_lucro(dados["lucro_rodada"], lucro_min, lucro_max)
                        score = (
                            lucro_norm * pesos["lucro"]
                            + dados["market_share"] * pesos["market_share"]
                            + dados["atendimento"] * pesos["atendimento"]
                            + dados["eficiencia"] * pesos["eficiencia_estoque"]
                        )

                        IndicadorRodadaGrupo.objects.update_or_create(
                            grupo=dados["grupo"],
                            rodada=rodada.numero,
                            defaults={
                                "lucro_rodada": dados["lucro_rodada"],
                                "market_share_percent": dados["market_share"],
                                "atendimento_demanda_percent": dados["atendimento"],
                                "eficiencia_estoque_percent": dados["eficiencia"],
                                "score_multicriterio": score,
                            },
                        )
                        ConsolidadoRodadaGrupo.objects.update_or_create(
                            grupo=dados["grupo"],
                            rodada=rodada.numero,
                            defaults={
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
                                "eficiencia_estoque_percent": dados["eficiencia"],
                                "score_multicriterio": score,
                            },
                        )

                rodada.fechada = True
                rodada.save(update_fields=["fechada"])
                logger.info(
                    "Rodada %s fechada",
                    rodada.numero,
                    extra={"correlation_id": correlation_id, "rodada": rodada.numero},
                )

            job.status = "sucesso"
            job.detalhes = "Execucao concluida com sucesso."
        except Exception as exc:
            job.status = "falha"
            job.detalhes = str(exc)
            logger.exception("Falha no fechamento de rodadas", extra={"correlation_id": correlation_id})
            raise
        finally:
            job.finalizado_em = timezone.now()
            job.save(update_fields=["status", "detalhes", "finalizado_em"])
