from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.usuarios.politicas import ROLES_AUTORIDAD_FILIAL

from .models import Iglesia


FIELD_CLASS = "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950"


class IglesiaFormMixin:
    def aplicar_estilos(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300")
            else:
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean_codigo(self):
        return self.cleaned_data["codigo"].strip().upper()


class IglesiaUpdateForm(IglesiaFormMixin, forms.ModelForm):
    class Meta:
        model = Iglesia
        fields = (
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "email",
            "zona",
            "estado",
            "responsable_principal",
            "activo",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].disabled = bool(self.instance.pk)
        self.aplicar_estilos()


class NuevaFilialForm(IglesiaFormMixin, forms.ModelForm):
    responsable_username = forms.CharField(label="Usuario del responsable")
    responsable_nombres = forms.CharField(label="Nombres del responsable")
    responsable_apellidos = forms.CharField(label="Apellidos del responsable")
    responsable_email = forms.EmailField(label="Correo del responsable", required=False)
    responsable_rol = forms.ChoiceField(
        label="Autoridad inicial",
        choices=[(rol, Usuario.Rol(rol).label) for rol in ROLES_AUTORIDAD_FILIAL],
    )
    password1 = forms.CharField(label="Contrasena temporal", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)

    class Meta:
        model = Iglesia
        fields = (
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "email",
            "zona",
            "responsable_principal",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos()

    def clean_responsable_username(self):
        username = self.cleaned_data["responsable_username"].strip()
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Ya existe un usuario con este nombre.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("Las contrasenas no coinciden.")
        if cleaned_data.get("password1"):
            validate_password(cleaned_data["password1"])
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        iglesia = super().save(commit=False)
        iglesia.tipo = Iglesia.Tipo.FILIAL
        iglesia.iglesia_matriz = Iglesia.objects.get(codigo="NACIONAL")
        iglesia.estado = Iglesia.Estado.ACTIVA
        iglesia.activo = True
        if not commit:
            return iglesia

        iglesia.save()
        usuario = Usuario.objects.create_user(
            username=self.cleaned_data["responsable_username"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["responsable_nombres"],
            last_name=self.cleaned_data["responsable_apellidos"],
            email=self.cleaned_data["responsable_email"],
            rol=self.cleaned_data["responsable_rol"],
            iglesia=iglesia,
            is_staff=False,
            debe_cambiar_password=True,
        )
        usuario.groups.set([Group.objects.get(name=usuario.rol)])
        return iglesia
