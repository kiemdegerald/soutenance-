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
        fields = ['nom', 'prenom', 'date_naissance', 'ville', 'lien_parente']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ouagadougou'}),
            'lien_parente': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FicheVictimeForm(forms.ModelForm):
    class Meta:
        model = FicheVictime
        fields = ['nom', 'prenom', 'matricule', 'photo', 'grade', 'date_deces', 'lieu_deces', 'acte_deces', 'statut_victime']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INCO', 'required': True}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'date_deces': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_deces': forms.TextInput(attrs={'class': 'form-control'}),
            'statut_victime': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if not matricule:
            raise forms.ValidationError("Le champ INCO est obligatoire.")
        # Vérifier les doublons uniquement pour les nouvelles instances
        if not self.instance.pk:  # Nouvelle instance
            if FicheVictime.objects.filter(matricule=matricule).exists():
                raise forms.ValidationError(f"L'INCO '{matricule}' existe déjà dans la base de données.")
        return matricule

class DemandeAideForm(forms.ModelForm):
    class Meta:
        model = DemandeAide
        fields = ['famille', 'type_demande', 'description']
        widgets = {
            'famille': forms.Select(attrs={'class': 'form-control'}),
            'type_demande': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
