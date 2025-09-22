from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Person, Visit, Sede, Estructura
import base64
import re
from datetime import datetime

class PersonForm(forms.ModelForm):
    photo_data_url = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Person
        fields = ['dni', 'nombre', 'apellido', 'telefono', 'email', 'tarjetavisita', 'observaciones']
        widgets = {
            'dni': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese DNI', 'required': 'required'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese nombre', 'required': 'required'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese apellido', 'required': 'required'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese email'}),
            'tarjetavisita': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de tarjeta', 'required': 'required'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingrese observaciones'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos obligatorios
        self.fields['dni'].required = True
        self.fields['nombre'].required = True
        self.fields['apellido'].required = True
        self.fields['tarjetavisita'].required = True
        
    def clean(self):
        cleaned_data = super().clean()
        # Solo exigir foto si es nuevo
        photo_data_url = cleaned_data.get('photo_data_url')
        if not self.instance.pk and not photo_data_url:
            self.add_error('photo_data_url', 'La foto es obligatoria')
        return cleaned_data

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['fecha', 'hora_entrada', 'sede', 'area', 'receptor_nombre', 'receptor_apellido', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_entrada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sede': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'area': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'receptor_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de quien recibe', 'required': 'required'}),
            'receptor_apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido de quien recibe', 'required': 'required'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingrese observaciones'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('fecha'):
            self.initial['fecha'] = timezone.now().date()
        if not self.initial.get('hora_entrada'):
            self.initial['hora_entrada'] = timezone.now().time().strftime('%H:%M')
        
        # Configurar todas las áreas activas ordenadas por unidad orgánica
        self.fields['area'].queryset = Estructura.objects.filter(activo=True).order_by('unidad_organica')
        
        # Hacer campos obligatorios
        self.fields['area'].required = True
        self.fields['receptor_nombre'].required = True
        self.fields['receptor_apellido'].required = True

# Formularios para administración
class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EstructuraForm(forms.ModelForm):
    class Meta:
        model = Estructura
        fields = ['unidad_organica', 'siglas', 'padre', 'activo']
        widgets = {
            'unidad_organica': forms.TextInput(attrs={'class': 'form-control'}),
            'siglas': forms.TextInput(attrs={'class': 'form-control'}),
            'padre': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate padre choices with active areas
        areas = Estructura.objects.filter(padre__isnull=True, activo=True)
        self.fields['padre'].choices = [('', '---------')] + [(area.siglas, area.unidad_organica) for area in areas]
        self.fields['padre'].required = False
