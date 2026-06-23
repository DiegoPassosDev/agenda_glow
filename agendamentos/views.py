from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from .models import Agendamento, Cliente, Esteticista, Notificacao, Servico
from .forms import AgendamentoForm, ClienteForm, LoginForm, ServicoForm
import json


def login_view(request):
  if request.user.is_authenticated:
    return redirect("dashboard")

  if request.method == "POST":
    form = LoginForm(data=request.POST)
    if form.is_valid():
      user = form.get_user()
      login(request, user)
      return redirect("dashboard")
  else:
    form = LoginForm()

  return render(request, "login.html", {"form": form})

@login_required
def logout_view(request):
  logout(request)
  return redirect("login")

@login_required
def dashboard(request):
  try:
    esteticista = request.user.esteticista
  except Esteticista.DoesNotExist:
    messages.error(request, "Usuário não está associado a uma esteticista.")
    return redirect("login")

  data_str = request.GET.get("data")
  if data_str:
    try:
      data_selecionada = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
      data_selecionada = timezone.now().date()
  else:
    data_selecionada = timezone.now().date()

  inicio_dia = timezone.make_aware(
    datetime.combine(data_selecionada, datetime.min.time())
  )
  fim_dia = timezone.make_aware(
    datetime.combine(data_selecionada, datetime.max.time())
  )

  agendamentos = (
    Agendamento.objects.filter(data_hora__gte=inicio_dia, data_hora__lte=fim_dia)
    .select_related("esteticista", "cliente", "servico")
    .order_by("data_hora")
  )

  total_agendamentos = agendamentos.count()
  total_cancelados = agendamentos.filter(status="cancelado").count()
  total_confirmados = agendamentos.filter(status="confirmado").count()
  total_concluidos = agendamentos.filter(status="concluido").count()

  horarios_disponiveis = []
  hora_atual = 8
  while hora_atual < 18:
    for minuto in [0, 30]:
      horario = f"{hora_atual:02d}:{minuto:02d}"
      hora_check = timezone.make_aware(
        datetime.combine(
          data_selecionada, datetime.strptime(horario, "%H:%M").time()
        )
      )

      agora = timezone.now()
      if hora_check < agora:
        horarios_disponiveis.append({"horario": horario, "disponivel": False})
        continue

      ocupado = False
      for ag in agendamentos.exclude(status="cancelado"):
        hora_fim_ag = ag.data_hora + timedelta(minutes=ag.duracao_minutos)
        if ag.data_hora <= hora_check < hora_fim_ag:
          ocupado = True
          break

      horarios_disponiveis.append({"horario": horario, "disponivel": not ocupado})
    hora_atual += 1

  context = {
    "agendamentos": agendamentos,
    "total_agendamentos": total_agendamentos,
    "total_cancelados": total_cancelados,
    "total_confirmados": total_confirmados,
    "total_concluidos": total_concluidos,
    "data_selecionada": data_selecionada,
    "data_anterior": data_selecionada - timedelta(days=1),
    "data_proxima": data_selecionada + timedelta(days=1),
    "horarios_disponiveis": horarios_disponiveis,
    "hoje": timezone.now().date(),
  }

  return render(request, "dashboard.html", context)

@login_required
def criar_agendamento(request):
  try:
    esteticista = request.user.esteticista
  except Esteticista.DoesNotExist:
    messages.error(request, "Usuário não está associado a uma esteticista.")
    return redirect("dashboard")

  if request.method == "POST":
    form = AgendamentoForm(request.POST, esteticista=esteticista)
    if form.is_valid():
      agendamento = form.save(commit=False)
      agendamento.esteticista = esteticista
      agendamento.save()

      outras_esteticistas = Esteticista.objects.exclude(id=esteticista.id)
      for outra in outras_esteticistas:
        Notificacao.objects.create(
          esteticista=outra,
          agendamento=agendamento,
          tipo="novo_agendamento",
          mensagem=f"{esteticista} agendou {agendamento.cliente.nome} para {agendamento.data_hora.strftime('%d/%m às %H:%M')}",
        )

      messages.success(request, "Agendamento criado com sucesso!")
      return redirect("dashboard")
    else:
      erro_modal = None

      if "__all__" in form.errors:
        erro_modal = form.errors["__all__"][0]

      for field, errors in form.errors.items():
        if field != "__all__":
          for error in errors:
            label = form.fields[field].label
            messages.error(request, f"{label}: {error}")
      return render(
        request,
        "agendamento_form.html",
        {
          "form": form,
          "titulo": "Novo Agendamento",
          "erro_modal": erro_modal,
        },
      )
  else:
    form = AgendamentoForm(esteticista=esteticista)

  return render(
    request,
    "agendamento_form.html",
    {
      "form": form,
      "titulo": "Novo Agendamento",
    },
  )

