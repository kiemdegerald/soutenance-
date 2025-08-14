from django.contrib import admin
from .models import User, Famille, MembreFamille, FicheVictime, DemandeAide, JournalAction

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")

@admin.register(Famille)
class FamilleAdmin(admin.ModelAdmin):
    list_display = ("id", "adresse", "ville", "nombre_personnes")
    search_fields = ("adresse", "ville")

@admin.register(MembreFamille)
class MembreFamilleAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "famille", "date_naissance", "lien_parente")
    search_fields = ("nom", "prenom", "lien_parente")
    list_filter = ("lien_parente",)

@admin.register(FicheVictime)
class FicheVictimeAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "grade", "date_deces", "famille", "cree_par")
    search_fields = ("nom", "prenom", "grade")
    list_filter = ("grade", "date_deces")

@admin.register(DemandeAide)
class DemandeAideAdmin(admin.ModelAdmin):
    list_display = ("id", "famille", "type_demande", "statut", "cree_par", "valide_par", "date_creation", "date_validation")
    list_filter = ("type_demande", "statut")
    search_fields = ("famille__adresse", "famille__ville", "description")

@admin.register(JournalAction)
class JournalActionAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "action", "date_action")
    search_fields = ("utilisateur__username", "action", "details")
