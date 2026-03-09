import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from rest_framework import generics, viewsets

from .forms import (
    ConfigWizardStep1Form,
    ConfigWizardStep2Form,
    CompraMateriaPrimaForm,
    CustomUserCreationForm,
    DecisaoForm,
    DistribuicaoForm,
    GameConfigForm,
    GrupoForm,
    InvestimentoForm,
    ProducaoForm,
    ResultadoFilterForm,
    RodadaForm,
)
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

MATERIA_PRIMA_FORNECEDORES = {
    "MP1": {"Fortaleza", "Maceio"},
    "MP2": {"Recife", "Porto Alegre"},
    "MP3": {"Rio de Janeiro", "Aracaju", "Belem"},
    "MP4": {"Sao Paulo", "Joao Pessoa", "Goiania"},
}
EVENTO_COOLDOWN_RODADAS = 2
CAPACIDADE_PADRAO_POR_CODIGO = {"A": 15, "B": 15, "C": 10}
TAXA_APLICACAO_FINANCEIRA_RODADA = Decimal("0.015")
CUSTO_OPERADOR_POR_RODADA = Decimal("2000")
FATOR_DESCONTO_LOGISTICO_CRUZADO = Decimal("0.10")
FATOR_KG_EQUIVALENTE_ENVIO = Decimal("1")


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


def evento_estado_ativo(rodada_numero, efeito_estado, jogo_id=None):
    eventos_rodada = EventoRodada.objects.filter(rodada__lte=rodada_numero).select_related("evento")
    if jogo_id:
        eventos_rodada = eventos_rodada.filter(jogo_id=jogo_id)
    else:
        eventos_rodada = eventos_rodada.filter(jogo__isnull=True)

    for er in eventos_rodada.order_by("-rodada"):
        evento = er.evento
        if evento.modo_aplicacao != "estado" or evento.efeito_estado != efeito_estado:
            continue
        fim_vigencia = er.rodada + max(evento.duracao_rodadas, 1) - 1
        if rodada_numero <= fim_vigencia:
            return evento
    return None


def obter_demanda_cidade_produto(cidade, produto):
    demanda = DemandaCidadeProduto.objects.filter(cidade=cidade, produto=produto).first()
    if demanda:
        return int(demanda.demanda_maxima)
    return int(cidade.demanda)


def calcular_fator_marketing(grupo, cidade, rodada_numero):
    investimentos = Investimento.objects.filter(
        grupo=grupo,
        categoria="marketing",
        cidade=cidade,
        rodada_ativacao__lte=rodada_numero,
    )
    total = investimentos.aggregate(total=Sum("valor")).get("total") or Decimal("0")
    config = GameConfig.objects.order_by("id").first()
    regras = config.regra_eventos if config and isinstance(config.regra_eventos, dict) else {}
    marketing_cfg = regras.get("marketing", {}) if isinstance(regras.get("marketing", {}), dict) else {}
    base_valor = Decimal(str(marketing_cfg.get("base_valor", 10000)))
    ganho_por_base = Decimal(str(marketing_cfg.get("ganho_por_base", 0.02)))
    max_fator = Decimal(str(marketing_cfg.get("max_fator", 1.30)))
    if base_valor <= 0:
        base_valor = Decimal("10000")
    fator = Decimal("1") + (total / base_valor) * ganho_por_base
    return min(fator, max_fator)


def calcular_desconto_logistico_cruzado(grupo, cidade, rodada_numero, quantidade_kg, custo_base):
    envios_relacionados = Distribuicao.objects.filter(
        grupo=grupo,
        cidade=cidade,
        rodada=rodada_numero,
    ).aggregate(total=Sum("quantidade"))
    quantidade_envio = Decimal(envios_relacionados.get("total") or 0)
    if quantidade_envio <= 0 or custo_base <= 0:
        return Decimal("0")
    config = GameConfig.objects.order_by("id").first()
    regras = config.regra_eventos if config and isinstance(config.regra_eventos, dict) else {}
    fator_kg = Decimal(str(regras.get("desconto_logistico_kg_equivalente", FATOR_KG_EQUIVALENTE_ENVIO)))
    percentual = Decimal(str(regras.get("desconto_logistico_percentual", FATOR_DESCONTO_LOGISTICO_CRUZADO)))

    limite_kg = quantidade_envio * fator_kg
    base_desconto = min(Decimal(quantidade_kg), limite_kg)
    if base_desconto <= 0:
        return Decimal("0")
    fracao = base_desconto / Decimal(quantidade_kg)
    desconto = custo_base * fracao * percentual
    return min(desconto, custo_base)


