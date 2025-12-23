from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Q
from datetime import date
from .models import User, Famille, MembreFamille, FicheVictime, DemandeAide, JournalAction, DocumentVictime

# Filtre personnalisé pour la ville avec toutes les villes de la base
class VilleFilter(admin.SimpleListFilter):
    title = 'Ville'
    parameter_name = 'ville'

    def lookups(self, request, model_admin):
        # Récupérer toutes les villes uniques des membres de famille
        villes = MembreFamille.objects.exclude(ville='').values_list('ville', flat=True).distinct().order_by('ville')
        return [(ville, ville) for ville in villes if ville]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ville=self.value())
        return queryset

# Filtre personnalisé pour le lien de parenté avec tous les liens de la base
class LienParenteFilter(admin.SimpleListFilter):
    title = 'Lien de parenté'
    parameter_name = 'lien_parente'

    def lookups(self, request, model_admin):
        # Récupérer tous les liens de parenté uniques
        liens = MembreFamille.objects.exclude(lien_parente='').values_list('lien_parente', flat=True).distinct().order_by('lien_parente')
        return [(lien, lien) for lien in liens if lien]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(lien_parente=self.value())
        return queryset

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    
    # Ajouter le champ role aux fieldsets existants
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role',)}),
    )
    
    # Ajouter le champ role lors de la création
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role',)}),
    )

@admin.register(Famille)
class FamilleAdmin(admin.ModelAdmin):
    list_display = ("id", "adresse", "ville", "nombre_personnes")
    search_fields = ("adresse", "ville")

@admin.register(MembreFamille)
class MembreFamilleAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "get_age", "ville", "famille", "date_naissance", "lien_parente")
    search_fields = ("nom", "prenom", "ville", "lien_parente")
    list_filter = (VilleFilter, LienParenteFilter, "sexe")
    ordering = ["-date_naissance"]  # Tri par défaut : plus jeunes en premier
    
    def get_age(self, obj):
        """Affiche l'âge calculé dans la liste"""
        if obj.age is not None:
            return f"{obj.age} ans"
        return "-"
    get_age.short_description = "Âge"
    get_age.admin_order_field = "-date_naissance"  # Tri inversé : plus récent = plus jeune
    
    # Recherche avancée par âge exact et ville
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Si le terme de recherche est un nombre, filtrer par âge
        if search_term.isdigit():
            age_recherche = int(search_term)
            today = date.today()
            annee_naissance = today.year - age_recherche
            
            # Filtrer les membres nés dans l'année correspondante (avec marge d'un an)
            queryset_age = self.model.objects.filter(
                Q(date_naissance__year=annee_naissance) | 
                Q(date_naissance__year=annee_naissance - 1)
            )
            queryset = queryset | queryset_age
        
        return queryset, use_distinct

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

@admin.register(DocumentVictime)
class DocumentVictimeAdmin(admin.ModelAdmin):
    list_display = ("victime", "type_document", "nom_fichier", "date_ajout")
    list_filter = ("type_document", "date_ajout")
    search_fields = ("victime__nom", "victime__prenom", "nom_fichier")
    readonly_fields = ("date_ajout",)
