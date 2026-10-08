from collections import defaultdict
import random
import os
import csv
import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView, ListView, TemplateView, UpdateView
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .geografia import CIDADE_SEDE, montar_mapa, ponto_da_praca
from .parametros import (
    CUSTO_ARMAZENAGEM_PERCENT,
    PERCENTUAL_PENALIDADE_SEM_SUBMISSAO,
    CUSTO_MAQUINA,
    CUSTO_OPERADOR_POR_RODADA,
    OPERADORES_POR_MAQUINA,
    MAQUINAS_INICIAIS_POR_PRODUTO,
    TAXA_APLICACAO_FINANCEIRA_RODADA,
)
from .services.dre import montar_dre, montar_fluxo_de_caixa, resumo_do_fluxo
from .services.eventos import (
    custo_da_oferta,
    evento_de_decisao,
    evento_estado_ativo,
    registrar_decisao,
    sortear_evento,
)
from .services.estoque import (
    adicionar_estoque_produto,
    consumir_materia_prima_para_producao,
    estoque_disponivel_produto,
)
from .services.producao import garantir_capacidades_grupo
from .services.investimentos import impedimento_para_investir, limite_de_expansao
from .services.logistica import calcular_frete, calcular_frete_materia_prima, peso_do_envio
from .services.marketing import fator_marketing
from .services.perecibilidade import risco_de_perda_de_estoque
from .services.suprimentos import limite_de_compra
from .services.pontuacao import (
    ordenar_classificacao,
    pares_com_operacao,
    satisfacao_por_praca,
)
from .services.relatorios_dashboard import montar_painel as montar_painel_financeiro
from .forms import (
    ConfigWizardStep1Form,
    ConfigWizardStep2Form,
    CompraMateriaPrimaForm,
    CustomUserCreationForm,
    DecisaoForm,
    DistribuicaoForm,
    GameConfigForm,
    GrupoCadastroForm,
    GrupoForm,
    FeedbackForm,
    InvestimentoForm,
    MembroFormSet,
    ProducaoForm,
    ResultadoFilterForm,
    RodadaForm,
)
from .models import (
    AplicacaoFinanceiraGrupo,
    AuditoriaSubmissaoRodada,
    CapacidadeProdutoGrupo,
    DecisaoEventoGrupo,
    CEOGrupoRodada,
    Cidade,
    ConsolidadoRodadaGrupo,
    DemandaCidadeProduto,
    CompraMateriaPrima,
    ComposicaoProduto,
    Decisao,
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
    Jogo,
    MarketShareCidadeProduto,
    MateriaPrima,
    Producao,
    Produto,
    ResultadoFinanceiro,
    Rodada,
    User,
)
from .serializers import (
    AplicacaoFinanceiraGrupoSerializer,
    AuditoriaSubmissaoRodadaSerializer,
    CapacidadeProdutoGrupoSerializer,
    CEOGrupoRodadaSerializer,
    CidadeSerializer,
    ConsolidadoRodadaGrupoSerializer,
    DemandaCidadeProdutoSerializer,
    CompraMateriaPrimaSerializer,
    ComposicaoProdutoSerializer,
    DecisaoSerializer,
    DistribuicaoSerializer,
    EstoqueMateriaPrimaSerializer,
    EstoqueProdutoSerializer,
    EventoRodadaSerializer,
    EventoSerializer,
    ExecucaoJobSerializer,
    GameConfigSerializer,
    GrupoSerializer,
    IndicadorRodadaGrupoSerializer,
    InvestimentoSerializer,
    JogoSerializer,
    MarketShareCidadeProdutoSerializer,
    MateriaPrimaSerializer,
    ProducaoSerializer,
    ProdutoSerializer,
    ResultadoFinanceiroSerializer,
    RodadaSerializer,
)

# Fornecedores por materia-prima, nas pracas da regiao (sede em Currais
# Novos/RN). O 7.1 lista fornecedores nacionais; a troca para a regiao e
# decisao do dono do projeto, registrada no guia (D9). Cada MP tem ao menos
# um fornecedor perto e um longe, para a escolha continuar sendo uma decisao
# logistica e nao um detalhe.
# 7.1, tabela "Tipos, Custos Iniciais e Localizacao dos Fornecedores".
# Sem acento porque `fornecedor_valido_para_mp` normaliza o nome da cidade
# antes de comparar.
MATERIA_PRIMA_FORNECEDORES = {
    "MP1": {"Fortaleza", "Maceio"},
    "MP2": {"Recife", "Porto Alegre"},
    "MP3": {"Rio de Janeiro", "Aracaju", "Belem"},
    "MP4": {"Sao Paulo", "Joao Pessoa", "Goiania"},
}


