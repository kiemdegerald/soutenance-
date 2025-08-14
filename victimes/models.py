
from django.db import models
from django.contrib.auth.models import AbstractUser

# Rôles utilisateur
class User(AbstractUser):
    ROLE_CHOICES = [
        ("agent", "Agent Gendarmerie"),
        ("assistant", "Assistant Social"),
        ("responsable", "Responsable"),
        ("admin", "Administrateur"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="agent")


class Famille(models.Model):
    TYPE_FAMILLE_CHOICES = [
        ('nucleaire', 'Nucléaire'),
        ('elargie', 'Élargie'),
        ('monoparentale', 'Monoparentale'),
        ('recomposee', 'Recomposée'),
    ]
    
    SITUATION_ECONOMIQUE_CHOICES = [
        ('stable', 'Stable'),
        ('precaire', 'Précaire'),
        ('difficile', 'Difficile'),
        ('aisee', 'Aisée'),
    ]
    
    nom_famille = models.CharField(max_length=100, verbose_name="Nom de famille")
    type_famille = models.CharField(max_length=20, choices=TYPE_FAMILLE_CHOICES, default='nucleaire', verbose_name="Type de famille")
    adresse = models.TextField(blank=True, verbose_name="Adresse complète")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    situation_economique = models.CharField(max_length=20, choices=SITUATION_ECONOMIQUE_CHOICES, default='stable', verbose_name="Situation économique")
    informations_complementaires = models.TextField(blank=True, verbose_name="Informations complémentaires")
    nombre_personnes = models.PositiveIntegerField(default=1, verbose_name="Nombre de personnes")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Famille {self.nom_famille} - {self.ville}"


class MembreFamille(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    RELATION_CHOICES = [
        ('parent', 'Parent'),
        ('enfant', 'Enfant'),
        ('conjoint', 'Conjoint/Conjointe'),
        ('frere_soeur', 'Frère/Sœur'),
        ('grand_parent', 'Grand-parent'),
        ('petit_enfant', 'Petit-enfant'),
        ('oncle_tante', 'Oncle/Tante'),
        ('cousin', 'Cousin/Cousine'),
        ('autre', 'Autre'),
    ]
    
    famille = models.ForeignKey(Famille, related_name="membres", on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='M', verbose_name="Sexe")
    relation_victime = models.CharField(max_length=20, choices=RELATION_CHOICES, verbose_name="Relation avec la victime")
    profession = models.CharField(max_length=100, blank=True, verbose_name="Profession")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    informations_complementaires = models.TextField(blank=True, verbose_name="Informations complémentaires")
    # Champ de compatibilité avec l'ancien modèle
    lien_parente = models.CharField(max_length=50, blank=True, verbose_name="Lien de parenté (ancien)")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_relation_victime_display()})"



class FicheVictime(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    STATUT_CIVIL_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
        ('union_libre', 'Union libre'),
    ]
    
    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='M', verbose_name="Sexe")
    nationalite = models.CharField(max_length=100, blank=True, verbose_name="Nationalité")
    statut_civil = models.CharField(max_length=20, choices=STATUT_CIVIL_CHOICES, blank=True, verbose_name="Statut civil")
    profession = models.CharField(max_length=100, blank=True, verbose_name="Profession")
    
    # Coordonnées
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    # Informations de décès (champs existants)
    grade = models.CharField(max_length=100, blank=True, verbose_name="Grade")
    date_deces = models.DateField(null=True, blank=True, verbose_name="Date de décès")
    lieu_deces = models.CharField(max_length=100, blank=True, verbose_name="Lieu de décès")
    acte_deces = models.FileField(upload_to="actes_deces/", blank=True, null=True, verbose_name="Acte de décès")
    
    # Informations d'incident
    type_incident = models.CharField(max_length=100, blank=True, verbose_name="Type d'incident")
    description_incident = models.TextField(blank=True, verbose_name="Description de l'incident")
    date_incident = models.DateField(null=True, blank=True, verbose_name="Date de l'incident")
    lieu_incident = models.CharField(max_length=200, blank=True, verbose_name="Lieu de l'incident")
    
    # Relations
    famille = models.ForeignKey(Famille, related_name="victimes", on_delete=models.CASCADE, null=True, blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class DemandeAide(models.Model):
    TYPE_CHOICES = [
        ("scolaire", "Aide scolaire"),
        ("allocation", "Allocation"),
        ("logement", "Logement"),
        ("autre", "Autre"),
    ]
    STATUT_CHOICES = [
        ("planifiee", "Planifiée"),
        ("soumise", "Soumise"),
        ("validee", "Validée"),
        ("refusee", "Refusée"),
    ]
    famille = models.ForeignKey(Famille, related_name="demandes", on_delete=models.CASCADE)
    type_demande = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="planifiee")
    description = models.TextField(blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_creees")
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes_validees")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_type_demande_display()} - {self.famille}"


class JournalAction(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.utilisateur} - {self.action} - {self.date_action}"
