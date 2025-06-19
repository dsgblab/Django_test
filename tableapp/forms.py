from django import forms
from .models import Table1, Table2

class Table1Form(forms.ModelForm):
    class Meta:
        model = Table1
        fields = '__all__'

class Table2Form(forms.ModelForm):
    class Meta:
        model = Table2
        fields = '__all__'
