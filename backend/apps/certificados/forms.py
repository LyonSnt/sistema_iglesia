from django import forms


class AnularCertificadoForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo de anulacion",
        min_length=5,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm",
            }
        ),
    )
