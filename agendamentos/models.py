from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Esteticista(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  telefone = models.CharField(max_length=15, blank=True)
  foto = models.ImageField(upload_to="esteticistas/", blank=True, null=True)

  def __str__(self):
    return self.user.get_full_name() or self.user.username

  class Meta:
    verbose_name = "Esteticista"
    verbose_name_plural = "Esteticistas"


class Cliente(models.Model):
  nome = models.CharField(max_length=100)
  telefone = models.CharField(max_length=15)
  email = models.EmailField(blank=True)
  observacoes = models.TextField(blank=True)
  criado_em = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.nome

  class Meta:
    verbose_name = "Cliente"
    verbose_name_plural = "Clientes"
    ordering = ["nome"]

  def save(self, *args, **kwargs):
    if self.nome:
      self.nome = self.nome.upper()
    super().save(*args, **kwargs)


class Servico(models.Model):
  nome = models.CharField(max_length=100)
  duracao_minutos = models.IntegerField(help_text="Duração em minutos")
  preco = models.DecimalField(max_digits=10, decimal_places=2)
  descricao = models.TextField(blank=True)
  ativo = models.BooleanField(default=True)

  def __str__(self):
    return f"{self.nome} ({self.duracao_minutos} min)"

  class Meta:
    verbose_name = "Serviço"
    verbose_name_plural = "Serviços"
    ordering = ["nome"]

  def save(self, *args, **kwargs):
    if self.nome:
      self.nome = self.nome.upper()
    super().save(*args, **kwargs)


class Agendamento(models.Model):
  STATUS_CHOICES = [
    ("agendado", "Agendado"),
    ("confirmado", "Confirmado"),
    ("em_atendimento", "Em Atendimento"),
    ("concluido", "Concluído"),
    ("cancelado", "Cancelado"),
  ]

  esteticista = models.ForeignKey(
    Esteticista, on_delete=models.CASCADE, related_name="agendamentos"
  )
  cliente = models.ForeignKey(
    Cliente, on_delete=models.CASCADE, related_name="agendamentos"
  )
  servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
  data_hora = models.DateTimeField()
  duracao_minutos = models.IntegerField()
  status = models.CharField(
    max_length=20, choices=STATUS_CHOICES, default="agendado")
  observacoes = models.TextField(blank=True)
  criado_em = models.DateTimeField(auto_now_add=True)
  atualizado_em = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"{self.cliente.nome} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

  @property
  def hora_fim(self):
    return self.data_hora + timedelta(minutes=self.duracao_minutos)

  @property
  def esta_proximo(self):
    agora = timezone.now()
    diferenca = self.data_hora - agora
    return timedelta(0) <= diferenca <= timedelta(minutes=15)

  def save(self, *args, **kwargs):
    if not self.duracao_minutos:
      self.duracao_minutos = self.servico.duracao_minutos
    super().save(*args, **kwargs)

  class Meta:
    verbose_name = "Agendamento"
    verbose_name_plural = "Agendamentos"
    ordering = ["data_hora"]


class Notificacao(models.Model):
  TIPO_CHOICES = [
    ("lembrete", "Lembrete"),
    ("novo_agendamento", "Novo Agendamento"),
    ("cancelamento", "Cancelamento"),
  ]

  esteticista = models.ForeignKey(
    Esteticista, on_delete=models.CASCADE, related_name="notificacoes"
  )
  agendamento = models.ForeignKey(
    Agendamento, on_delete=models.CASCADE, null=True, blank=True
  )
  tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
  mensagem = models.TextField()
  lida = models.BooleanField(default=False)
  criada_em = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.tipo} - {self.esteticista}"

  class Meta:
    verbose_name = "Notificação"
    verbose_name_plural = "Notificações"
    ordering = ["-criada_em"]
