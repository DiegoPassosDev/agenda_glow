from django.urls import path
from . import views

urlpatterns = [
  path("", views.login_view, name="login"),
  path("logout/", views.logout_view, name="logout"),
  path("dashboard/", views.dashboard, name="dashboard"),
  path("agendamento/novo/", views.criar_agendamento, name="criar_agendamento"),
  path("agendamento/<int:pk>/editar/", views.editar_agendamento, name="editar_agendamento"),
  path("agendamento/<int:pk>/cancelar/", views.cancelar_agendamento, name="cancelar_agendamento"),
  path("agendamento/<int:pk>/atualizar-status/", views.atualizar_status_agendamento, name="atualizar_status_agendamento"),
  path("verificar-agendamentos-pendentes/", views.verificar_agendamentos_pendentes, name="verificar_agendamentos_pendentes"),
  path("clientes/", views.clientes_list, name="clientes_list"),
  path("clientes/novo/", views.cliente_create, name="cliente_create"),
  path("clientes/<int:pk>/editar/", views.cliente_edit, name="cliente_edit"),
  path("servicos/", views.servicos_list, name="servicos_list"),
  path("servicos/novo/", views.servico_create, name="servico_create"),
  path("servicos/<int:pk>/editar/", views.servico_edit, name="servico_edit"),
  path("servicos/<int:pk>/toggle/", views.servico_toggle_ativo, name="servico_toggle_ativo"),
  path("notificacao/<int:pk>/lida/", views.marcar_notificacao_lida, name="marcar_notificacao_lida"),
  path("dashboard/verificar-atualizacao/", views.verificar_atualizacao_dashboard, name="verificar_atualizacao_dashboard"),
]
