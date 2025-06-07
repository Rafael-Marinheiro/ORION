from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import GameConfig, Group, InventoryItem, ProductionSetting
from .forms import GameConfigForm, DecisionForm, ProductionSettingForm

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def config_view(request):
    if not hasattr(request.user, "tipo_usuario") or request.user.tipo_usuario != "aluno_admin":
        return redirect("home")
    config, _ = GameConfig.objects.get_or_create(id=1)
    if request.method == "POST":
        form = GameConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return render(request, "game_config.html", {"form": form, "saved": True})
    else:
        form = GameConfigForm(instance=config)
    return render(request, "game_config.html", {"form": form})


@login_required
def group_panel(request):
    group = request.user.grupos.first()
    if not group:
        group = Group.objects.create(nome=f"Grupo {request.user.id}")
        group.membros.add(request.user)

    decisions = group.decisoes.all()
    prod_config, _ = ProductionSetting.objects.get_or_create(grupo=group)
    estoque_item, _ = InventoryItem.objects.get_or_create(
        grupo=group, produto="Padrao"
    )
    alerta = None
    capacidade_total = prod_config.maquinas * prod_config.capacidade_maquina
    if estoque_item.quantidade <= 0:
        alerta = "Risco de ruptura de estoque"
    elif estoque_item.quantidade > capacidade_total:
        alerta = "Risco de desperdício de estoque"

    if request.method == "POST":
        form = DecisionForm(request.POST)
        if form.is_valid():
            decision = form.save(commit=False)
            decision.grupo = group
            decision.save()
            return redirect("group_panel")
    else:
        form = DecisionForm()
    return render(
        request,
        "group_panel.html",
        {
            "group": group,
            "decisions": decisions,
            "form": form,
            "estoque": estoque_item,
            "alerta": alerta,
            "prod_config": prod_config,
            "capacidade_total": capacidade_total,
        },
    )


@login_required
def production_config(request):
    group = request.user.grupos.first()
    if not group:
        return redirect("group_panel")

    prod_config, _ = ProductionSetting.objects.get_or_create(grupo=group)
    if request.method == "POST":
        form = ProductionSettingForm(request.POST, instance=prod_config)
        if form.is_valid():
            form.save()
            return redirect("group_panel")
    else:
        form = ProductionSettingForm(instance=prod_config)

    return render(request, "production_config.html", {"form": form, "group": group})