def obter_aplicacao_financeira_grupo(grupo):
    return AplicacaoFinanceiraGrupo.objects.get_or_create(
        grupo=grupo,
        defaults={"saldo_aplicado": Decimal("0"), "taxa_juros_rodada": TAXA_APLICACAO_FINANCEIRA_RODADA},
    )[0]


def sortear_evento(rodada, jogo_id=None):
    filtro = {"rodada": rodada}
    if jogo_id:
        filtro["jogo_id"] = jogo_id
    else:
        filtro["jogo__isnull"] = True
    existente = EventoRodada.objects.filter(**filtro).select_related("evento").first()
    if existente:
        return existente.evento

    eventos = list(Evento.objects.all())
    if not eventos:
        return None

    rodadas_bloqueadas = [rodada - i for i in range(1, EVENTO_COOLDOWN_RODADAS + 1) if rodada - i > 0]
    historico = EventoRodada.objects.filter(rodada__in=rodadas_bloqueadas)
    if jogo_id:
        historico = historico.filter(jogo_id=jogo_id)
    else:
        historico = historico.filter(jogo__isnull=True)
    eventos_bloqueados_ids = set(historico.values_list("evento_id", flat=True))
    candidatos = [evento for evento in eventos if evento.id not in eventos_bloqueados_ids]
    if not candidatos:
        candidatos = eventos

    escolhido = random.choice(candidatos)
    EventoRodada.objects.create(rodada=rodada, jogo_id=jogo_id, evento=escolhido)
    return escolhido


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


def processar_recebimentos_materia_prima(grupo, rodada_numero):
    evento_atraso = evento_estado_ativo(
        rodada_numero=rodada_numero,
        efeito_estado="atraso_mp",
        jogo_id=grupo.jogo_id,
    )
    pendentes = CompraMateriaPrima.objects.filter(
        grupo=grupo,
        recebida=False,
        rodada_recebimento__lte=rodada_numero,
    ).select_related("materia_prima")
    for compra in pendentes:
        if evento_atraso and compra.rodada_recebimento <= rodada_numero:
            compra.rodada_recebimento = rodada_numero + 1
            compra.save(update_fields=["rodada_recebimento"])
            continue
        estoque, _ = EstoqueMateriaPrima.objects.get_or_create(
            grupo=grupo,
            materia_prima=compra.materia_prima,
            defaults={"quantidade_kg": Decimal("0")},
        )
        estoque.quantidade_kg += compra.quantidade_kg
        estoque.save(update_fields=["quantidade_kg"])
        compra.recebida = True
        compra.save(update_fields=["recebida"])


def consumir_materia_prima_para_producao(grupo, produto, quantidade_planejada, aplicar_consumo=True):
    composicoes = list(
        ComposicaoProduto.objects.filter(produto=produto).select_related("materia_prima")
    )
    if not composicoes:
        return False, "Produto sem composicao cadastrada."

    faltas = []
    consumos = []

    for item in composicoes:
        necessidade = item.quantidade_por_unidade * Decimal(quantidade_planejada)
        estoque, _ = EstoqueMateriaPrima.objects.get_or_create(
            grupo=grupo,
            materia_prima=item.materia_prima,
            defaults={"quantidade_kg": Decimal("0")},
        )
        if estoque.quantidade_kg < necessidade:
            faltas.append(
                f"{item.materia_prima.codigo}: precisa {necessidade} kg, saldo {estoque.quantidade_kg} kg"
            )
        consumos.append((estoque, necessidade))

    if faltas:
        return False, "Materia-prima insuficiente: " + "; ".join(faltas)

    if aplicar_consumo:
        for estoque, necessidade in consumos:
            estoque.quantidade_kg -= necessidade
            estoque.save(update_fields=["quantidade_kg"])

    return True, None


def atualizar_estoque_total_grupo(grupo):
    total = (
        EstoqueProduto.objects.filter(grupo=grupo)
        .aggregate(total=Sum("quantidade"))
        .get("total")
        or 0
    )
    grupo.estoque = int(total)
    grupo.save(update_fields=["estoque"])


def adicionar_estoque_produto(grupo, produto, rodada_numero, quantidade):
    lote, _ = EstoqueProduto.objects.get_or_create(
        grupo=grupo,
        produto=produto,
        rodada_entrada=rodada_numero,
        defaults={"quantidade": 0},
    )
    lote.quantidade += int(quantidade)
    lote.save(update_fields=["quantidade"])
    atualizar_estoque_total_grupo(grupo)


