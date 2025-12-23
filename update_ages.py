import os
import django
from datetime import date, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gendarmerie.settings')
django.setup()

from victimes.models import MembreFamille

# Dates de naissance pour créer différents âges
dates_naissance = [
    ("2016-03-15", 9),   # 9 ans
    ("2010-05-20", 15),  # 15 ans
    ("2005-08-10", 20),  # 20 ans
    ("1995-11-25", 30),  # 30 ans
    ("1990-02-14", 35),  # 35 ans
    ("1985-07-30", 40),  # 40 ans
    ("1975-04-18", 50),  # 50 ans
    ("1965-09-22", 60),  # 60 ans
]

membres = MembreFamille.objects.filter(date_naissance__isnull=False).order_by('id')

print(f"Mise à jour de {min(len(membres), len(dates_naissance))} membres avec des âges variés...\n")

for i, membre in enumerate(membres[:len(dates_naissance)]):
    date_str, age_attendu = dates_naissance[i]
    ancien_age = membre.age
    # Convertir la chaîne en objet date
    membre.date_naissance = datetime.strptime(date_str, '%Y-%m-%d').date()
    membre.save()
    print(f"✓ {membre.prenom} {membre.nom}: {ancien_age} ans → {membre.age} ans (né(e) le {date_str})")

print(f"\n✅ Mise à jour terminée!")
print(f"\nVous pouvez maintenant actualiser votre page d'administration.")