@login_required
def editar_agendamento(request, pk):
  agendamento = get_object_or_404(Agendamento, pk=pk)

  if agendamento.esteticista != request.user.esteticista:
    messages.error(request, "Você não tem permissão para editar este agendamento.")
    return redirect("dashboard")

  if request.method == "POST":
    form = AgendamentoForm(
      request.POST, instance=agendamento, esteticista=request.user.esteticista
    )
    if form.is_valid():
      form.save()

      outras_esteticistas = Esteticista.objects.exclude(
        id=request.user.esteticista.id
      )
      for outra in outras_esteticistas:
        Notificacao.objects.create(
          esteticista=outra,
          agendamento=agendamento,
          tipo="novo_agendamento",
          mensagem=f"{request.user.esteticista} atualizou o agendamento de {agendamento.cliente.nome} para {agendamento.data_hora.strftime('%d/%m às %H:%M')}",
        )

      messages.success(request, "Agendamento atualizado com sucesso!")
      return redirect("dashboard")
  else:
    form = AgendamentoForm(
      instance=agendamento, esteticista=request.user.esteticista
    )

  return render(
    request,
    "agendamento_form.html",
    {"form": form, "titulo": "Editar Agendamento", "agendamento": agendamento},
  )

@login_required
def cancelar_agendamento(request, pk):
  agendamento = get_object_or_404(Agendamento, pk=pk)

  if agendamento.esteticista != request.user.esteticista:
    messages.error(
      request, "Você não tem permissão para cancelar este agendamento."
    )
    return redirect("dashboard")

  if agendamento.status not in ["agendado", "confirmado"]:
    messages.error(request, "Este agendamento não pode mais ser cancelado.")
    return redirect("dashboard")

  if request.method == "POST":
    agendamento.status = "cancelado"
    agendamento.save()

    outras_esteticistas = Esteticista.objects.exclude(
      id=request.user.esteticista.id
    )
    for outra in outras_esteticistas:
      Notificacao.objects.create(
        esteticista=outra,
        agendamento=agendamento,
        tipo="cancelamento",
        mensagem=f"Agendamento de {agendamento.cliente.nome} em {agendamento.data_hora.strftime('%d/%m às %H:%M')} foi cancelado",
      )

    messages.success(request, "Agendamento cancelado com sucesso!")
    return redirect("dashboard")

  return render(request, "confirmar_cancelamento.html", {"agendamento": agendamento})

@login_required
def clientes_list(request):
  clientes = Cliente.objects.all().order_by("nome")
  return render(request, "clientes_list.html", {"clientes": clientes})

@login_required
def cliente_create(request):
  if request.method == "POST":
    form = ClienteForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Cliente cadastrado com sucesso!")
      return redirect("clientes_list")
  else:
    form = ClienteForm()

  return render(
    request,
    "cliente_form.html",
    {"form": form, "titulo": "Novo Cliente"},
  )

@login_required
def cliente_edit(request, pk):
  cliente = get_object_or_404(Cliente, pk=pk)

  if request.method == "POST":
    form = ClienteForm(request.POST, instance=cliente)
    if form.is_valid():
      form.save()
      messages.success(request, "Cliente atualizado com sucesso!")
      return redirect("clientes_list")
  else:
    form = ClienteForm(instance=cliente)

  return render(
    request,
    "cliente_form.html",
    {"form": form, "titulo": "Editar Cliente", "cliente": cliente},
  )

@login_required
def marcar_notificacao_lida(request, pk):
  notificacao = get_object_or_404(
    Notificacao, pk=pk, esteticista=request.user.esteticista
  )
  notificacao.lida = True
  notificacao.save()
  return JsonResponse({"status": "ok"})

@login_required
def servicos_list(request):
  servicos = Servico.objects.all().order_by("nome")
  return render(request, "servicos_list.html", {"servicos": servicos})

@login_required
def servico_create(request):
  if request.method == "POST":
    form = ServicoForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, "Serviço cadastrado com sucesso!")
      return redirect("servicos_list")
  else:
    form = ServicoForm()

  return render(
    request,
    "servico_form.html",
    {"form": form, "titulo": "Novo Serviço"},
  )

@login_required
def servico_edit(request, pk):
  servico = get_object_or_404(Servico, pk=pk)

  if request.method == "POST":
    form = ServicoForm(request.POST, instance=servico)
    if form.is_valid():
      form.save()
      messages.success(request, "Serviço atualizado com sucesso!")
      return redirect("servicos_list")
  else:
    form = ServicoForm(instance=servico)

  return render(
    request,
    "servico_form.html",
    {"form": form, "titulo": "Editar Serviço", "servico": servico},
  )

