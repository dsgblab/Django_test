from django import forms
from .models import PvoRegistro


class PvoRegistroForm(forms.ModelForm):
    class Meta:
        model = PvoRegistro
        exclude = ['creado_por', 'fecha_creacion']
        widgets = {
            'pid': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'fecha_full': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_flp': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fef': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
