from django import forms
from .models import Famille, MembreFamille, FicheVictime, DemandeAide

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

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
    actes_deces = MultipleFileField(required=False, label="Acte(s) de décès")
    rapports_medicaux = MultipleFileField(required=False, label="Rapport(s) médical(aux)")
    
    class Meta:
        model = FicheVictime
        fields = ['nom', 'prenom', 'matricule', 'photo', 'grade', 'date_deces', 'lieu_deces', 'statut_victime']
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