@login_required
def servico_toggle_ativo(request, pk):
  servico = get_object_or_404(Servico, pk=pk)
  servico.ativo = not servico.ativo
  servico.save()

  status = "ativado" if servico.ativo else "desativado"
  messages.success(request, f"Serviço {status} com sucesso!")
  return redirect("servicos_list")

@login_required
@require_POST
def atualizar_status_agendamento(request, pk):
  try:
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if agendamento.esteticista != request.user.esteticista:
      return JsonResponse(
        {
          "success": False,
          "message": "Você não tem permissão para alterar este agendamento.",
        },
        status=403,
      )

    data = json.loads(request.body)
    novo_status = data.get("status")

    if novo_status not in dict(Agendamento.STATUS_CHOICES).keys():
      return JsonResponse(
        {"success": False, "message": "Status inválido."}, status=400
      )

    agendamento.status = novo_status
    agendamento.save()

    return JsonResponse(
      {
        "success": True,
        "message": f"Status atualizado para {agendamento.get_status_display()}",
        "status": novo_status,
        "status_display": agendamento.get_status_display(),
      }
    )

  except Exception as e:
    return JsonResponse({"success": False, "message": str(e)}, status=500)

@login_required
def verificar_agendamentos_pendentes(request):
  try:
    esteticista = request.user.esteticista
    agora = timezone.now()

    limite_confirmacao = agora + timedelta(minutes=15)
    agendamentos_para_confirmar = Agendamento.objects.filter(
      esteticista=esteticista,
      status="agendado",
      data_hora__lte=limite_confirmacao,
      data_hora__gt=agora,
    )

    agendamentos_para_iniciar = Agendamento.objects.filter(
      esteticista=esteticista, status="confirmado", data_hora__lte=agora
    )

    agendamentos_para_finalizar = []
    em_atendimento = Agendamento.objects.filter(
      esteticista=esteticista, status="em_atendimento"
    )

    for agendamento in em_atendimento:
      if agendamento.hora_fim <= agora:
        agendamentos_para_finalizar.append(agendamento)

    resultado = []

    for agendamento in agendamentos_para_confirmar:
      resultado.append(
        {
          "id": agendamento.pk,
          "cliente": agendamento.cliente.nome,
          "servico": agendamento.servico.nome,
          "horario": timezone.localtime(agendamento.data_hora).strftime(
            "%H:%M"
          ),
          "acao": "confirmar",
          "status_atual": "agendado",
          "proximo_status": "confirmado",
          "mensagem": f'O cliente {agendamento.cliente.nome} confirmou presença para às {timezone.localtime(agendamento.data_hora).strftime("%H:%M")}?',
        }
      )

    for agendamento in agendamentos_para_iniciar:
      resultado.append(
        {
          "id": agendamento.pk,
          "cliente": agendamento.cliente.nome,
          "servico": agendamento.servico.nome,
          "horario": timezone.localtime(agendamento.data_hora).strftime(
            "%H:%M"
          ),
          "acao": "iniciar",
          "status_atual": "confirmado",
          "proximo_status": "em_atendimento",
          "mensagem": f"Iniciar atendimento de {agendamento.cliente.nome}?",
        }
      )

    for agendamento in agendamentos_para_finalizar:
      resultado.append(
        {
          "id": agendamento.pk,
          "cliente": agendamento.cliente.nome,
          "servico": agendamento.servico.nome,
          "horario": timezone.localtime(agendamento.data_hora).strftime(
            "%H:%M"
          ),
          "acao": "finalizar",
          "status_atual": "em_atendimento",
          "proximo_status": "concluido",
          "mensagem": f"Concluir atendimento de {agendamento.cliente.nome}?",
        }
      )

    return JsonResponse({"success": True, "agendamentos": resultado})

  except Exception as e:
    return JsonResponse({"success": False, "message": str(e)}, status=500)

@login_required
def verificar_atualizacao_dashboard(request):
  ultima_alteracao = (
    Agendamento.objects
    .exclude(status="cancelado")
    .order_by("-atualizado_em")
    .first()
  )

  if not ultima_alteracao:
    return JsonResponse({"atualizar": False})

  last_check_str = request.GET.get("last_check")

  if last_check_str:
    last_check = parse_datetime(last_check_str)

    if last_check is None:
      return JsonResponse({"atualizar": False})

    if timezone.is_naive(last_check):
      last_check = timezone.make_aware(last_check)

    if ultima_alteracao.atualizado_em > last_check:
      return JsonResponse({"atualizar": True})

  return JsonResponse({
    "atualizar": False,
    "server_time": timezone.now().isoformat()
  })
