import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gendarmerie.settings')
django.setup()

from victimes.models import FicheVictime
from django.db.models import Count

# Trouver les INCO en double
doublons = (
    FicheVictime.objects.values('matricule')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

print(f"Nombre d'INCO en double: {doublons.count()}")
print("\nDétails des doublons:")

total_supprimes = 0

for doublon in doublons:
    matricule = doublon['matricule']
    count = doublon['count']
    print(f"\nINCO '{matricule}' apparaît {count} fois")
    
    # Récupérer toutes les victimes avec cet INCO
    victimes = FicheVictime.objects.filter(matricule=matricule).order_by('id')
    
    # Afficher les détails
    for i, v in enumerate(victimes, 1):
        print(f"  {i}. ID: {v.id}, Nom: {v.nom} {v.prenom}, Créé le: {v.date_creation}")
    
    # Garder la première, supprimer les autres
    victimes_a_supprimer = list(victimes[1:])
    if victimes_a_supprimer:
        print(f"  → Conservation de l'ID {victimes[0].id}, suppression de {len(victimes_a_supprimer)} doublon(s)")
        for v in victimes_a_supprimer:
            v.delete()
            total_supprimes += 1

print(f"\n{'='*50}")
print(f"Total: {total_supprimes} doublon(s) supprimé(s)")
print(f"{'='*50}")