def consumir_estoque_produto(grupo, produto, quantidade):
    quantidade_restante = int(quantidade)
    lotes = EstoqueProduto.objects.filter(
        grupo=grupo,
        produto=produto,
        quantidade__gt=0,
    ).order_by("rodada_entrada", "id")
    disponivel = lotes.aggregate(total=Sum("quantidade")).get("total") or 0
    if disponivel < quantidade_restante:
        return False, disponivel

    for lote in lotes:
        if quantidade_restante <= 0:
            break
        retirada = min(lote.quantidade, quantidade_restante)
        lote.quantidade -= retirada
        lote.save(update_fields=["quantidade"])
        quantidade_restante -= retirada

    atualizar_estoque_total_grupo(grupo)
    return True, disponivel


def garantir_capacidades_grupo(grupo):
    for produto in Produto.objects.filter(ativo=True):
        maquinas_default = CAPACIDADE_PADRAO_POR_CODIGO.get(produto.codigo, 0)
        CapacidadeProdutoGrupo.objects.get_or_create(
            grupo=grupo,
            produto=produto,
            defaults={
                "maquinas": maquinas_default,
                "operadores": maquinas_default * 2,
                "minutos_por_maquina": 400,
            },
        )


def capacidade_disponivel_produto_rodada(grupo, produto, rodada_numero):
    capacidade, _ = CapacidadeProdutoGrupo.objects.get_or_create(
        grupo=grupo,
        produto=produto,
        defaults={
            "maquinas": CAPACIDADE_PADRAO_POR_CODIGO.get(produto.codigo, 0),
            "operadores": CAPACIDADE_PADRAO_POR_CODIGO.get(produto.codigo, 0) * 2,
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



class FeedbackView(FormView):
    template_name = 'feedback.html'
    form_class = FeedbackForm
    success_url = reverse_lazy('feedback')

    def form_valid(self, form):
        suggestion = form.cleaned_data['suggestion']
        email = form.cleaned_data.get('email')
        line = f"- {suggestion}"
        if email:
            line += f" (contato: {email})"
        line += f" - {timezone.now().date()}\n"
        roadmap_path = settings.ROADMAP_FILE
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

@login_required
def home(request):
    return render(request, "home.html")


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")

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
        obj, _ = GameConfig.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        form.instance.produtos_habilitados = form.cleaned_data["produtos_habilitados"]
        form.instance.regra_eventos = form.cleaned_data.get("regra_eventos", {})
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
            initial = {
                "capital_inicial": config.capital_inicial,
                "estoque_inicial": config.estoque_inicial,
                "maquinas_iniciais": config.maquinas_iniciais,
                "capacidade_maquina": config.capacidade_maquina,
            }
            initial.update(wizard_data.get("step1", {}))
            form = self.get_form_for_step(step, initial=initial)
        elif step == 2:
            initial = {
                "produtos_habilitados": config.produtos_habilitados,
                "modulo_producao": config.modulo_producao,
                "modulo_distribuicao": config.modulo_distribuicao,
                "modulo_financeiro": config.modulo_financeiro,
                "regra_eventos": config.regra_eventos,
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
            },
        )

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
                    },
                )
            wizard_data[f"step{step}"] = form.cleaned_data
            request.session[self.session_key] = wizard_data
            return redirect(f"{reverse_lazy('game_config_wizard')}?step={step+1}")

        if step == 3 and "confirmar" in request.POST:
            dados_step1 = wizard_data.get("step1", {})
            dados_step2 = wizard_data.get("step2", {})
            if not dados_step1 or not dados_step2:
                messages.error(request, "Wizard incompleto. Preencha as etapas anteriores.")
                return redirect(f"{reverse_lazy('game_config_wizard')}?step=1")
            config, _ = GameConfig.objects.get_or_create(id=1)
            config.capital_inicial = dados_step1["capital_inicial"]
            config.estoque_inicial = dados_step1["estoque_inicial"]
            config.maquinas_iniciais = dados_step1["maquinas_iniciais"]
            config.capacidade_maquina = dados_step1["capacidade_maquina"]
            config.produtos_habilitados = dados_step2.get("produtos_habilitados") or ""
            config.modulo_producao = dados_step2.get("modulo_producao", False)
            config.modulo_distribuicao = dados_step2.get("modulo_distribuicao", False)
            config.modulo_financeiro = dados_step2.get("modulo_financeiro", False)
            config.regra_eventos = dados_step2.get("regra_eventos") or {}
            config.save()
            request.session.pop(self.session_key, None)
            messages.success(request, "Configuracao atualizada pelo wizard com sucesso.")
            return redirect("game_config")

        return redirect(f"{reverse_lazy('game_config_wizard')}?step={step}")


class RodadaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Rodada
    form_class = RodadaForm
    template_name = "rodada_form.html"
    success_url = reverse_lazy("home")
    permission_required = "app.add_rodada"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

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


class RankingView(LoginRequiredMixin, TemplateView):
    template_name = "ranking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        indicadores = IndicadorRodadaGrupo.objects.select_related("grupo", "grupo__jogo")

        if not self.request.user.is_staff:
            grupo = obter_grupo_do_usuario(self.request.user)
            if grupo and grupo.jogo_id:
                indicadores = indicadores.filter(grupo__jogo_id=grupo.jogo_id)
            elif grupo:
                indicadores = indicadores.filter(grupo__jogo__isnull=True)

        rodada_referencia = indicadores.order_by("-rodada").values_list("rodada", flat=True).first()
        if rodada_referencia:
            ranking = list(
                indicadores.filter(rodada=rodada_referencia).order_by("-score_multicriterio")
            )
        else:
            ranking = []
            grupos_base = Grupo.objects.order_by("-capital")
            if not self.request.user.is_staff:
                grupo_usuario = obter_grupo_do_usuario(self.request.user)
                if grupo_usuario and grupo_usuario.jogo_id:
                    grupos_base = grupos_base.filter(jogo_id=grupo_usuario.jogo_id)
                elif grupo_usuario:
                    grupos_base = grupos_base.filter(jogo__isnull=True)
                else:
                    grupos_base = Grupo.objects.none()
            for grupo in grupos_base:
                ranking.append(
                    {
                        "grupo": grupo,
                        "score_multicriterio": Decimal("0"),
                        "market_share_percent": Decimal("0"),
                        "atendimento_demanda_percent": Decimal("0"),
                        "eficiencia_estoque_percent": Decimal("0"),
                        "lucro_rodada": Decimal("0"),
                    }
                )

        context["ranking"] = ranking
        context["rodada_referencia"] = rodada_referencia
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
        if grupo and rodada_ativa:
            processar_recebimentos_materia_prima(grupo, rodada_ativa.numero)
        if grupo:
            garantir_capacidades_grupo(grupo)
        resultados = grupo.resultados.all() if grupo else ResultadoFinanceiro.objects.none()
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
        rodada_filtro = request.GET.get("rodada")
        if rodada_filtro and rodada_filtro.isdigit():
            rodada_filtrada = int(rodada_filtro)
            resultados = resultados.filter(rodada=rodada_filtrada)
            decisoes = decisoes.filter(rodada=rodada_filtrada)
            envios = envios.filter(rodada=rodada_filtrada)
            producoes = producoes.filter(rodada=rodada_filtrada)
            compras_mp = compras_mp.filter(rodada_pedido=rodada_filtrada)
            investimentos = investimentos.filter(rodada=rodada_filtrada)
            saldos_produto = saldos_produto.filter(rodada_entrada__lte=rodada_filtrada)

        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponiveis."
            request.session["ultima_rodada_vista"] = nova.rodada

        evento = sortear_evento(rodada_ativa.numero, jogo_id=grupo.jogo_id) if rodada_ativa and grupo else None

        capacidade_total = sum(c.capacidade_unidades_rodada for c in capacidades) if grupo else 0
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

        return {
            "grupo": grupo,
            "decisoes": decisoes,
            "envios": envios,
            "producoes": producoes,
            "resultados": resultados,
            "form": form or DecisaoForm(),
            "envio_form": envio_form or DistribuicaoForm(),
            "producao_form": producao_form or ProducaoForm(),
            "compra_mp_form": compra_mp_form or CompraMateriaPrimaForm(),
            "investimento_form": investimento_form or InvestimentoForm(),
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
            "aplicacao_financeira": aplicacao_financeira,
            "rodada_filtro": rodada_filtro or "",
        }

    def get(self, request, *args, **kwargs):
        grupo = obter_grupo_do_usuario(request.user)
        if not grupo:
            messages.warning(request, "Voce nao esta vinculado a nenhum grupo.")
        contexto = self.montar_contexto(request, grupo)
        return render(request, self.template_name, contexto)

    def post(self, request, *args, **kwargs):
        grupo = obter_grupo_do_usuario(request.user)
        if not grupo:
            messages.error(request, "Sem grupo vinculado. Solicite ajuste ao administrador.")
            return redirect("painel_grupo")

        rodada_ativa = obter_rodada_ativa(grupo)
        if not rodada_ativa:
            messages.error(request, "Nao existe rodada ativa no momento.")
            return redirect("painel_grupo")

        processar_recebimentos_materia_prima(grupo, rodada_ativa.numero)
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

                custo_insumo = compra.quantidade_kg * compra.preco_unitario
                compra.custo_logistico = (
                    compra.quantidade_kg
                    * Decimal(compra.cidade_fornecedora.distancia_km)
                    * Decimal("1.5")
                )
                desconto_logistico = calcular_desconto_logistico_cruzado(
                    grupo=grupo,
                    cidade=compra.cidade_fornecedora,
                    rodada_numero=rodada_ativa.numero,
                    quantidade_kg=compra.quantidade_kg,
                    custo_base=compra.custo_logistico,
                )
                compra.desconto_logistico = desconto_logistico
                compra.custo_logistico = max(compra.custo_logistico - desconto_logistico, Decimal("0"))
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

                if producao.quantidade_planejada > capacidade_disponivel:
                    messages.error(
                        request,
                        (
                            f"Capacidade insuficiente para {producao.produto.nome}. "
                            f"Disponivel: {capacidade_disponivel} de {capacidade_total} un na rodada."
                        ),
                    )
                    return redirect("painel_grupo")

                sucesso_consumo, erro_consumo = consumir_materia_prima_para_producao(
                    grupo=grupo,
                    produto=producao.produto,
                    quantidade_planejada=producao.quantidade_planejada,
                    aplicar_consumo=False,
                )
                if not sucesso_consumo:
                    messages.error(request, erro_consumo)
                    return redirect("painel_grupo")

                custo_unitario = producao.produto.custo_unitario_estimado
                custo_total = custo_unitario * Decimal(producao.quantidade_planejada)
                evento = sortear_evento(producao.rodada, jogo_id=grupo.jogo_id)
                if evento and evento.modo_aplicacao == "percentual" and evento.tipo == "custo_producao":
                    custo_total *= Decimal(1 + evento.impacto_percentual / 100)

                if grupo.capital < custo_total:
                    messages.error(request, "Capital insuficiente para esta producao.")
                    return redirect("painel_grupo")

                consumir_materia_prima_para_producao(
                    grupo=grupo,
                    produto=producao.produto,
                    quantidade_planejada=producao.quantidade_planejada,
                    aplicar_consumo=True,
                )

                producao.quantidade_produzida = producao.quantidade_planejada
                producao.custo_unitario = custo_unitario
                producao.custo_total = custo_total
                producao.save()

                grupo.capital -= custo_total
                grupo.save(update_fields=["capital"])
                adicionar_estoque_produto(
                    grupo=grupo,
                    produto=producao.produto,
                    rodada_numero=rodada_ativa.numero,
                    quantidade=producao.quantidade_produzida,
                )

                resultado, _ = ResultadoFinanceiro.objects.get_or_create(
                    grupo=grupo,
                    rodada=rodada_ativa.numero,
                )
                resultado.custos += custo_total
                resultado.saldo_caixa = grupo.capital
                resultado.lucro = resultado.receita - resultado.custos
                resultado.save()

                messages.success(request, "Producao registrada.")
                return redirect("painel_grupo")

        elif "enviar_envio" in request.POST:
            envio_form = DistribuicaoForm(request.POST)
            if envio_form.is_valid():
                envio = envio_form.save(commit=False)
                envio.grupo = grupo
                envio.rodada = rodada_ativa.numero

                evento = sortear_evento(envio.rodada, jogo_id=grupo.jogo_id)
                sucesso_consumo, disponivel = consumir_estoque_produto(
                    grupo=grupo,
                    produto=envio.produto,
                    quantidade=envio.quantidade,
                )
                if not sucesso_consumo:
                    messages.error(
                        request,
                        (
                            f"Estoque insuficiente para {envio.produto.nome}. "
                            f"Disponivel: {disponivel}."
                        ),
                    )
                    return redirect("painel_grupo")

                custo = Decimal(envio.cidade.distancia_km) * envio.quantidade * Decimal("0.1")
                if evento and evento.modo_aplicacao == "percentual" and evento.tipo == "custo_transporte":
                    custo *= Decimal(1 + evento.impacto_percentual / 100)

                envio.custo_transporte = custo
                envio.save()

                grupo.capital -= custo
                grupo.save(update_fields=["capital"])

                resultado, _ = ResultadoFinanceiro.objects.get_or_create(
                    grupo=grupo,
                    rodada=envio.rodada,
                )
                resultado.custos += custo
                resultado.lucro = resultado.receita - resultado.custos
                resultado.saldo_caixa = grupo.capital
                resultado.save()

                messages.success(
                    request,
                    "Distribuicao registrada. A venda sera calculada no fechamento da rodada.",
                )
                return redirect("painel_grupo")

        elif "enviar_investimento" in request.POST:
            investimento_form = InvestimentoForm(request.POST)
            if investimento_form.is_valid():
                investimento = investimento_form.save(commit=False)
                investimento.grupo = grupo
                investimento.rodada = rodada_ativa.numero
                investimento.processado = False

                if investimento.categoria in {"maquinas", "rh"}:
                    investimento.rodada_ativacao = rodada_ativa.numero + 1
                else:
                    investimento.rodada_ativacao = rodada_ativa.numero

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
                messages.success(
                    request,
                    f"Investimento registrado ({investimento.get_categoria_display()}) para ativacao na rodada {investimento.rodada_ativacao}.",
                )
                return redirect("painel_grupo")

        elif "enviar_decisao" in request.POST:
            form = DecisaoForm(request.POST)
            if form.is_valid():
                decisao = form.save(commit=False)
                decisao.grupo = grupo
                decisao.rodada = rodada_ativa.numero
                decisao.save()
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
            grupo = grupo_form.save(commit=False)
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
            grupo.capacidade_maquina = config.capacidade_maquina
            grupo.save()
            lider = None
            for form in membro_formset:
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
            if not lider:
                grupo.delete()
                membro_formset._non_form_errors = membro_formset.error_class(
                    ["Selecione um líder para o grupo."]
                )
                return render(
                    request,
                    self.template_name,
                    {"form": grupo_form, "membro_formset": membro_formset},
                )
            grupo.lider = lider
            grupo.save()
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

    def get(self, request, *args, **kwargs):
        form = ResultadoFilterForm(request.GET or None)
        resultados = ResultadoFinanceiro.objects.select_related("grupo")
        consolidados = ConsolidadoRodadaGrupo.objects.select_related("grupo")
        if not request.user.is_staff:
            grupo_usuario = obter_grupo_do_usuario(request.user)
            if not grupo_usuario:
                resultados = ResultadoFinanceiro.objects.none()
                consolidados = ConsolidadoRodadaGrupo.objects.none()
            elif grupo_usuario.jogo_id:
                resultados = resultados.filter(grupo__jogo_id=grupo_usuario.jogo_id)
                consolidados = consolidados.filter(grupo__jogo_id=grupo_usuario.jogo_id)
            else:
                resultados = resultados.filter(grupo__jogo__isnull=True)
                consolidados = consolidados.filter(grupo__jogo__isnull=True)
        if form.is_valid():
            if form.cleaned_data.get("rodada"):
                resultados = resultados.filter(rodada=form.cleaned_data["rodada"])
                consolidados = consolidados.filter(rodada=form.cleaned_data["rodada"])
            if form.cleaned_data.get("grupo"):
                resultados = resultados.filter(grupo=form.cleaned_data["grupo"])
                consolidados = consolidados.filter(grupo=form.cleaned_data["grupo"])
        contexto = {
            "resultados": resultados.order_by("-rodada", "grupo__nome"),
            "consolidados": consolidados.order_by("-rodada", "grupo__nome"),
            "form": form,
        }
        return render(request, self.template_name, contexto)


class JobsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "jobs.html"
    context_object_name = "jobs"
    model = ExecucaoJob
    permission_required = "app.view_resultadofinanceiro"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_queryset(self):
        qs = ExecucaoJob.objects.order_by("-iniciado_em")
        comando = self.request.GET.get("comando")
        status = self.request.GET.get("status")
        if comando:
            qs = qs.filter(comando__icontains=comando)
        if status:
            qs = qs.filter(status=status)
        return qs[:200]


@login_required
def export_resultados_pdf(request):
    rodada = request.GET.get("rodada")
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
    rodada = request.GET.get("rodada")
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
    rodada = request.GET.get("rodada")
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
    rodada = request.GET.get("rodada")
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
