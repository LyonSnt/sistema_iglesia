from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia

from .models import Usuario
from .politicas import roles_asignables_por


FIELD_CLASS = "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950"


class UsuarioFormMixin:
    def configurar(self, actor):
        self.actor = actor
        self.fields["rol"].choices = [
            (rol, Usuario.Rol(rol).label) for rol in roles_asignables_por(actor)
        ]
        iglesias = Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).order_by("nombre")
        if not usuario_es_nacional(actor):
            iglesias = iglesias.filter(pk=actor.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        self.fields["iglesia"].queryset = iglesias
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300")
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        if not usuario_es_nacional(self.actor):
            cleaned_data["iglesia"] = self.actor.iglesia
        if cleaned_data.get("rol") not in roles_asignables_por(self.actor):
            raise ValidationError("No puede asignar el rol seleccionado.")
        return cleaned_data

    def guardar_datos(self, usuario):
        if not usuario_es_nacional(self.actor):
            usuario.iglesia = self.actor.iglesia
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.debe_cambiar_password = True
        usuario.save()
        grupo = Group.objects.get(name=usuario.rol)
        usuario.groups.set([grupo])
        return usuario


class UsuarioCreateForm(UsuarioFormMixin, forms.ModelForm):
    password1 = forms.CharField(label="Contrasena temporal", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "cedula",
            "telefono",
            "iglesia",
            "rol",
        )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.configurar(actor)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise ValidationError("Las contrasenas no coinciden.")
        validate_password(password1)
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        return self.guardar_datos(usuario) if commit else usuario


class UsuarioUpdateForm(UsuarioFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "cedula",
            "telefono",
            "iglesia",
            "rol",
            "is_active",
        )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].disabled = True
        self.configurar(actor)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        return self.guardar_datos(usuario) if commit else usuario


class RestablecerPasswordForm(forms.Form):
    password1 = forms.CharField(label="Nueva contrasena temporal", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contrasena", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("Las contrasenas no coinciden.")
        if cleaned_data.get("password1"):
            validate_password(cleaned_data["password1"])
        return cleaned_data
