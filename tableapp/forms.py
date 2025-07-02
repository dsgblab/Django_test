from django import forms
from .models import Table1, Table2, PvoRegistro
from django.forms.widgets import DateTimeInput

class Table1Form(forms.ModelForm):
    class Meta:
        model = Table1
        fields = '__all__'

class Table2Form(forms.ModelForm):
    class Meta:
        model = Table2
        fields = '__all__'




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