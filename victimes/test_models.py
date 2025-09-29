from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from victimes.models import FicheVictime, DemandeAide, Famille

User = get_user_model()



class DemandeAideValidationFunctionalTest(TestCase):
    def setUp(self):
        self.responsable = User.objects.create_user(
            username='responsable1',
            email='resp1@example.com',
            password='testpass123',
            role='responsable'
        )
        self.client.login(username='responsable1', password='testpass123')
        self.famille = Famille.objects.create(nom_famille='Famille Test')
        self.demande = DemandeAide.objects.create(
            famille=self.famille,
            type_demande='aide_financiere',
            statut='soumise'
        )

    def test_valider_demande_aide(self):
        print("Test fonctionnel : Validation d'une demande d'aide par un responsable")
        url = reverse('demande_valider', args=[self.demande.id])
        response = self.client.post(url)
        self.demande.refresh_from_db()
        self.assertEqual(response.status_code, 302)  # Redirection après validation
        self.assertEqual(self.demande.statut, 'validee')
        print("\033[92mSuccès : Demande d'aide validée avec succès\033[0m")
        print("\033[92mOK\033[0m")