def obter_ip_origem(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def obter_ceo_rodada(grupo, rodada_numero):
    registro = CEOGrupoRodada.objects.filter(grupo=grupo, rodada=rodada_numero).select_related("usuario").first()
    if registro:
        return registro.usuario

    ceo = grupo.membros.filter(tipo_usuario="lider_grupo", status_usuario=True).order_by("id_usuario").first()
    if ceo:
        return ceo
    return grupo.membros.filter(status_usuario=True).order_by("id_usuario").first()


def obter_demanda_cidade_produto(cidade, produto):
    demanda = DemandaCidadeProduto.objects.filter(cidade=cidade, produto=produto).first()
    if demanda:
        return int(demanda.demanda_maxima)
    return int(cidade.demanda)


def calcular_fator_marketing(grupo, cidade, rodada_numero):
    """Mc do 14.1.1. Fica em `services.marketing`, unico para view e fechamento."""
    return fator_marketing(grupo, cidade, rodada_numero)


def peso_produtos_remetidos(grupo, cidade, rodada_numero):
    """Peso remetido para a cidade, em kg -- limita o desconto do §7.2.1.

    O desconto e frete de RETORNO: conta quantas viagens levaram produto
    para la e podem voltar carregadas com a MP. Por isso a medida e peso, e
    nao unidades -- uma unidade de A pesa 300 kg e uma de C, 650 (6.1).
    """
    envios = Distribuicao.objects.filter(
        grupo=grupo, cidade=cidade, rodada=rodada_numero
    ).select_related("produto")
    return sum((peso_do_envio(envio.produto, envio.quantidade) for envio in envios), Decimal("0"))


def obter_aplicacao_financeira_grupo(grupo):
    return AplicacaoFinanceiraGrupo.objects.get_or_create(
        grupo=grupo,
        defaults={"saldo_aplicado": Decimal("0"), "taxa_juros_rodada": TAXA_APLICACAO_FINANCEIRA_RODADA},
    )[0]


def obter_grupo_do_usuario(user):
    return user.grupos.select_related("jogo").first()


def obter_rodada_ativa(grupo=None):
    agora = timezone.now()
    rodadas = Rodada.objects.filter(fechada=False, fim__gt=agora)
    if grupo:
        if grupo.jogo_id:
            rodadas = rodadas.filter(jogo_id=grupo.jogo_id)
        else:
            rodadas = rodadas.filter(jogo__isnull=True)
    return rodadas.order_by("numero").first()


def normalizar_nome_cidade(nome):
    return (
        nome.replace("ã", "a")
        .replace("á", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def fornecedor_valido_para_mp(materia_prima, cidade):
    permitidas = MATERIA_PRIMA_FORNECEDORES.get(materia_prima.codigo, set())
    if not permitidas:
        return True
    nome_cidade = normalizar_nome_cidade(cidade.nome)
    return nome_cidade in permitidas


def capacidade_disponivel_produto_rodada(grupo, produto, rodada_numero):
    capacidade, _ = CapacidadeProdutoGrupo.objects.get_or_create(
        grupo=grupo,
        produto=produto,
        defaults={
            "maquinas": MAQUINAS_INICIAIS_POR_PRODUTO.get(produto.codigo, 0),
            "operadores": MAQUINAS_INICIAIS_POR_PRODUTO.get(produto.codigo, 0) * 2,
            "minutos_por_maquina": 400,
        },
    )
    capacidade_total = capacidade.capacidade_unidades_rodada
    produzido = (
        Producao.objects.filter(grupo=grupo, produto=produto, rodada=rodada_numero)
        .aggregate(total=Sum("quantidade_produzida"))
        .get("total")
        or 0
    )
    return max(capacidade_total - int(produzido), 0), capacidade_total


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if getattr(user, "tipo_usuario", None) == "gamemaster" or user.is_superuser:
            return reverse_lazy("game_config")
        return reverse_lazy("painel_grupo")


class HomeView(TemplateView):
    template_name = "home.html"


class AjudaView(TemplateView):
    template_name = "ajuda.html"

    def get_context_data(self, **kwargs):
        """As caracteristicas dos produtos, do 6.1, 6.2, 6.4 e 13.3.

        Elas nao apareciam em tela nenhuma. Ficam aqui, no manual, e nao em
        aviso durante a decisao: conhecer o produto e o efeito da escolha e
        parte do que se avalia, entao a regra tem que estar disponivel a
        todos, antes, e nao sussurrada a quem ja errou.

        Lidas do banco, nao escritas a mao: o 6.1 avisa que os precos de MP
        "sao parametrizaveis e podem variar entre rodadas", e uma tabela fixa
        no template envelheceria na primeira alteracao do professor.
        """
        context = super().get_context_data(**kwargs)
        context["nav"] = "ajuda"
        context["produtos"] = (
            Produto.objects.filter(ativo=True)
            .prefetch_related("composicoes__materia_prima")
            .order_by("codigo")
        )
        context["custo_armazenagem_percent"] = CUSTO_ARMAZENAGEM_PERCENT
        return context



class FeedbackView(LoginRequiredMixin, FormView):
    """A sugestao vira uma linha no roadmap, entao pede login.

    A tela estava aberta: qualquer visitante da internet podia gravar texto
    num arquivo do servidor, sem limite de envios e sem deixar quem foi. O
    campo tambem aceitava quebras de linha, que no markdown do roadmap viram
    varios itens -- da para forjar uma lista inteira num envio so.
    """

    template_name = 'feedback.html'
    form_class = FeedbackForm
    success_url = reverse_lazy('feedback')

    def form_valid(self, form):
        suggestion = ' '.join(form.cleaned_data['suggestion'].split())
        email = form.cleaned_data.get('email')
        line = f"- {suggestion}"
        if email:
            line += f" (contato: {email})"
        line += f" - {timezone.now().date()}\n"
        default_path = settings.BASE_DIR / "docs" / "roadmap.md"
        roadmap_path = getattr(settings, "ROADMAP_FILE", default_path)
        roadmap_path.parent.mkdir(parents=True, exist_ok=True)
        with open(roadmap_path, 'a+', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)
            if f.tell() > 0:
                f.seek(f.tell() - 1)
                if f.read(1) != "\n":
                    f.write("\n")
            f.write(line)
        messages.success(self.request, 'Obrigado pelo feedback!')
        return super().form_valid(form)

class RegisterView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = "registration/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    raise_exception = True

    def test_func(self):
        return getattr(self.request.user, 'tipo_usuario', '') == 'gamemaster'


class CustomPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


class GameConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = GameConfig
    form_class = GameConfigForm
    template_name = "game_config_form.html"
    success_url = reverse_lazy("home")
    permission_required = "app.change_gameconfig"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_object(self, queryset=None):
        """A configuracao da turma escolhida, nao a de id 1.

        Cada Jogo tem a sua `GameConfig`, e o fechamento le a do jogo da
        rodada. A tela editava sempre a de id 1: com duas turmas no sistema,
        o professor mudava o capital ou os pesos do 12.4, salvava, e a turma
        dele continuava igual -- sem nenhum aviso de que a escrita foi para
        outro lugar.
        """
        jogo_id, _sem_jogo, opcoes = turma_em_foco(self.request)
        self.turmas = opcoes
        jogo = (
            Jogo.objects.select_related("config").filter(id=jogo_id).first()
            if jogo_id
            else None
        )
        self.jogo = jogo
        if jogo:
            return jogo.config
        obj, _ = GameConfig.objects.get_or_create(id=1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turmas"] = getattr(self, "turmas", [])
        context["turma_em_foco"] = next(
            (opcao["nome"] for opcao in context["turmas"] if opcao["selecionada"]),
            None,
        )
        return context

    def get_success_url(self):
        destino = reverse("game_config")
        jogo = getattr(self, "jogo", None)
        return f"{destino}?jogo={jogo.id}" if jogo else destino

    def form_valid(self, form):
        form.instance.produtos_habilitados = form.cleaned_data["produtos_habilitados"]
        alvo = getattr(self, "jogo", None)
        messages.success(
            self.request,
            "Parâmetros salvos"
            + (f" para a turma {alvo.nome}." if alvo else " para os grupos sem turma."),
        )
        return super().form_valid(form)


class GameConfigWizardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "game_config_wizard.html"
    permission_required = "app.change_gameconfig"
    session_key = "game_config_wizard"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_form_for_step(self, step, data=None, initial=None):
        if step == 1:
            return ConfigWizardStep1Form(data=data, initial=initial)
        if step == 2:
            return ConfigWizardStep2Form(data=data, initial=initial)
        return None

    def get(self, request, *args, **kwargs):
        step = int(request.GET.get("step", 1))
        step = max(1, min(step, 3))
        wizard_data = request.session.get(self.session_key, {})
        config, _ = GameConfig.objects.get_or_create(id=1)
        if step == 1:
            jogo_id, _sem_jogo, _opcoes = turma_em_foco(request)
            alvo = Jogo.objects.select_related("config").filter(id=jogo_id).first()
            config = alvo.config if alvo else config
            initial = {
                "jogo": str(alvo.id) if alvo else "",
                "capital_inicial": config.capital_inicial,
                "estoque_inicial": config.estoque_inicial,
                "maquinas_iniciais": config.maquinas_iniciais,
                "numero_rodadas": config.numero_rodadas,
            }
            initial.update(wizard_data.get("step1", {}))
            form = self.get_form_for_step(step, initial=initial)
        elif step == 2:
            initial = {
                "produtos_habilitados": config.produtos_habilitados,
                "modulo_producao": config.modulo_producao,
                "modulo_distribuicao": config.modulo_distribuicao,
                "modulo_financeiro": config.modulo_financeiro,
            }
            initial.update(wizard_data.get("step2", {}))
            form = self.get_form_for_step(step, initial=initial)
        else:
            form = None
        return render(
            request,
            self.template_name,
            {
                "step": step,
                "form": form,
                "dados_step1": wizard_data.get("step1", {}),
                "dados_step2": wizard_data.get("step2", {}),
                "turma_escolhida": self.nome_da_turma(wizard_data),
            },
        )

    @staticmethod
    def nome_da_turma(wizard_data):
        escolhido = (wizard_data.get("step1", {}).get("jogo") or "").strip()
        if not escolhido.isdigit():
            return "Grupos sem turma"
        jogo = Jogo.objects.filter(id=escolhido).first()
        return jogo.nome if jogo else "Grupos sem turma"

    def post(self, request, *args, **kwargs):
        step = int(request.POST.get("step", 1))
        step = max(1, min(step, 3))
        wizard_data = request.session.get(self.session_key, {})

        if "voltar" in request.POST and step > 1:
            return redirect(f"{reverse_lazy('game_config_wizard')}?step={step-1}")

        if step in {1, 2}:
            form = self.get_form_for_step(step, data=request.POST)
            if not form.is_valid():
                return render(
                    request,
                    self.template_name,
                    {
                        "step": step,
                        "form": form,
                        "dados_step1": wizard_data.get("step1", {}),
                        "dados_step2": wizard_data.get("step2", {}),
                        "turma_escolhida": self.nome_da_turma(wizard_data),
                    },
                )
            # A sessao serializa em JSON e JSON nao conhece Decimal, entao
            # cleaned_data e normalizado aqui, no unico ponto onde entra.
            wizard_data[f"step{step}"] = json.loads(
                json.dumps(form.cleaned_data, cls=DjangoJSONEncoder)
            )
            request.session[self.session_key] = wizard_data
            return redirect(f"{reverse_lazy('game_config_wizard')}?step={step+1}")

        if step == 3 and "confirmar" in request.POST:
            dados_step1 = wizard_data.get("step1", {})
            dados_step2 = wizard_data.get("step2", {})
            if not dados_step1 or not dados_step2:
                messages.error(request, "Wizard incompleto. Preencha as etapas anteriores.")
                return redirect(f"{reverse_lazy('game_config_wizard')}?step=1")
            # A turma escolhida no passo 1 manda: cada jogo tem a sua
            # configuracao, e gravar sempre na de id 1 mudava outro jogo.
            escolhido = (dados_step1.get("jogo") or "").strip()
            alvo = (
                Jogo.objects.select_related("config").filter(id=escolhido).first()
                if escolhido.isdigit()
                else None
            )
            if alvo:
                config = alvo.config
            else:
                config, _ = GameConfig.objects.get_or_create(id=1)
            config.capital_inicial = dados_step1["capital_inicial"]
            config.estoque_inicial = dados_step1["estoque_inicial"]
            config.maquinas_iniciais = dados_step1["maquinas_iniciais"]
            config.numero_rodadas = dados_step1["numero_rodadas"]
            config.produtos_habilitados = dados_step2.get("produtos_habilitados") or ""
            config.modulo_producao = dados_step2.get("modulo_producao", False)
            config.modulo_distribuicao = dados_step2.get("modulo_distribuicao", False)
            config.modulo_financeiro = dados_step2.get("modulo_financeiro", False)
            config.save()
            request.session.pop(self.session_key, None)
            messages.success(
                request,
                "Configuração salva"
                + (f" para a turma {alvo.nome}." if alvo else " para os grupos sem turma."),
            )
            destino = reverse("game_config")
            return redirect(f"{destino}?jogo={alvo.id}" if alvo else destino)

        return redirect(f"{reverse_lazy('game_config_wizard')}?step={step}")


class RodadaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Rodada
    form_class = RodadaForm
    template_name = "rodada_form.html"
    success_url = reverse_lazy("home")
    permission_required = "app.add_rodada"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    @staticmethod
    def estado_das_turmas():
        """Em que pe esta cada turma: proxima rodada e pendencia.

        A professora abria a rodada digitando o numero de cabeca. O sistema
        ja sabe qual e a proxima -- e sabe tambem quando a anterior ainda
        nao fechou, que e o caso em que abrir outra so embaralha a aula.
        """
        estados = []
        jogos = list(Jogo.objects.select_related("config").order_by("nome"))
        avulsos = Grupo.objects.filter(jogo__isnull=True).exists()

        for jogo in jogos + ([None] if avulsos else []):
            rodadas = Rodada.objects.filter(jogo=jogo) if jogo else Rodada.objects.filter(jogo__isnull=True)
            ultima = rodadas.order_by("-numero").first()
            aberta = rodadas.filter(fechada=False).order_by("numero").first()
            config = jogo.config if jogo else GameConfig.objects.filter(pk=1).first()
            total = config.numero_rodadas if config else 0
            estados.append(
                {
                    "valor": str(jogo.id) if jogo else "",
                    "nome": jogo.nome if jogo else "Grupos sem turma",
                    "proxima": (ultima.numero + 1) if ultima else 1,
                    "total": total,
                    "pendente": aberta.numero if aberta else None,
                    "encerrada": bool(total) and bool(ultima) and ultima.numero >= total,
                }
            )
        return estados

    def get_initial(self):
        """Abre ja na turma que esta jogando, com a proxima rodada dela."""
        inicial = super().get_initial()
        jogo_id, _sem_jogo, _opcoes = turma_em_foco(self.request)
        estados = {estado["valor"]: estado for estado in self.estado_das_turmas()}
        escolhido = estados.get(str(jogo_id) if jogo_id else "")
        if escolhido:
            inicial.setdefault("jogo", jogo_id)
            inicial.setdefault("numero", escolhido["proxima"])
        return inicial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado_turmas"] = self.estado_das_turmas()
        return context

    @staticmethod
    def registrar_evento_manual(form, rodada):
        """Grava o evento que o professor determinou para a rodada.

        O 8.2 sorteia um evento por rodada. Quando o professor escolhe o
        evento, o sorteio e desligado -- a menos que ele peca os dois, e ai
        a rodada tem o dele MAIS o sorteado.

        Isto e a RN-10 do 5, que estava AUSENTE ate 25/09/2026: "a cada
        rodada, o sistema pode ativar ate 2 eventos aleatorios simultaneos.
        A ativacao e definida pelo moderador ou aleatoriamente, conforme
        configuracao" -- e "os eventos aleatorios sao informados na abertura
        da rodada", que e onde este formulario vive. A decisao B4
        (2026-09-18) escolheu o 8.2 para o SORTEIO; a ativacao pelo
        moderador e outra coisa, e continua valendo.
        """
        dados = form.cleaned_data
        if not dados.get("adicionar_evento"):
            return None

        if (dados.get("origem_evento") or "catalogo") == "catalogo":
            evento = dados["evento_existente"]
        else:
            evento = Evento.objects.create(
                nome=dados["evento_nome"],
                frase_indicativa=dados.get("evento_frase") or dados["evento_nome"],
                descricao=dados.get("evento_frase") or "",
                tipo=dados["evento_tipo"],
                modo_aplicacao=dados.get("evento_medida") or "percentual",
                impacto_percentual=(
                    int(form.efeito_do_evento())
                    if dados.get("evento_medida") != "absoluto"
                    else 0
                ),
                valor_absoluto=(
                    form.efeito_do_evento()
                    if dados.get("evento_medida") == "absoluto"
                    else None
                ),
                # Fora do sorteio: acontece porque foi mandado.
                probabilidade=0,
                manual=True,
                jogo=rodada.jogo,
            )
            evento.cidades.set(dados.get("evento_cidades") or [])

        EventoRodada.objects.get_or_create(
            rodada=rodada.numero,
            jogo=rodada.jogo,
            evento=evento,
            defaults={"manual": True},
        )
        if not dados.get("evento_com_sorteio"):
            rodada.sorteio_evento = False
            rodada.save(update_fields=["sorteio_evento"])
        return evento

    def form_valid(self, form):
        fim = form.cleaned_data["fim"]
        if fim <= timezone.now():
            form.add_error("fim", "A data de encerramento deve estar no futuro.")
            return self.form_invalid(form)

        jogo = form.cleaned_data.get("jogo")
        abertas = Rodada.objects.filter(fechada=False, fim__gt=timezone.now())
        if jogo:
            abertas = abertas.filter(jogo=jogo)
        else:
            abertas = abertas.filter(jogo__isnull=True)

        if abertas.exists():
            form.add_error(None, "Ja existe uma rodada ativa para este jogo.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        rodada = self.object
        self.registrar_evento_manual(form, rodada)
        grupos = Grupo.objects.all()
        if rodada.jogo_id:
            grupos = grupos.filter(jogo_id=rodada.jogo_id)
        else:
            grupos = grupos.filter(jogo__isnull=True)
        for grupo in grupos:
            if CEOGrupoRodada.objects.filter(grupo=grupo, rodada=rodada.numero).exists():
                continue
            ceo = grupo.membros.filter(tipo_usuario="lider_grupo", status_usuario=True).order_by("id_usuario").first()
            if not ceo:
                ceo = grupo.membros.filter(status_usuario=True).order_by("id_usuario").first()
            if ceo:
                CEOGrupoRodada.objects.create(grupo=grupo, rodada=rodada.numero, usuario=ceo)
        return response


class GerenciamentoJogoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Acompanha a submissão das decisões nas rodadas ainda abertas."""

    template_name = "gerenciamento_jogo.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agora = timezone.now()
        # Toda rodada ainda nao fechada, inclusive a de prazo vencido: o
        # 11.1 manda o fechamento acontecer "no momento exato do
        # prazo-limite", e e o servico automatico que o executa. Filtrar por
        # `fim__gt=agora` fazia a rodada sumir da tela no instante do prazo
        # -- se o servico estivesse parado, o professor via "nao ha rodadas
        # abertas" e nada mais.
        rodadas = Rodada.objects.filter(
            fechada=False
        ).select_related("jogo").order_by("jogo__nome", "numero")
        paineis = []

        for rodada in rodadas:
            grupos = Grupo.objects.filter(
                jogo_id=rodada.jogo_id
            ).order_by("nome") if rodada.jogo_id else Grupo.objects.filter(
                jogo__isnull=True
            ).order_by("nome")
            ceos = {
                ceo.grupo_id: ceo
                for ceo in CEOGrupoRodada.objects.filter(
                    grupo__in=grupos, rodada=rodada.numero
                ).select_related("usuario")
            }
            auditorias = {}
            for auditoria in AuditoriaSubmissaoRodada.objects.filter(
                grupo__in=grupos, rodada=rodada.numero
            ).select_related("usuario").order_by("grupo_id", "-data_registro"):
                auditorias.setdefault(auditoria.grupo_id, auditoria)

            participacoes = [
                {
                    "grupo": grupo,
                    "ceo": ceos.get(grupo.id),
                    "auditoria": auditorias.get(grupo.id),
                }
                for grupo in grupos
            ]
            submetidos = sum(item["auditoria"] is not None for item in participacoes)
            total = len(participacoes)
            paineis.append(
                {
                    "rodada": rodada,
                    "participacoes": participacoes,
                    "submetidos": submetidos,
                    "pendentes": total - submetidos,
                    "total": total,
                    "percentual": round(100 * submetidos / total) if total else 0,
                    "vencida": rodada.fim <= agora,
                }
            )

        context["paineis"] = paineis
        context["penalidade_percent"] = PERCENTUAL_PENALIDADE_SEM_SUBMISSAO * 100
        context["ultimo_fechamento"] = (
            ExecucaoJob.objects.filter(comando="fechar_rodadas")
            .order_by("-iniciado_em")
            .first()
        )
        return context


def rodada_do_filtro(request):
    """Rodada pedida na querystring, ou None.

    O valor vem do usuario: texto, numero negativo ou rodada inexistente
    viram None. Sem isso, `?rodada=abc` chegava ao ORM e levantava
    ValueError -- HTTP 500 nas quatro exportacoes.
    """
    valor = (request.GET.get("rodada") or "").strip()
    if not valor.isdigit():
        return None
    numero = int(valor)
    return numero if numero > 0 else None


def numeros_de_rodadas_fechadas(jogo_id=None, sem_jogo=False):
    """Numeros das rodadas ja encerradas.

    Resultado de rodada aberta e informacao competitiva: enquanto o prazo
    corre, saber o desempenho alheio muda a decisao de quem ainda nao
    submeteu. Hoje indicadores e consolidados so nascem no fechamento, mas
    as telas nao dependem disso -- filtram por rodada fechada, para a regra
    valer mesmo que algum codigo futuro passe a gravar antes.
    """
    rodadas = Rodada.objects.filter(fechada=True)
    if jogo_id:
        rodadas = rodadas.filter(jogo_id=jogo_id)
    elif sem_jogo:
        rodadas = rodadas.filter(jogo__isnull=True)
    return list(rodadas.values_list("numero", flat=True))


AVULSO = "avulso"


def turma_em_foco(request):
    """Qual turma as telas de ranking mostram para o professor.

    O 12 classifica os grupos DE UM JOGO: equipes de turmas diferentes
    jogaram rodadas diferentes, com eventos diferentes, e somar as duas
    listas nao produz classificacao nenhuma. Ate 25/09/2026 o ranking nao
    filtrava nada para quem e `is_staff`: a tela misturava todas as turmas
    do banco numa lista so, e a rodada de referencia saia da maior rodada
    fechada de qualquer jogo -- podia nem existir na turma do professor,
    que entao nao via as proprias equipes.

    Devolve `(jogo_id, sem_jogo, opcoes)`. `sem_jogo` cobre os grupos
    cadastrados fora de qualquer jogo.
    """
    jogos = list(Jogo.objects.order_by("nome"))
    tem_avulsos = Grupo.objects.filter(jogo__isnull=True).exists()

    escolha = (request.GET.get("jogo") or "").strip()
    jogo_id = None
    sem_jogo = False
    if escolha == AVULSO and tem_avulsos:
        sem_jogo = True
    elif escolha.isdigit() and any(jogo.id == int(escolha) for jogo in jogos):
        jogo_id = int(escolha)
    else:
        # Sem escolha explicita, a turma que esta jogando: a do ultimo
        # periodo aberto ou fechado.
        ultima = Rodada.objects.order_by("-id").first()
        if ultima and ultima.jogo_id:
            jogo_id = ultima.jogo_id
        elif ultima and tem_avulsos:
            sem_jogo = True
        elif jogos:
            jogo_id = jogos[0].id
        elif tem_avulsos:
            sem_jogo = True

    opcoes = [
        {"valor": str(jogo.id), "nome": jogo.nome, "selecionada": jogo.id == jogo_id}
        for jogo in jogos
    ]
    if tem_avulsos:
        opcoes.append(
            {"valor": AVULSO, "nome": "Grupos sem turma", "selecionada": sem_jogo}
        )
    return jogo_id, sem_jogo, opcoes


class RankingView(LoginRequiredMixin, TemplateView):
    template_name = "ranking.html"

    @staticmethod
    def _ordenar_consolidados(consolidados):
        """Aplica os critérios normativos do ranking a uma rodada."""
        return ordenar_classificacao(
            [
                {
                    "grupo": c.grupo,
                    "pontuacao": c.score_multicriterio,
                    "EO": c.eo_percent,
                    "DF": c.df_percent,
                    "EE": c.eficiencia_estoque_percent,
                    "SD": c.sd_percent,
                    "DS": c.ds_percent,
                    "receita": c.receita_vendas,
                    "lucro_rodada": c.lucro_rodada,
                    "market_share": c.market_share_percent,
                    "nome": c.grupo.nome,
                }
                for c in consolidados
            ]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav"] = "ranking"
        # Consolidado, nao Indicador: o desempate do 12.5 precisa de EO, SD,
        # DS e receita bruta, que so existem la.
        indicadores = ConsolidadoRodadaGrupo.objects.select_related("grupo", "grupo__jogo")
        grupo_usuario = None
        rodada_kwargs = {}

        if self.request.user.is_staff:
            # O professor nao pertence a grupo: escolhe a turma na tela.
            jogo_id, sem_jogo, opcoes = turma_em_foco(self.request)
            context["turmas"] = opcoes
            context["turma_em_foco"] = next(
                (opcao["nome"] for opcao in opcoes if opcao["selecionada"]), None
            )
            if jogo_id:
                indicadores = indicadores.filter(grupo__jogo_id=jogo_id)
                rodada_kwargs["jogo_id"] = jogo_id
            elif sem_jogo:
                indicadores = indicadores.filter(grupo__jogo__isnull=True)
                rodada_kwargs["sem_jogo"] = True
        else:
            grupo_usuario = obter_grupo_do_usuario(self.request.user)
            if grupo_usuario and grupo_usuario.jogo_id:
                indicadores = indicadores.filter(grupo__jogo_id=grupo_usuario.jogo_id)
                rodada_kwargs["jogo_id"] = grupo_usuario.jogo_id
            elif grupo_usuario:
                indicadores = indicadores.filter(grupo__jogo__isnull=True)
                rodada_kwargs["sem_jogo"] = True
            else:
                indicadores = indicadores.none()

        rodadas_fechadas = sorted(numeros_de_rodadas_fechadas(**rodada_kwargs))
        indicadores = indicadores.filter(rodada__in=rodadas_fechadas)
        rodada_referencia = indicadores.order_by("-rodada").values_list("rodada", flat=True).first()
        if rodada_referencia:
            ranking = self._ordenar_consolidados(indicadores.filter(rodada=rodada_referencia))
        else:
            ranking = []
            grupos_base = Grupo.objects.order_by("-capital")
            if self.request.user.is_staff:
                if rodada_kwargs.get("jogo_id"):
                    grupos_base = grupos_base.filter(jogo_id=rodada_kwargs["jogo_id"])
                elif rodada_kwargs.get("sem_jogo"):
                    grupos_base = grupos_base.filter(jogo__isnull=True)
            elif grupo_usuario and grupo_usuario.jogo_id:
                grupos_base = grupos_base.filter(jogo_id=grupo_usuario.jogo_id)
            elif grupo_usuario:
                grupos_base = grupos_base.filter(jogo__isnull=True)
            else:
                grupos_base = Grupo.objects.none()
            for grupo in grupos_base:
                ranking.append(
                    {
                        "grupo": grupo,
                        "pontuacao": Decimal("0"),
                        "EO": Decimal("0"),
                        "DF": Decimal("0"),
                        "EE": Decimal("0"),
                        "SD": Decimal("0"),
                        "DS": Decimal("0"),
                        "lucro_rodada": Decimal("0"),
                        # Antes do primeiro fechamento ainda não existe venda
                        # consolidada. A linha existe só para mostrar quem
                        # está no jogo; os destaques ficam de fora.
                        "market_share": Decimal("0"),
                    }
                )

        context["ranking"] = ranking
        context["rodada_referencia"] = rodada_referencia
        # Antes do primeiro fechamento a lista existe so para mostrar quem
        # esta na turma: nao ha rodada medida. Coroar "Lider da rodada" com
        # 0,00 pontos nesse estado anuncia um desempenho que ninguem teve.
        context["sem_rodada_fechada"] = not rodada_referencia
        context["destaques"] = (
            self._destaques_da_rodada(ranking) if rodada_referencia else []
        )
        classificacoes = self._classificacoes_por_rodada(indicadores, rodadas_fechadas)
        # 7.3: a MP so chega na rodada seguinte, entao na rodada 1 ninguem
        # produz nem vende. Apresentar posicao e pontuacao ali seria ordenar
        # equipes por um desempenho que a rodada nao teve como medir.
        grupos_no_ranking = {item["grupo"] for item in ranking}
        grupos_no_ranking.update(
            item["grupo"] for lista in classificacoes.values() for item in lista
        )
        com_operacao = pares_com_operacao(grupos_no_ranking, rodadas_fechadas)

        for item in ranking:
            item["operou"] = (item["grupo"].id, rodada_referencia) in com_operacao
        rodada_operou = any(item["operou"] for item in ranking)
        context["rodada_sem_operacao"] = bool(rodada_referencia) and not rodada_operou
        # Destaque de uma rodada sem operacao seria coroar quem nao jogou.
        if context["rodada_sem_operacao"]:
            context["destaques"] = []
        context["grafico_posicoes"] = self._grafico_posicoes(
            classificacoes, rodadas_fechadas, com_operacao
        )
        context["evolucao_grupo"] = self._evolucao_do_grupo(
            classificacoes, rodadas_fechadas, grupo_usuario, com_operacao
        )
        return context

    def _classificacoes_por_rodada(self, indicadores, rodadas_fechadas):
        """Classificação de cada rodada fechada, com uma consulta só.

        O gráfico de posições e a evolução do grupo percorriam a mesma lista
        filtrando por rodada dentro do laço: duas idas ao banco por rodada
        fechada, e a simulação tem uma rodada por aula.
        """
        por_rodada = defaultdict(list)
        for consolidado in indicadores:
            por_rodada[consolidado.rodada].append(consolidado)
        return {
            rodada: self._ordenar_consolidados(por_rodada.get(rodada, []))
            for rodada in rodadas_fechadas
        }

    def _grafico_posicoes(self, classificacoes, rodadas_fechadas, com_operacao):
        """Converte a classificação de cada rodada em trajetórias por equipe.

        Rodada em que a equipe não operou fica como lacuna: posição ali seria
        ordenar quem não jogou.
        """
        series_por_grupo = {}
        for indice, rodada in enumerate(rodadas_fechadas):
            classificacao = classificacoes.get(rodada, [])
            for posicao, item in enumerate(classificacao, start=1):
                nome = item["grupo"].nome
                if nome not in series_por_grupo:
                    series_por_grupo[nome] = [None] * len(rodadas_fechadas)
                if (item["grupo"].id, rodada) not in com_operacao:
                    continue
                series_por_grupo[nome][indice] = posicao

        return {
            "labels": [f"R{rodada}" for rodada in rodadas_fechadas],
            "series": [
                {"label": nome, "data": posicoes, "type": "line"}
                for nome, posicoes in sorted(series_por_grupo.items())
            ],
        }

    @staticmethod
    def _destaques_da_rodada(ranking):
        if not ranking:
            return []
        maior_lucro = max(ranking, key=lambda item: item["lucro_rodada"])
        maior_market_share = max(ranking, key=lambda item: item["market_share"])
        # `formato` acompanha o dado. Antes a unidade era escolhida no
        # template pela POSICAO na lista (o segundo item virava R$, o
        # terceiro virava %), entao trocar a ordem dos destaques ou omitir
        # um deles trocava a unidade dos outros sem ninguem perceber.
        return [
            {"titulo": "Líder da rodada", "grupo": ranking[0]["grupo"].nome,
             "valor": ranking[0]["pontuacao"], "formato": "pontos"},
            {"titulo": "Maior lucro", "grupo": maior_lucro["grupo"].nome,
             "valor": maior_lucro["lucro_rodada"], "formato": "moeda"},
            {"titulo": "Maior participação de mercado", "grupo": maior_market_share["grupo"].nome,
             "valor": maior_market_share["market_share"], "formato": "percentual"},
        ]

    def _evolucao_do_grupo(self, classificacoes, rodadas_fechadas, grupo_usuario,
                           com_operacao):
        if not grupo_usuario:
            return []
        evolucao = []
        for rodada in rodadas_fechadas:
            ranking = classificacoes.get(rodada, [])
            for posicao, item in enumerate(ranking, start=1):
                if item["grupo"].id == grupo_usuario.id:
                    operou = (grupo_usuario.id, rodada) in com_operacao
                    evolucao.append(
                        {
                            "rodada": rodada,
                            "posicao": posicao if operou else None,
                            "pontuacao": item["pontuacao"] if operou else None,
                            "operou": operou,
                        }
                    )
                    break
        return evolucao


class ClassificacaoFinalView(LoginRequiredMixin, TemplateView):
    """Classificação do ciclo após o encerramento de todas as rodadas."""

    template_name = "classificacao.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # A classificacao final fecha a familia do ranking (RN-12): o menu
        # continua marcando "Ranking" como a secao corrente.
        context["nav"] = "ranking"
        grupo_usuario = obter_grupo_do_usuario(self.request.user)
        if grupo_usuario:
            jogo = grupo_usuario.jogo
        elif self.request.user.is_staff:
            # 10.3 poe "Visualizacao de Ranking Geral" no perfil do
            # administrador, que nao pertence a grupo nenhum -- sem isso a
            # tela nascia vazia justamente para quem ela foi pedida. A turma
            # e a mesma escolhida no ranking por rodada, e a tela diz qual e:
            # antes ela pegava o jogo de maior id, sem avisar.
            jogo_id, _sem_jogo, opcoes = turma_em_foco(self.request)
            jogo = Jogo.objects.filter(id=jogo_id).first() if jogo_id else None
            context["turmas"] = opcoes
            context["turma_em_foco"] = next(
                (opcao["nome"] for opcao in opcoes if opcao["selecionada"]), None
            )
        else:
            context["grupos"] = []
            return context

        if jogo:
            grupos = Grupo.objects.filter(jogo=jogo)
            rodadas = Rodada.objects.filter(jogo=jogo)
            numero_rodadas = jogo.config.numero_rodadas
        else:
            grupos = Grupo.objects.filter(jogo__isnull=True)
            rodadas = Rodada.objects.filter(jogo__isnull=True)
            config = GameConfig.objects.order_by("id").first()
            numero_rodadas = config.numero_rodadas if config else 0

        fechadas = set(rodadas.filter(fechada=True).values_list("numero", flat=True))
        esperadas = set(range(1, numero_rodadas + 1))
        if not numero_rodadas or not esperadas.issubset(fechadas):
            context["grupos"] = []
            return context

        consolidados = ConsolidadoRodadaGrupo.objects.filter(
            grupo__in=grupos, rodada__in=esperadas
        ).select_related("grupo")
        por_grupo = {}
        for consolidado in consolidados:
            dados = por_grupo.setdefault(
                consolidado.grupo_id,
                {
                    "grupo": consolidado.grupo,
                    "pontuacao": Decimal("0"),
                    "EO": Decimal("0"),
                    "DF": Decimal("0"),
                    "EE": Decimal("0"),
                    "SD": Decimal("0"),
                    "DS": Decimal("0"),
                    "receita": Decimal("0"),
                    "nome": consolidado.grupo.nome,
                },
            )
            dados["pontuacao"] += consolidado.score_multicriterio
            dados["EO"] += consolidado.eo_percent
            dados["DF"] += consolidado.df_percent
            dados["EE"] += consolidado.eficiencia_estoque_percent
            dados["SD"] += consolidado.sd_percent
            dados["DS"] += consolidado.ds_percent
            dados["receita"] += consolidado.receita_vendas

        context["grupos"] = ordenar_classificacao(por_grupo.values())
        return context


class PainelGrupoView(LoginRequiredMixin, TemplateView):
    template_name = "painel_grupo.html"

    @staticmethod
    def usuario_pode_submeter(user, grupo, rodada_numero):
        ceo_rodada = obter_ceo_rodada(grupo, rodada_numero)
        return bool(ceo_rodada and ceo_rodada.id_usuario == user.id_usuario)

    def montar_contexto(
        self,
        request,
        grupo,
        form=None,
        envio_form=None,
        producao_form=None,
        compra_mp_form=None,
        investimento_form=None,
    ):
        rodada_ativa = obter_rodada_ativa(grupo) if grupo else None
        if grupo:
            garantir_capacidades_grupo(grupo)
        resultados = grupo.resultados.all() if grupo else ResultadoFinanceiro.objects.none()
        consolidados = (
            ConsolidadoRodadaGrupo.objects.filter(grupo=grupo)
            if grupo
            else ConsolidadoRodadaGrupo.objects.none()
        )
        decisoes = grupo.decisoes.all() if grupo else Decisao.objects.none()
        envios = (
            grupo.envios.select_related("cidade", "produto").all()
            if grupo
            else Distribuicao.objects.none()
        )
        producoes = grupo.producoes.select_related("produto").all() if grupo else Producao.objects.none()
        compras_mp = (
            grupo.compras_materia_prima.select_related("materia_prima", "cidade_fornecedora").all()
            if grupo
            else CompraMateriaPrima.objects.none()
        )
        investimentos = (
            grupo.investimentos.select_related("cidade", "produto").all()
            if grupo
            else Investimento.objects.none()
        )
        saldos_mp = (
            grupo.estoques_materia_prima.select_related("materia_prima").all()
            if grupo
            else EstoqueMateriaPrima.objects.none()
        )
        saldos_produto = (
            grupo.estoques_produto.select_related("produto").all()
            if grupo
            else EstoqueProduto.objects.none()
        )
        capacidades = (
            grupo.capacidades_produto.select_related("produto").all().order_by("produto__codigo")
            if grupo
            else CapacidadeProdutoGrupo.objects.none()
        )
        aplicacao_financeira = obter_aplicacao_financeira_grupo(grupo) if grupo else None
        rodadas_disponiveis = (
            list(Rodada.objects.filter(jogo_id=grupo.jogo_id).order_by("numero"))
            if grupo and grupo.jogo_id
            else []
        )
        numeros_rodadas_disponiveis = {rodada.numero for rodada in rodadas_disponiveis}
        rodada_filtro = request.GET.get("rodada", "")
        rodada_mapa = rodada_ativa.numero if rodada_ativa else None
        if rodada_filtro.isdigit() and int(rodada_filtro) in numeros_rodadas_disponiveis:
            rodada_filtrada = int(rodada_filtro)
            resultados = resultados.filter(rodada=rodada_filtrada)
            consolidados = consolidados.filter(rodada=rodada_filtrada)
            decisoes = decisoes.filter(rodada=rodada_filtrada)
            envios = envios.filter(rodada=rodada_filtrada)
            producoes = producoes.filter(rodada=rodada_filtrada)
            compras_mp = compras_mp.filter(rodada_pedido=rodada_filtrada)
            investimentos = investimentos.filter(rodada=rodada_filtrada)
            rodada_mapa = rodada_filtrada
            saldos_produto = saldos_produto.filter(rodada_entrada__lte=rodada_filtrada)

        resultados_grafico = list(
            resultados.order_by("rodada").values("rodada", "receita", "lucro")
        )
        grafico_desempenho = {
            "labels": [f"R{linha['rodada']}" for linha in resultados_grafico],
            "receita": [float(linha["receita"]) for linha in resultados_grafico],
            "lucro": [float(linha["lucro"]) for linha in resultados_grafico],
        }
        painel_indicadores = montar_painel_financeiro(consolidados)

        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponiveis."
            request.session["ultima_rodada_vista"] = nova.rodada

        evento = sortear_evento(rodada_ativa.numero, jogo_id=grupo.jogo_id) if rodada_ativa and grupo else None

        capacidade_total = sum(c.capacidade_unidades_rodada for c in capacidades) if grupo else 0
        producao_por_produto = {}
        for producao in producoes:
            producao_por_produto[producao.produto_id] = (
                producao_por_produto.get(producao.produto_id, 0)
                + producao.quantidade_produzida
            )
        linhas_fabrica = []
        for capacidade in capacidades:
            produzidas = producao_por_produto.get(capacidade.produto_id, 0)
            total_linha = capacidade.capacidade_unidades_rodada
            linhas_fabrica.append({
                "produto": capacidade.produto,
                "maquinas": capacidade.maquinas,
                "operadores": capacidade.operadores,
                "capacidade": total_linha,
                "produzidas": produzidas,
                "percentual": min(100, round((produzidas / total_linha) * 100)) if total_linha else 0,
            })
        alerta = None
        if grupo:
            if grupo.estoque < capacidade_total * 0.2:
                alerta = "Risco de ruptura de estoque"
            elif grupo.estoque > capacidade_total:
                alerta = "Risco de desperdicio de estoque"

        submissao_realizada = False
        ceo_rodada = None
        if grupo and rodada_ativa:
            submissao_realizada = Decisao.objects.filter(
                grupo=grupo,
                rodada=rodada_ativa.numero,
            ).exists()
            ceo_rodada = obter_ceo_rodada(grupo, rodada_ativa.numero)

        pode_submeter = bool(grupo and rodada_ativa and self.usuario_pode_submeter(request.user, grupo, rodada_ativa.numero))
        permite_edicao = bool(grupo and rodada_ativa and pode_submeter and not submissao_realizada)

        satisfacao_pracas = (
            satisfacao_por_praca(grupo=grupo, rodada=rodada_mapa)
            if grupo and rodada_mapa
            else []
        )
        mapa_barras, mapa_fora = montar_mapa(satisfacao_pracas)
        sede = ponto_da_praca(CIDADE_SEDE)
        mapa_sede = (
            {"nome": CIDADE_SEDE, "x": sede[0], "topo": round(sede[1] - 10, 1)}
            if sede and mapa_barras
            else None
        )

        # Oferta do evento de decisao, se a rodada tiver uma.
        oferta = (
            evento_de_decisao(rodada_ativa.numero, grupo.jogo_id)
            if grupo and rodada_ativa
            else None
        )
        oferta_decidida = None
        if oferta:
            oferta_decidida = DecisaoEventoGrupo.objects.filter(
                grupo=grupo, rodada=rodada_ativa.numero, evento=oferta
            ).first()

        return {
            "nav": "painel",
            "oferta": oferta,
            "oferta_custo": custo_da_oferta(oferta, grupo) if oferta else None,
            "oferta_decidida": oferta_decidida,
            "grupo": grupo,
            "decisoes": decisoes,
            "envios": envios,
            "producoes": producoes,
            "resultados": resultados,
            "grafico_desempenho": grafico_desempenho,
            "painel_indicadores": painel_indicadores,
            "form": form or DecisaoForm(),
            "envio_form": envio_form or DistribuicaoForm(),
            "producao_form": producao_form or ProducaoForm(),
            "compra_mp_form": compra_mp_form or CompraMateriaPrimaForm(),
            "investimento_form": investimento_form or InvestimentoForm(),
            "limite_maquinas": limite_de_expansao(grupo) if grupo else None,
            "alerta": alerta,
            "evento": evento,
            "notificacao": notificacao,
            "rodada_ativa": rodada_ativa,
            "ceo_rodada": ceo_rodada,
            "submissao_realizada": submissao_realizada,
            "pode_submeter": pode_submeter,
            "permite_edicao": permite_edicao,
            "sem_grupo": grupo is None,
            "compras_mp": compras_mp,
            "investimentos": investimentos,
            "saldos_mp": saldos_mp,
            "saldos_produto": saldos_produto,
            "capacidades_produto": capacidades,
            # 12.3.4: a nota usa a SD Global, mas o grupo decide olhando praca
            # a praca -- e aqui que ele ve onde deixou demanda na mesa.
            "satisfacao_pracas": satisfacao_pracas,
            # O mesmo dado no mapa do 9.1: cada praca no lugar real dela,
            # com a barra saindo do ponto. A lista acima continua sendo a
            # leitura numerica -- o mapa mostra onde, ela mostra quanto.
            "mapa_barras": mapa_barras,
            "mapa_sede": mapa_sede,
            "mapa_fora": mapa_fora,
            "linhas_fabrica": linhas_fabrica,
            "aplicacao_financeira": aplicacao_financeira,
            # 6.2: o aviso declara o estado, nao a jogada -- nem quanto,
            # nem qual produto, nem o que fazer.
            "risco_perda_estoque": risco_de_perda_de_estoque(
                grupo, rodada_ativa.numero if rodada_ativa else None
            ),
            "rodada_filtro": rodada_filtro or "",
            "rodadas_disponiveis": rodadas_disponiveis,
        }

    def get(self, request, *args, **kwargs):
        grupo = obter_grupo_do_usuario(request.user)
        if not grupo:
            messages.warning(request, "Voce nao esta vinculado a nenhum grupo.")
        contexto = self.montar_contexto(request, grupo)
        return render(request, self.template_name, contexto)

    def post(self, request, *args, **kwargs):
        """Toda submissao move capital: uma transacao so cobre os cinco ramos.

        Cada ramo grava o registro, debita o capital do grupo e atualiza o
        ResultadoFinanceiro em saves separados. Sem transacao, uma falha no
        meio deixa compra sem debito ou debito sem lancamento contabil.
        """
        with transaction.atomic():
            return self._processar_submissao(request)

    def _processar_submissao(self, request):
        grupo = obter_grupo_do_usuario(request.user)
        if not grupo:
            messages.error(request, "Sem grupo vinculado. Solicite ajuste ao administrador.")
            return redirect("painel_grupo")

        # Relê sob trava: o teste de saldo de cada ramo compara contra este
        # objeto, e dois envios simultâneos debitariam o mesmo capital.
        # ponytail: em SQLite o FOR UPDATE é ignorado e sobra a trava de
        # escrita do próprio arquivo; a trava real vale ao migrar para Postgres.
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)

        rodada_ativa = obter_rodada_ativa(grupo)
        if not rodada_ativa:
            messages.error(request, "Nao existe rodada ativa no momento.")
            return redirect("painel_grupo")

        garantir_capacidades_grupo(grupo)

        if not self.usuario_pode_submeter(request.user, grupo, rodada_ativa.numero):
            ceo = obter_ceo_rodada(grupo, rodada_ativa.numero)
            if ceo:
                messages.error(
                    request,
                    f"Apenas o CEO da rodada pode submeter decisoes: {ceo.nome_usuario}.",
                )
            else:
                messages.error(request, "Nao existe CEO definido para esta rodada.")
            return redirect("painel_grupo")

        if Decisao.objects.filter(grupo=grupo, rodada=rodada_ativa.numero).exists():
            messages.error(request, "A submissao desta rodada ja foi enviada e esta bloqueada.")
            return redirect("painel_grupo")

        if "responder_oferta" in request.POST:
            oferta = evento_de_decisao(rodada_ativa.numero, grupo.jogo_id)
            # as duas guardas acima ja garantem CEO da rodada e rodada
            # ainda aberta -- e o mesmo que  significa.
            if oferta:
                aceitou = request.POST.get("responder_oferta") == "aceitar"
                registrar_decisao(grupo, rodada_ativa.numero, oferta, aceitou)
                messages.success(
                    request,
                    "Resposta registrada. Pode ser alterada até a submissão.",
                )
            return redirect("painel_grupo")

        if "enviar_compra_mp" in request.POST:
            compra_form = CompraMateriaPrimaForm(request.POST)
            if compra_form.is_valid():
                compra = compra_form.save(commit=False)
                compra.grupo = grupo
                compra.rodada_pedido = rodada_ativa.numero
                compra.rodada_recebimento = rodada_ativa.numero + 1
                compra.preco_unitario = compra.materia_prima.preco_unitario

                if not fornecedor_valido_para_mp(compra.materia_prima, compra.cidade_fornecedora):
                    messages.error(
                        request,
                        "Cidade fornecedora invalida para a materia-prima selecionada.",
                    )
                    return redirect("painel_grupo")

                # RN-05: a compra de MP por rodada vai ate 150% do consumo
                # estimado da producao, e "quantidades acima do limite serao
                # automaticamente ajustadas pelo sistema, com alerta ao CEO".
                # Apara antes do frete, senao o grupo pagaria viagem por carga
                # que nao vai comprar.
                limite = limite_de_compra(
                    grupo, compra.materia_prima, rodada_ativa.numero
                )
                if compra.quantidade_kg > limite["restante"]:
                    pedido = compra.quantidade_kg
                    compra.quantidade_kg = limite["restante"]
                    messages.warning(
                        request,
                        (
                            f"Compra ajustada de {pedido} para {compra.quantidade_kg} kg "
                            f"de {compra.materia_prima.codigo}: o limite da rodada e "
                            f"{limite['teto']} kg, 150% do que a fabrica consome "
                            f"rodando cheia (RN-05)."
                        ),
                    )
                if compra.quantidade_kg <= 0:
                    messages.error(
                        request,
                        (
                            f"Limite de compra de {compra.materia_prima.codigo} ja "
                            f"atingido nesta rodada: {limite['teto']} kg."
                        ),
                    )
                    return redirect("painel_grupo")

                custo_insumo = compra.quantidade_kg * compra.preco_unitario
                frete = calcular_frete_materia_prima(
                    distancia_km=compra.cidade_fornecedora.distancia_km,
                    quantidade_kg=compra.quantidade_kg,
                    peso_remetido_kg=peso_produtos_remetidos(
                        grupo, compra.cidade_fornecedora, rodada_ativa.numero
                    ),
                )
                compra.desconto_logistico = frete["desconto_retorno"]
                compra.custo_logistico = frete["custo"]
                compra.valor_total = custo_insumo + compra.custo_logistico

                if grupo.capital < compra.valor_total:
                    messages.error(request, "Capital insuficiente para compra de materia-prima.")
                    return redirect("painel_grupo")

                compra.save()
                grupo.capital -= compra.valor_total
                grupo.save(update_fields=["capital"])

                resultado, _ = ResultadoFinanceiro.objects.get_or_create(
                    grupo=grupo,
                    rodada=rodada_ativa.numero,
                )
                resultado.custos += compra.valor_total
                resultado.saldo_caixa = grupo.capital
                resultado.lucro = resultado.receita - resultado.custos
                resultado.save()

                messages.success(
                    request,
                    (
                        f"Compra registrada. Recebimento previsto para rodada "
                        f"{compra.rodada_recebimento}."
                    ),
                )
                return redirect("painel_grupo")

        elif "enviar_producao" in request.POST:
            producao_form = ProducaoForm(request.POST)
            if producao_form.is_valid():
                producao = producao_form.save(commit=False)
                producao.grupo = grupo
                producao.rodada = rodada_ativa.numero
                evento_bloqueio = evento_estado_ativo(
                    rodada_numero=rodada_ativa.numero,
                    efeito_estado="bloqueio_producao",
                    jogo_id=grupo.jogo_id,
                )
                if evento_bloqueio:
                    messages.error(
                        request,
                        "Producao bloqueada por evento de estado nesta rodada.",
                    )
                    return redirect("painel_grupo")

                if Producao.objects.filter(
                    grupo=grupo,
                    produto=producao.produto,
                    rodada=rodada_ativa.numero,
                ).exists():
                    messages.error(request, "Produto ja possui producao registrada nesta rodada.")
                    return redirect("painel_grupo")

                capacidade_disponivel, capacidade_total = capacidade_disponivel_produto_rodada(
                    grupo=grupo,
                    produto=producao.produto,
                    rodada_numero=rodada_ativa.numero,
                )

                # 11.3.b poe a producao entre as acoes executadas no
                # FECHAMENTO, e o 13.12 lista "quantidade produzida" entre os
                # indicadores gerados pela Producao. Aqui so se registra a
                # ordem; quem produz e o fechamento, seguindo o 13.7.
                producao.quantidade_produzida = 0
                producao.custo_unitario = Decimal("0")
                producao.custo_total = Decimal("0")
                producao.save()

                # RN-05: quantidade acima do limite e "automaticamente
                # ajustada pelo sistema, com alerta ao CEO" -- avisa, nao
                # recusa. O 13.11 manda produzir parcialmente.
                if producao.quantidade_planejada > capacidade_disponivel:
                    messages.warning(
                        request,
                        (
                            f"Ordem registrada, mas a linha de {producao.produto.nome} "
                            f"comporta {capacidade_disponivel} de {capacidade_total} un "
                            f"nesta rodada. O fechamento vai produzir o que couber."
                        ),
                    )

                messages.success(
                    request,
                    "Ordem de produção registrada. A produção é apurada no fechamento.",
                )
                return redirect("painel_grupo")

        elif "enviar_envio" in request.POST:
            envio_form = DistribuicaoForm(request.POST)
            if envio_form.is_valid():
                envio = envio_form.save(commit=False)
                envio.grupo = grupo
                envio.rodada = rodada_ativa.numero

                # 11.3.b executa a distribuicao no FECHAMENTO, depois da
                # producao. Aqui so se registra a ordem de envio: a baixa do
                # acabado e o frete saem no fechamento, quando ja existe o que
                # foi produzido nesta rodada (6.2, produto B).
                envio.custo_transporte = Decimal("0")
                envio.save()

                frete = calcular_frete(
                    distancia_km=envio.cidade.distancia_km,
                    peso_kg=peso_do_envio(envio.produto, envio.quantidade),
                )

                disponivel = estoque_disponivel_produto(grupo, envio.produto)
                if envio.quantidade > disponivel:
                    # RN-05: avisa e ajusta no fechamento, nao recusa.
                    messages.warning(
                        request,
                        (
                            f"Ordem registrada, mas ha {disponivel} un de "
                            f"{envio.produto.nome} em estoque. Se a producao desta "
                            f"rodada nao cobrir o resto, o envio sai parcial."
                        ),
                    )

                messages.success(
                    request,
                    (
                        "Ordem de envio registrada: {viagens} viagem(ns) até {cidade}, "
                        "{ocupacao:.0f}% da capacidade do caminhão, frete estimado de "
                        "{custo}. Expedição e venda saem no fechamento da rodada."
                    ).format(
                        viagens=frete["viagens"],
                        cidade=envio.cidade.nome,
                        ocupacao=frete["ocupacao_percentual"],
                        custo=frete["custo"].quantize(Decimal("0.01")),
                    ),
                )
                return redirect("painel_grupo")

        elif "enviar_investimento" in request.POST:
            investimento_form = InvestimentoForm(request.POST)
            if investimento_form.is_valid():
                investimento = investimento_form.save(commit=False)
                investimento.grupo = grupo
                investimento.rodada = rodada_ativa.numero
                investimento.processado = False

                impedimento = impedimento_para_investir(grupo, investimento)
                if impedimento:
                    messages.error(request, impedimento)
                    return redirect("painel_grupo")

                if investimento.categoria in {"maquinas", "rh"}:
                    investimento.rodada_ativacao = rodada_ativa.numero + 1
                else:
                    investimento.rodada_ativacao = rodada_ativa.numero

                # 14.2.4: o preco da maquina e "fixado pelo simulador", nao
                # digitado por quem compra.
                if investimento.categoria == "maquinas":
                    investimento.valor = CUSTO_MAQUINA * Decimal(investimento.quantidade)

                # 14.3: contratar nao tem taxa de entrada -- "o custo por
                # funcionario e de R$ 1.800,00 mensais, registrado como custo
                # fixo operacional", e o fechamento ja cobra isso por rodada.
                # Debitar um valor de entrada cobraria a mesma contratacao duas
                # vezes.
                if investimento.categoria == "rh":
                    investimento.valor = Decimal("0")

                if investimento.categoria == "financeiro":
                    aplicacao = obter_aplicacao_financeira_grupo(grupo)
                    if investimento.operacao_financeira == "aplicar":
                        if grupo.capital < investimento.valor:
                            messages.error(request, "Capital insuficiente para aplicacao financeira.")
                            return redirect("painel_grupo")
                        grupo.capital -= investimento.valor
                        aplicacao.saldo_aplicado += investimento.valor
                        investimento.processado = True
                    else:
                        if aplicacao.saldo_aplicado < investimento.valor:
                            messages.error(request, "Saldo aplicado insuficiente para resgate.")
                            return redirect("painel_grupo")
                        aplicacao.saldo_aplicado -= investimento.valor
                        grupo.capital += investimento.valor
                        investimento.processado = True
                    aplicacao.save(update_fields=["saldo_aplicado", "data_atualizacao"])
                    grupo.save(update_fields=["capital"])
                    resultado, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo,
                        rodada=rodada_ativa.numero,
                    )
                    resultado.saldo_caixa = grupo.capital
                    resultado.save(update_fields=["saldo_caixa"])
                else:
                    if grupo.capital < investimento.valor:
                        messages.error(request, "Capital insuficiente para registrar investimento.")
                        return redirect("painel_grupo")
                    grupo.capital -= investimento.valor
                    grupo.save(update_fields=["capital"])
                    resultado, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo,
                        rodada=rodada_ativa.numero,
                    )
                    resultado.custos += investimento.valor
                    resultado.saldo_caixa = grupo.capital
                    resultado.lucro = resultado.receita - resultado.custos
                    resultado.save()
                    if investimento.categoria == "marketing":
                        investimento.processado = True

                investimento.save()
                if investimento.categoria == "maquinas":
                    detalhe = (
                        f"{investimento.quantidade} máquina(s) a "
                        f"R$ {CUSTO_MAQUINA:.2f} cada, total de "
                        f"R$ {investimento.valor:.2f}. Lembre de contratar "
                        f"{investimento.quantidade * OPERADORES_POR_MAQUINA} operadores: "
                        f"máquina sem equipe fica parada (14.2.3)."
                    )
                elif investimento.categoria == "rh":
                    detalhe = (
                        f"{investimento.quantidade} operador(es). Não há taxa de "
                        f"contratação: o custo é a folha de R$ "
                        f"{CUSTO_OPERADOR_POR_RODADA:.2f} por rodada (14.3)."
                    )
                else:
                    detalhe = f"R$ {investimento.valor:.2f}."
                messages.success(
                    request,
                    (
                        f"Investimento registrado em "
                        f"{investimento.get_categoria_display()} para ativação na "
                        f"rodada {investimento.rodada_ativacao}. {detalhe}"
                    ),
                )
                return redirect("painel_grupo")

        elif "enviar_decisao" in request.POST:
            # A submissão é o ato de fechar a rodada (11.2), não um texto.
            # A tela pedia "descrição" e "quantidade" -- dois campos que
            # nenhuma regra lê: o fechamento só verifica se a submissão
            # existe. O CEO respondia a uma pergunta sem consequência.
            decisao = Decisao.objects.create(
                grupo=grupo,
                rodada=rodada_ativa.numero,
                descricao=f"Decisões da rodada {rodada_ativa.numero}",
            )
            AuditoriaSubmissaoRodada.objects.create(
                grupo=grupo,
                rodada=rodada_ativa.numero,
                usuario=request.user,
                decisao=decisao,
                ip_origem=obter_ip_origem(request),
            )
            messages.success(
                request,
                "Submissao oficial da rodada registrada. Novas alteracoes foram bloqueadas.",
            )
            return redirect("painel_grupo")

        contexto = self.montar_contexto(
            request,
            grupo,
            form=DecisaoForm(request.POST if "enviar_decisao" in request.POST else None),
            envio_form=DistribuicaoForm(request.POST if "enviar_envio" in request.POST else None),
            producao_form=ProducaoForm(request.POST if "enviar_producao" in request.POST else None),
            compra_mp_form=CompraMateriaPrimaForm(
                request.POST if "enviar_compra_mp" in request.POST else None
            ),
            investimento_form=InvestimentoForm(
                request.POST if "enviar_investimento" in request.POST else None
            ),
        )
        return render(request, self.template_name, contexto)


class DecisoesRodadaView(PainelGrupoView):
    """Tela própria das decisões, preservando as mesmas validações do painel."""

    def montar_contexto(self, *args, **kwargs):
        contexto = super().montar_contexto(*args, **kwargs)
        contexto.update({"somente_decisoes": True, "nav": "decisoes"})

        # A tela decide UMA rodada. As listas vinham com o histórico inteiro:
        # a conferência final dizia "12 registros" para uma rodada em que a
        # equipe tinha comprado 4 vezes -- as outras 8 eram de rodadas já
        # fechadas. O histórico fica em Relatórios.
        rodada = contexto.get("rodada_ativa")
        if rodada:
            numero = rodada.numero
            contexto.update(
                {
                    "compras_mp": contexto["compras_mp"].filter(rodada_pedido=numero),
                    "producoes": contexto["producoes"].filter(rodada=numero),
                    "envios": contexto["envios"].filter(rodada=numero),
                    "investimentos": contexto["investimentos"].filter(rodada=numero),
                }
            )
        return contexto

    def post(self, request, *args, **kwargs):
        resposta = super().post(request, *args, **kwargs)
        if (
            resposta.status_code in {301, 302, 303, 307, 308}
            and resposta.get("Location", "").endswith("/painel/")
        ):
            return redirect("decisoes_rodada")
        return resposta


class GrupoViewSet(viewsets.ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer


class JogoScopedQuerysetMixin:
    jogo_lookup = "jogo_id"

    def filtrar_por_jogo(self, queryset):
        request = self.request
        user = request.user
        jogo_query = request.query_params.get("jogo")

        if user.is_staff:
            if jogo_query is None:
                return queryset
            if jogo_query in {"null", "none"}:
                return queryset.filter(**{f"{self.jogo_lookup}__isnull": True})
            return queryset.filter(**{self.jogo_lookup: jogo_query})

        grupo = obter_grupo_do_usuario(user)
        if not grupo:
            return queryset.none()
        if grupo.jogo_id:
            return queryset.filter(**{self.jogo_lookup: grupo.jogo_id})
        return queryset.filter(**{f"{self.jogo_lookup}__isnull": True})

    def get_queryset(self):
        return self.filtrar_por_jogo(super().get_queryset())


class DecisaoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Decisao.objects.all()
    serializer_class = DecisaoSerializer
    jogo_lookup = "grupo__jogo_id"


class DistribuicaoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Distribuicao.objects.all()
    serializer_class = DistribuicaoSerializer
    jogo_lookup = "grupo__jogo_id"


class ResultadoFinanceiroViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ResultadoFinanceiro.objects.all()
    serializer_class = ResultadoFinanceiroSerializer
    jogo_lookup = "grupo__jogo_id"


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer


class EventoRodadaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EventoRodada.objects.all()
    serializer_class = EventoRodadaSerializer
    jogo_lookup = "jogo_id"


class RodadaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Rodada.objects.all()
    serializer_class = RodadaSerializer
    jogo_lookup = "jogo_id"


class CidadeViewSet(viewsets.ModelViewSet):
    queryset = Cidade.objects.all()
    serializer_class = CidadeSerializer


class GameConfigViewSet(viewsets.ModelViewSet):
    queryset = GameConfig.objects.all()
    serializer_class = GameConfigSerializer


class JogoViewSet(viewsets.ModelViewSet):
    queryset = Jogo.objects.all()
    serializer_class = JogoSerializer


class InvestimentoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Investimento.objects.all()
    serializer_class = InvestimentoSerializer
    jogo_lookup = "grupo__jogo_id"


class MateriaPrimaViewSet(viewsets.ModelViewSet):
    queryset = MateriaPrima.objects.all()
    serializer_class = MateriaPrimaSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer


class ComposicaoProdutoViewSet(viewsets.ModelViewSet):
    queryset = ComposicaoProduto.objects.select_related("produto", "materia_prima").all()
    serializer_class = ComposicaoProdutoSerializer


class ProducaoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Producao.objects.select_related("grupo", "produto").all()
    serializer_class = ProducaoSerializer
    jogo_lookup = "grupo__jogo_id"


class CapacidadeProdutoGrupoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CapacidadeProdutoGrupo.objects.select_related("grupo", "produto").all()
    serializer_class = CapacidadeProdutoGrupoSerializer
    jogo_lookup = "grupo__jogo_id"


class ConsolidadoRodadaGrupoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ConsolidadoRodadaGrupo.objects.select_related("grupo").all()
    serializer_class = ConsolidadoRodadaGrupoSerializer
    jogo_lookup = "grupo__jogo_id"


class CEOGrupoRodadaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CEOGrupoRodada.objects.select_related("grupo", "usuario").all()
    serializer_class = CEOGrupoRodadaSerializer
    jogo_lookup = "grupo__jogo_id"


class AuditoriaSubmissaoRodadaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = AuditoriaSubmissaoRodada.objects.select_related("grupo", "usuario", "decisao").all()
    serializer_class = AuditoriaSubmissaoRodadaSerializer
    jogo_lookup = "grupo__jogo_id"


class DemandaCidadeProdutoViewSet(viewsets.ModelViewSet):
    queryset = DemandaCidadeProduto.objects.select_related("cidade", "produto").all()
    serializer_class = DemandaCidadeProdutoSerializer


class AplicacaoFinanceiraGrupoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = AplicacaoFinanceiraGrupo.objects.select_related("grupo").all()
    serializer_class = AplicacaoFinanceiraGrupoSerializer
    jogo_lookup = "grupo__jogo_id"


class ExecucaoJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExecucaoJob.objects.all()
    serializer_class = ExecucaoJobSerializer


class EstoqueMateriaPrimaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EstoqueMateriaPrima.objects.select_related("grupo", "materia_prima").all()
    serializer_class = EstoqueMateriaPrimaSerializer
    jogo_lookup = "grupo__jogo_id"


class EstoqueProdutoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EstoqueProduto.objects.select_related("grupo", "produto").all()
    serializer_class = EstoqueProdutoSerializer
    jogo_lookup = "grupo__jogo_id"


class MarketShareCidadeProdutoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MarketShareCidadeProduto.objects.select_related("grupo", "cidade", "produto").all()
    serializer_class = MarketShareCidadeProdutoSerializer
    jogo_lookup = "grupo__jogo_id"


class IndicadorRodadaGrupoViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = IndicadorRodadaGrupo.objects.select_related("grupo").all()
    serializer_class = IndicadorRodadaGrupoSerializer
    jogo_lookup = "grupo__jogo_id"


class CompraMateriaPrimaViewSet(JogoScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CompraMateriaPrima.objects.select_related(
        "grupo",
        "materia_prima",
        "cidade_fornecedora",
    ).all()
    serializer_class = CompraMateriaPrimaSerializer
    jogo_lookup = "grupo__jogo_id"

    def create(self, request, *args, **kwargs):
        grupo_id = request.data.get('grupo')
        if grupo_id:
            resultados = (
                ResultadoFinanceiro.objects.filter(grupo_id=grupo_id)
                .order_by('-rodada')[:2]
            )
            if len(resultados) == 2 and all(r.saldo_caixa < 0 for r in resultados):
                return Response(
                    {
                        'detail': 'Investimentos bloqueados por fluxo de caixa negativo.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().create(request, *args, **kwargs)

class RankingAPIView(generics.ListAPIView):
    serializer_class = GrupoSerializer

    def get_queryset(self):
        queryset = Grupo.objects.order_by("-capital")
        user = self.request.user
        if user.is_staff:
            jogo = self.request.query_params.get("jogo")
            if jogo in {"null", "none"}:
                return queryset.filter(jogo__isnull=True)
            if jogo:
                return queryset.filter(jogo_id=jogo)
            return queryset
        grupo = obter_grupo_do_usuario(user)
        if not grupo:
            return Grupo.objects.none()
        if grupo.jogo_id:
            return queryset.filter(jogo_id=grupo.jogo_id)
        return queryset.filter(jogo__isnull=True)


class RankingMulticriterioAPIView(generics.ListAPIView):
    serializer_class = IndicadorRodadaGrupoSerializer

    def get_queryset(self):
        indicadores = IndicadorRodadaGrupo.objects.select_related("grupo", "grupo__jogo")
        user = self.request.user
        if not user.is_staff:
            grupo = obter_grupo_do_usuario(user)
            if grupo and grupo.jogo_id:
                indicadores = indicadores.filter(grupo__jogo_id=grupo.jogo_id)
            elif grupo:
                indicadores = indicadores.filter(grupo__jogo__isnull=True)
            else:
                return IndicadorRodadaGrupo.objects.none()

        rodada_referencia = indicadores.order_by("-rodada").values_list("rodada", flat=True).first()
        if not rodada_referencia:
            return IndicadorRodadaGrupo.objects.none()
        return indicadores.filter(rodada=rodada_referencia).order_by("-score_multicriterio")


class GrupoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = "grupo_list.html"
    context_object_name = "grupos"
    permission_required = "app.view_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_queryset(self):
        return (
            Grupo.objects.select_related("jogo", "lider")
            .prefetch_related("membros")
            .order_by("jogo__nome", "nome")
        )

    def get_context_data(self, **kwargs):
        """Grupos agrupados por turma.

        Uma lista corrida de nomes nao diz de que turma cada equipe e, e a
        professora com duas turmas no mesmo sistema precisa disso antes de
        qualquer outra coisa.
        """
        context = super().get_context_data(**kwargs)
        turmas = {}
        for grupo in context["grupos"]:
            chave = grupo.jogo_id
            turma = turmas.setdefault(
                chave,
                {
                    "nome": grupo.jogo.nome if grupo.jogo else "Grupos sem turma",
                    "jogo": grupo.jogo,
                    "grupos": [],
                },
            )
            turma["grupos"].append(grupo)
        context["turmas"] = list(turmas.values())
        return context


class GrupoCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")

    def test_func(self):
        user = self.request.user
        return getattr(user, "tipo_usuario", "") == "gamemaster" or user.is_superuser

    def get(self, request, *args, **kwargs):
        grupo_form = GrupoCadastroForm()
        membro_formset = MembroFormSet()
        return render(
            request,
            self.template_name,
            {"form": grupo_form, "membro_formset": membro_formset},
        )

    def post(self, request, *args, **kwargs):
        grupo_form = GrupoCadastroForm(request.POST)
        membro_formset = MembroFormSet(request.POST)
        if grupo_form.is_valid() and membro_formset.is_valid():
            try:
                with transaction.atomic():
                    grupo = grupo_form.save(commit=False)
                    if grupo.jogo_id:
                        config = grupo.jogo.config
                    else:
                        config, _ = GameConfig.objects.get_or_create(id=1)
                    grupo.capital = config.capital_inicial
                    grupo.estoque = config.estoque_inicial
                    grupo.maquinas_a = config.maquinas_iniciais_a
                    grupo.maquinas_b = config.maquinas_iniciais_b
                    grupo.maquinas_c = config.maquinas_iniciais_c
                    grupo.maquinas = (
                        config.maquinas_iniciais_a
                        + config.maquinas_iniciais_b
                        + config.maquinas_iniciais_c
                    )
                    grupo.trabalhadores = config.trabalhadores_iniciais
                    grupo.save()
                    lider = None
                    for form in membro_formset.preenchidos:
                        user = User.objects.create_user(
                            email_usuario=form.cleaned_data["email"],
                            nome_usuario=form.cleaned_data["nome"],
                            password=form.cleaned_data["senha"],
                            tipo_usuario=(
                                "lider_grupo" if form.cleaned_data.get("lider") else "membro_grupo"
                            ),
                        )
                        grupo.membros.add(user)
                        if form.cleaned_data.get("lider"):
                            lider = user
                    grupo.lider = lider
                    grupo.save()
            except IntegrityError:
                membro_formset._non_form_errors = membro_formset.error_class(
                    ["Não foi possível cadastrar os integrantes. Confira se os e-mails já possuem cadastro."]
                )
                return render(request, self.template_name, {
                    "form": grupo_form, "membro_formset": membro_formset,
                })
            messages.success(request, "Grupo criado com sucesso.")
            return redirect(self.success_url)
        return render(
            request,
            self.template_name,
            {"form": grupo_form, "membro_formset": membro_formset},
        )


class GrupoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")
    permission_required = "app.change_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class RelatoriosView(LoginRequiredMixin, TemplateView):
    template_name = "financeiro/relatorios.html"
    modo_comparativo = False

    def get(self, request, *args, **kwargs):
        grupo_do_usuario = (
            None if request.user.is_staff else obter_grupo_do_usuario(request.user)
        )
        if request.user.is_staff:
            rodadas_ofertadas = numeros_de_rodadas_fechadas()
        elif grupo_do_usuario:
            rodadas_ofertadas = numeros_de_rodadas_fechadas(
                jogo_id=grupo_do_usuario.jogo_id,
                sem_jogo=grupo_do_usuario.jogo_id is None,
            )
        else:
            rodadas_ofertadas = []
        form = ResultadoFilterForm(request.GET or None, rodadas=rodadas_ofertadas)
        resultados = ResultadoFinanceiro.objects.select_related("grupo")
        consolidados = ConsolidadoRodadaGrupo.objects.select_related("grupo")
        if not request.user.is_staff:
            grupo_usuario = obter_grupo_do_usuario(request.user)
            if not grupo_usuario:
                resultados = ResultadoFinanceiro.objects.none()
                consolidados = ConsolidadoRodadaGrupo.objects.none()
                form.fields["grupo"].queryset = Grupo.objects.none()
            elif grupo_usuario.jogo_id:
                resultados = resultados.filter(grupo__jogo_id=grupo_usuario.jogo_id)
                consolidados = consolidados.filter(grupo__jogo_id=grupo_usuario.jogo_id)
                form.fields["grupo"].queryset = Grupo.objects.filter(jogo_id=grupo_usuario.jogo_id)
            else:
                resultados = resultados.filter(grupo__jogo__isnull=True)
                consolidados = consolidados.filter(grupo__jogo__isnull=True)
                form.fields["grupo"].queryset = Grupo.objects.filter(jogo__isnull=True)
        if form.is_valid():
            if form.cleaned_data.get("rodada"):
                resultados = resultados.filter(rodada=form.cleaned_data["rodada"])
                consolidados = consolidados.filter(rodada=form.cleaned_data["rodada"])
            if form.cleaned_data.get("grupo"):
                resultados = resultados.filter(grupo=form.cleaned_data["grupo"])
                consolidados = consolidados.filter(grupo=form.cleaned_data["grupo"])
        fechadas = numeros_de_rodadas_fechadas()
        resultados = resultados.filter(rodada__in=fechadas)
        consolidados = consolidados.filter(rodada__in=fechadas).order_by("-rodada", "grupo__nome")
        # DRE e fluxo de caixa sao por grupo (10.3): so fazem sentido quando ha
        # um grupo em foco -- o filtro, ou o grupo do proprio aluno.
        grupo_foco = form.cleaned_data.get("grupo") if form.is_valid() else None
        if not grupo_foco and not request.user.is_staff:
            grupo_foco = obter_grupo_do_usuario(request.user)

        dre_linhas = []
        fluxo = []
        dre_consolidado = None
        if grupo_foco:
            do_grupo = list(consolidados.filter(grupo=grupo_foco))
            fluxo = montar_fluxo_de_caixa(do_grupo)
            dre_consolidado = max(do_grupo, key=lambda c: c.rodada, default=None)
            if dre_consolidado:
                dre_linhas = montar_dre(dre_consolidado)

        grupo_destaque = obter_grupo_do_usuario(request.user) if not request.user.is_staff else None
        contexto = {
            "nav": "comparativos" if self.modo_comparativo else "relatorios",
            "resultados": resultados.order_by("-rodada", "grupo__nome"),
            "consolidados": consolidados,
            "painel": montar_painel_financeiro(consolidados, grupo_destaque.nome if grupo_destaque else None),
            "form": form,
            "grupo_foco": grupo_foco,
            "dre_consolidado": dre_consolidado,
            "dre_linhas": dre_linhas,
            "fluxo": fluxo,
            "fluxo_resumo": resumo_do_fluxo(fluxo),
            "modo_comparativo": self.modo_comparativo,
        }
        return render(request, self.template_name, contexto)


class RelatoriosComparativosView(RelatoriosView):
    """Entrada explícita para a leitura comparativa entre equipes do jogo."""
    modo_comparativo = True


class EncerramentoRodadaView(LoginRequiredMixin, TemplateView):
    """Mostra ao grupo o resultado da última rodada já encerrada."""

    template_name = "financeiro/encerramento.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupo = obter_grupo_do_usuario(self.request.user)
        if not grupo:
            context.update({"rodada": None, "resultado": None})
            return context

        rodadas_fechadas = Rodada.objects.filter(fechada=True)
        if grupo.jogo_id:
            rodadas_fechadas = rodadas_fechadas.filter(jogo_id=grupo.jogo_id)
        else:
            rodadas_fechadas = rodadas_fechadas.filter(jogo__isnull=True)
        rodada = rodadas_fechadas.order_by("-numero").first()
        resultado = None
        consolidado = None
        posicao = None
        total_grupos = 0
        operou = False
        evento = None
        if rodada:
            resultado = ResultadoFinanceiro.objects.filter(
                grupo=grupo, rodada=rodada.numero
            ).first()
            # 11.3.e: o fechamento calcula os indicadores e atualiza o
            # ranking. Esta tela e onde o grupo ve o proprio resultado --
            # sem a posicao ela conta metade da rodada.
            consolidados = list(
                ConsolidadoRodadaGrupo.objects.filter(
                    rodada=rodada.numero, grupo__jogo_id=grupo.jogo_id
                ).select_related("grupo")
            )
            classificados = RankingView._ordenar_consolidados(consolidados)
            total_grupos = len(classificados)
            for indice, linha in enumerate(classificados, start=1):
                if linha["grupo"].id == grupo.id:
                    posicao = indice
            consolidado = next(
                (c for c in consolidados if c.grupo_id == grupo.id), None
            )
            operou = bool(
                pares_com_operacao([grupo], [rodada.numero])
            )
            evento = (
                EventoRodada.objects.filter(
                    rodada=rodada.numero, jogo_id=grupo.jogo_id
                )
                .select_related("evento")
                .first()
            )

        context.update(
            {
                "rodada": rodada,
                "resultado": resultado,
                "consolidado": consolidado,
                "posicao": posicao,
                "total_grupos": total_grupos,
                "operou": operou,
                "evento_rodada": evento,
                "nav": "encerramento_rodada",
            }
        )
        return context


class JobsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "jobs.html"
    context_object_name = "jobs"
    model = ExecucaoJob
    permission_required = "app.view_resultadofinanceiro"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def turma_pedida(self):
        """Turma escolhida no filtro, ou None para "todas"."""
        escolha = (self.request.GET.get("jogo") or "").strip()
        if escolha == AVULSO:
            return AVULSO
        if escolha.isdigit() and Jogo.objects.filter(id=int(escolha)).exists():
            return int(escolha)
        return None

    def _por_turma(self, queryset):
        turma = self.turma_pedida()
        if turma == AVULSO:
            return queryset.filter(jogo__isnull=True)
        if turma:
            return queryset.filter(jogo_id=turma)
        return queryset

    def get_queryset(self):
        qs = self._por_turma(
            ExecucaoJob.objects.select_related("jogo").order_by("-iniciado_em")
        )
        comando = self.request.GET.get("comando")
        status = self.request.GET.get("status")
        if comando:
            qs = qs.filter(comando__icontains=comando)
        if status:
            qs = qs.filter(status=status)
        return qs[:200]

    def get_context_data(self, **kwargs):
        """Resumo antes da lista: como foi a ultima execucao de cada rotina.

        A tela abria numa tabela de 200 linhas. A pergunta que leva o
        professor ate aqui e "o fechamento da MINHA turma rodou?", e ela nao
        se responde lendo linha por linha nem misturando turmas.
        """
        context = super().get_context_data(**kwargs)
        escopo = self._por_turma(ExecucaoJob.objects.select_related("jogo"))
        ultimas = {}
        for job in escopo.order_by("comando", "-iniciado_em"):
            ultimas.setdefault(job.comando, job)
        context["ultimas_execucoes"] = list(ultimas.values())
        context["falhas_recentes"] = escopo.filter(status="falha").count()

        turma = self.turma_pedida()
        context["turmas"] = [
            {"valor": "", "nome": "Todas as turmas", "selecionada": turma is None}
        ] + [
            {"valor": str(jogo.id), "nome": jogo.nome, "selecionada": turma == jogo.id}
            for jogo in Jogo.objects.order_by("nome")
        ] + [
            {"valor": AVULSO, "nome": "Grupos sem turma", "selecionada": turma == AVULSO}
        ]
        return context


@login_required
def export_resultados_pdf(request):
    rodada = rodada_do_filtro(request)
    grupo_id = request.GET.get("grupo")
    qs = ConsolidadoRodadaGrupo.objects.select_related("grupo")
    if not request.user.is_staff:
        grupo_usuario = obter_grupo_do_usuario(request.user)
        if not grupo_usuario:
            qs = ConsolidadoRodadaGrupo.objects.none()
        elif grupo_usuario.jogo_id:
            qs = qs.filter(grupo__jogo_id=grupo_usuario.jogo_id)
        else:
            qs = qs.filter(grupo__jogo__isnull=True)
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=resultados.pdf"
    pdf = canvas.Canvas(response)
    y = 800
    pdf.drawString(100, y, "Consolidado de Rodadas")
    y -= 20

    for consolidado in qs.order_by("-rodada", "grupo__nome"):
        pdf.drawString(
            100,
            y,
            (
                f"Grupo {consolidado.grupo.nome} - R{consolidado.rodada} - "
                f"Receita {consolidado.receita_vendas} - Custos {consolidado.custos_totais} - "
                f"Lucro {consolidado.lucro_rodada} - Score {consolidado.score_multicriterio}"
            ),
        )
        y -= 20
        if y < 50:
            pdf.showPage()
            y = 800

    pdf.showPage()
    pdf.save()
    return response


@login_required
def export_resultados_excel(request):
    rodada = rodada_do_filtro(request)
    grupo_id = request.GET.get("grupo")
    qs = ConsolidadoRodadaGrupo.objects.select_related("grupo")
    if not request.user.is_staff:
        grupo_usuario = obter_grupo_do_usuario(request.user)
        if not grupo_usuario:
            qs = ConsolidadoRodadaGrupo.objects.none()
        elif grupo_usuario.jogo_id:
            qs = qs.filter(grupo__jogo_id=grupo_usuario.jogo_id)
        else:
            qs = qs.filter(grupo__jogo__isnull=True)
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)

    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "Grupo",
            "Rodada",
            "Receita Vendas",
            "Custos Operacionais",
            "Penalidade",
            "Perda Pereciveis",
            "Custo Arm. MP",
            "Custo Arm. Produtos",
            "Custos Totais",
            "Lucro",
            "Caixa",
            "Market Share %",
            "Atendimento %",
            "Eficiencia %",
            "Score",
        ]
    )

    for consolidado in qs.order_by("-rodada", "grupo__nome"):
        ws.append(
            [
                consolidado.grupo.nome,
                consolidado.rodada,
                float(consolidado.receita_vendas),
                float(consolidado.custos_operacionais),
                float(consolidado.penalidade_sem_submissao),
                float(consolidado.perda_pereciveis),
                float(consolidado.custo_armazenagem_mp),
                float(consolidado.custo_armazenagem_produtos),
                float(consolidado.custos_totais),
                float(consolidado.lucro_rodada),
                float(consolidado.saldo_caixa),
                float(consolidado.market_share_percent),
                float(consolidado.atendimento_demanda_percent),
                float(consolidado.eficiencia_estoque_percent),
                float(consolidado.score_multicriterio),
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=resultados.xlsx"
    wb.save(response)
    return response


@login_required
def export_resultados_csv(request):
    rodada = rodada_do_filtro(request)
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=resultados.csv"
    writer = csv.writer(response)
    writer.writerow(["Grupo", "Rodada", "Receita", "Custos", "Lucro", "Caixa"])
    for r in qs:
        writer.writerow([
            r.grupo.nome,
            r.rodada,
            float(r.receita),
            float(r.custos),
            float(r.lucro),
            float(r.saldo_caixa),
        ])
    return response


@login_required
def export_resultados_json(request):
    rodada = rodada_do_filtro(request)
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    data = [
        {
            "grupo": r.grupo.nome,
            "rodada": r.rodada,
            "receita": float(r.receita),
            "custos": float(r.custos),
            "lucro": float(r.lucro),
            "caixa": float(r.saldo_caixa),
        }
        for r in qs
    ]
    return JsonResponse(data, safe=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def investir_capacidade_api(request):
    linha_id = request.data.get("linha")
    aumento = int(request.data.get("aumento", 0))
    valor = Decimal(request.data.get("valor", 0))
    linha = get_object_or_404(LinhaProducao, id=linha_id)
    linha.capacidade += aumento
    linha.save()
    Investimento.objects.create(grupo=linha.grupo, categoria="maquinas", valor=valor)
    return Response({"nova_capacidade": linha.capacidade})
