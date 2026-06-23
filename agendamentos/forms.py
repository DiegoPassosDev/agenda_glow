from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Agendamento, Cliente, Servico
from datetime import datetime, timedelta
from django.utils import timezone


class LoginForm(AuthenticationForm):
  username = forms.CharField(
    widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Usuário"})
  )
  password = forms.CharField(
    widget=forms.PasswordInput(
      attrs={"class": "form-input", "placeholder": "Senha"}
    )
  )


class ClienteForm(forms.ModelForm):
  class Meta:
    model = Cliente
    fields = ["nome", "telefone", "email", "observacoes"]
    widgets = {
      "nome": forms.TextInput(
        attrs={"class": "form-input", "placeholder": "Nome completo"}
      ),
      "telefone": forms.TextInput(
        attrs={"class": "form-input", "placeholder": "(00) 00000-0000"}
      ),
      "email": forms.EmailInput(
        attrs={"class": "form-input", "placeholder": "email@exemplo.com"}
      ),
      "observacoes": forms.Textarea(
        attrs={
          "class": "form-textarea",
          "placeholder": "Observações sobre o cliente",
          "rows": 3,
        }
      ),
    }


class AgendamentoForm(forms.ModelForm):
  data = forms.DateField(
    widget=forms.DateInput(attrs={"type": "date", "class": "form-input"})
  )
  hora = forms.TimeField(
    widget=forms.TimeInput(attrs={"type": "time", "class": "form-input"})
  )

  class Meta:
    model = Agendamento
    fields = ["cliente", "servico", "data", "hora", "status", "observacoes"]
    widgets = {
      "cliente": forms.Select(attrs={"class": "form-select"}),
      "servico": forms.Select(attrs={"class": "form-select"}),
      "status": forms.Select(attrs={"class": "form-select"}),
      "observacoes": forms.Textarea(
        attrs={
          "class": "form-textarea",
          "placeholder": "Observações do atendimento",
          "rows": 3,
        }
      ),
    }

  def __init__(self, *args, **kwargs):
    self.esteticista = kwargs.pop("esteticista", None)
    super().__init__(*args, **kwargs)

    self.fields["cliente"].queryset = Cliente.objects.all()
    self.fields["servico"].queryset = Servico.objects.filter(ativo=True)

    if not self.instance.pk and not self.is_bound:
      agora = timezone.localtime()
      self.initial["data"] = agora.date()
      self.initial["hora"] = agora.strftime("%H:%M")

  def clean(self):
    cleaned_data = super().clean()
    data = cleaned_data.get("data")
    hora = cleaned_data.get("hora")
    servico = cleaned_data.get("servico")

    if data and hora and servico:
      data_hora = timezone.make_aware(datetime.combine(data, hora))
      duracao = servico.duracao_minutos
      hora_fim = data_hora + timedelta(minutes=duracao)

      if data_hora < timezone.now():
        raise forms.ValidationError(
          "Não é possível criar um agendamento para uma data ou horário já passado."
        )

      conflitos = Agendamento.objects.filter(
        data_hora__lt=hora_fim
      ).exclude(status="cancelado")

      if self.instance and self.instance.pk:
        conflitos = conflitos.exclude(pk=self.instance.pk)

      for ag in conflitos:
        if ag.hora_fim > data_hora:
          raise forms.ValidationError(
            f"Já existe um agendamento de "
            f'{ag.cliente.nome} às {timezone.localtime(ag.data_hora).strftime("%H:%M")} '
            f'até {timezone.localtime(ag.hora_fim).strftime("%H:%M")} '
            f"(com {ag.esteticista}). "
            f"A sala estará ocupada neste período."
          )

    return cleaned_data

  def save(self, commit=True):
    agendamento = super().save(commit=False)
    data = self.cleaned_data["data"]
    hora = self.cleaned_data["hora"]
    agendamento.data_hora = timezone.make_aware(datetime.combine(data, hora))

    if commit:
      agendamento.save()
    return agendamento


class ServicoForm(forms.ModelForm):
  class Meta:
    model = Servico
    fields = ["nome", "duracao_minutos", "preco", "descricao", "ativo"]
    widgets = {
      "nome": forms.TextInput(
        attrs={
          "class": "form-input",
          "placeholder": "Ex: Limpeza de Pele, Massagem Relaxante, ...",
        }
      ),
      "duracao_minutos": forms.NumberInput(
        attrs={
          "class": "form-input",
          "placeholder": "Duração em minutos",
          "min": "1",
          "step": "1",
        }
      ),
      "preco": forms.NumberInput(
        attrs={
          "class": "form-input",
          "placeholder": "0.00",
          "step": "0.01",
          "min": "0",
        }
      ),
      "descricao": forms.Textarea(
        attrs={
          "class": "form-textarea",
          "placeholder": "Descrição do serviço",
          "rows": 3,
        }
      ),
      "ativo": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
    }
    labels = {
      "nome": "Nome do Serviço",
      "duracao_minutos": "Duração (minutos)",
      "preco": "Preço (R$)",
      "descricao": "Descrição",
      "ativo": "Serviço Ativo",
    }
