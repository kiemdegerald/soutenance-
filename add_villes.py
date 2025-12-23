import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gendarmerie.settings')
django.setup()

from victimes.models import MembreFamille

# Villes du Burkina Faso
villes = ['Ouagadougou', 'Bobo-Dioulasso', 'Koudougou', 'Ouahigouya', 'Banfora', 'Dédougou', 'Kaya', 'Ouagadougou']

# Liens de parenté
liens = ['Père', 'Mère', 'Fils', 'Fille', 'Frère', 'Sœur', 'Oncle', 'Tante']

membres = MembreFamille.objects.all().order_by('id')

print(f"Mise à jour de {membres.count()} membres avec des villes et liens de parenté...\n")

for i, membre in enumerate(membres):
    ville = villes[i % len(villes)]
    lien = liens[i % len(liens)]
    
    membre.ville = ville
    membre.lien_parente = lien
    membre.save()
    print(f"✓ {membre.prenom} {membre.nom}: Ville={ville}, Lien={lien}")

print(f"\n✅ Mise à jour terminée!")
print(f"Actualisez votre page d'administration pour voir les filtres Ville et Lien de parenté.")
