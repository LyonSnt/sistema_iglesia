from django import forms

from .models import DocumentoAdjunto, choices_tipos_documento_permitidos


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class DocumentoAdjuntoForm(forms.ModelForm):
    class Meta:
        model = DocumentoAdjunto
        fields = ("archivo", "nombre", "tipo", "descripcion")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, objeto=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.objeto = objeto
        self.user = user
        self.fields["tipo"].choices = choices_tipos_documento_permitidos(objeto)
        aplicar_estilos(self.fields.values())

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.iglesia = obtener_iglesia_objeto(self.objeto)
        instance.content_object = self.objeto
        instance.subido_por = self.user
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class AnularDocumentoAdjuntoForm(forms.Form):
    motivo = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}))


def aplicar_estilos(fields):
    for field in fields:
        if not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs.setdefault("class", FIELD_CLASS)


def obtener_iglesia_objeto(objeto):
    if hasattr(objeto, "iglesia"):
        return objeto.iglesia
    if hasattr(objeto, "iglesia_origen"):
        return objeto.iglesia_origen
    raise AttributeError("El objeto asociado no define una iglesia para el documento.")
