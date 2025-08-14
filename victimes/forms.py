from django import forms
from .models import Famille, MembreFamille, FicheVictime, DemandeAide

class FamilleForm(forms.ModelForm):
    class Meta:
        model = Famille
        fields = ['adresse', 'ville', 'nombre_personnes']
        widgets = {
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_personnes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MembreFamilleForm(forms.ModelForm):
    class Meta:
        model = MembreFamille
        fields = ['nom', 'prenom', 'date_naissance', 'lien_parente']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lien_parente': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FicheVictimeForm(forms.ModelForm):
    class Meta:
        model = FicheVictime
        fields = ['nom', 'prenom', 'grade', 'date_deces', 'lieu_deces', 'acte_deces']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'date_deces': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_deces': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DemandeAideForm(forms.ModelForm):
    class Meta:
        model = DemandeAide
        fields = ['famille', 'type_demande', 'description']
        widgets = {
            'famille': forms.Select(attrs={'class': 'form-control'}),
            'type_demande': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
