from django.contrib import admin
from .models import Esteticista, Cliente, Servico, Agendamento, Notificacao


@admin.register(Esteticista)
class EsteticistaAdmin(admin.ModelAdmin):
  list_display = ["user", "telefone"]
  search_fields = ["user__username", "user__first_name", "user__last_name"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
  list_display = ["nome", "telefone", "email", "criado_em"]
  search_fields = ["nome", "telefone", "email"]
  list_filter = ["criado_em"]
  ordering = ["nome"]


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
  list_display = ["nome", "duracao_minutos", "preco", "ativo"]
  search_fields = ["nome"]
  list_filter = ["ativo"]
  ordering = ["nome"]


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
  list_display = [
    "cliente",
    "esteticista",
    "servico",
    "data_hora",
    "status",
    "criado_em",
  ]
  search_fields = ["cliente__nome", "esteticista__user__username"]
  list_filter = ["status", "data_hora", "esteticista"]
  date_hierarchy = "data_hora"
  ordering = ["-data_hora"]

  fieldsets = (
    ("Informações Básicas", {"fields": ("esteticista", "cliente", "servico")}),
    ("Agendamento", {"fields": ("data_hora", "duracao_minutos", "status")}),
    ("Observações", {"fields": ("observacoes",), "classes": ("collapse",)}),
  )


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
  list_display = ["esteticista", "tipo", "lida", "criada_em"]
  search_fields = ["esteticista__user__username", "mensagem"]
  list_filter = ["tipo", "lida", "criada_em"]
  ordering = ["-criada_em"]
