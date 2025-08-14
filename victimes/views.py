# Imports nécessaires
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from .decorators import role_required
from .models import Famille, MembreFamille, FicheVictime, DemandeAide, JournalAction, User
from .forms import FamilleForm, MembreFamilleForm, FicheVictimeForm, DemandeAideForm

# Vue pour détail AJAX famille/victime/membres
@login_required
def famille_detail_modal(request, famille_id):
    famille = get_object_or_404(Famille, pk=famille_id)
    victimes = famille.victimes.all()
    membres = famille.membres.all()
    return render(request, 'victimes/famille_detail_modal.html', {
        'famille': famille,
        'victimes': victimes,
        'membres': membres,
    })

# Liste des demandes à valider (pour responsable/admin)
@role_required(['responsable', 'admin'])
def demandes_a_valider(request):
    demandes = DemandeAide.objects.filter(statut='soumise')
    return render(request, 'victimes/demandes_a_valider.html', {'demandes': demandes})

# Rapport statistique simple
@role_required(['responsable', 'admin', 'agent', 'assistant', 'admin'])
def rapport_familles_aidees(request):
    nb_familles = Famille.objects.filter(demandes__statut='validee').distinct().count()
    return render(request, 'victimes/rapport.html', {'nb_familles': nb_familles})

# Validation des demandes (responsable/admin)
@role_required(['responsable', 'admin'])
def demande_valider(request, demande_id):
    demande = get_object_or_404(DemandeAide, pk=demande_id)
    if demande.statut != 'validee':
        demande.statut = 'validee'
        demande.valide_par = request.user
        demande.date_validation = timezone.now()
        demande.save()
        # Journalisation
        JournalAction.objects.create(
            utilisateur=request.user,
            action="Validation de demande",
            details=f"Demande {demande.id} validée pour la famille {demande.famille.id}"
        )
        messages.success(request, "Demande validée avec succès.")
    else:
        messages.info(request, "Cette demande est déjà validée.")
    return redirect('famille_list')

# Famille CRUD
@role_required(['agent', 'responsable', 'admin'])
def famille_list(request):
    if request.user.role == 'agent':
        # Les agents ne voient que les familles des victimes qu'ils ont créées
        familles = Famille.objects.filter(victimes__cree_par=request.user).distinct()
    else:
        # Les responsables et admins voient toutes les familles
        familles = Famille.objects.all()
    return render(request, 'victimes/famille_list.html', {'familles': familles})

@role_required(['agent', 'responsable', 'admin'])
def famille_create(request, victime_id=None):
    if request.method == 'POST':
        form = FamilleForm(request.POST)
        if form.is_valid():
            famille = form.save()
            # Journalisation
            JournalAction.objects.create(
                utilisateur=request.user,
                action="Création famille",
                details=f"Famille créée à {famille.ville} ({famille.id})"
            )
            # Si la création de famille fait suite à une création de victime, lier la victime à la famille
            if victime_id:
                from .models import FicheVictime
                victime = FicheVictime.objects.get(id=victime_id)
                victime.famille = famille
                victime.save()
            messages.success(request, "Famille ajoutée. Veuillez maintenant ajouter les membres de la famille.")
            return redirect('membre_create', famille_id=famille.id)
    else:
        form = FamilleForm()
    return render(request, 'victimes/famille_form.html', {'form': form})

@role_required(['agent', 'responsable', 'admin'])
def famille_update(request, pk):
    famille = get_object_or_404(Famille, pk=pk)
    # Vérifier que l'agent ne peut modifier que les familles de ses propres victimes
    if request.user.role == 'agent' and not famille.victimes.filter(cree_par=request.user).exists():
        raise PermissionDenied("Vous ne pouvez modifier que les familles des victimes que vous avez créées.")
    
    if request.method == 'POST':
        form = FamilleForm(request.POST, instance=famille)
        if form.is_valid():
            form.save()
            messages.success(request, "Famille modifiée.")
            return redirect('famille_list')
    else:
        form = FamilleForm(instance=famille)
    return render(request, 'victimes/famille_form.html', {'form': form})

@role_required(['responsable', 'admin'])  # Seuls responsables et admins peuvent supprimer
def famille_delete(request, pk):
    famille = get_object_or_404(Famille, pk=pk)
    if request.method == 'POST':
        famille.delete()
        messages.success(request, "Famille supprimée.")
        return redirect('famille_list')
    return render(request, 'victimes/famille_confirm_delete.html', {'famille': famille})

# FicheVictime CRUD
@role_required(['agent', 'responsable', 'admin'])
def victime_list(request):
    if request.user.role == 'agent':
        # Les agents ne voient que leurs propres fiches victimes
        victimes = FicheVictime.objects.filter(cree_par=request.user).order_by('-date_creation')
    else:
        # Les responsables et admins voient toutes les fiches
        victimes = FicheVictime.objects.all().order_by('-date_creation')
    return render(request, 'victimes/victime_list.html', {'victimes': victimes})

@login_required  # Temporairement, on utilise juste login_required pour tester
@login_required
def victime_create(request):
    try:
        if request.method == 'POST':
            form = FicheVictimeForm(request.POST, request.FILES)
            if form.is_valid():
                victime = form.save(commit=False)
                victime.cree_par = request.user
                victime.save()
                # Journalisation
                JournalAction.objects.create(
                    utilisateur=request.user,
                    action="Création fiche victime",
                    details=f"Fiche victime créée pour {victime.prenom} {victime.nom}"
                )
                
                # Si c'est une requête AJAX (depuis le modal), retourner JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Fiche victime pour {victime.prenom} {victime.nom} créée avec succès!',
                        'victime_id': victime.id
                    })
                
                messages.success(request, "Fiche victime ajoutée avec succès!")
                return redirect('victime_list')  # Redirect vers la liste pour simplifier
            else:
                # Si c'est une requête AJAX avec des erreurs de validation
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    errors = {}
                    for field, error_list in form.errors.items():
                        errors[field] = [str(error) for error in error_list]
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez corriger les erreurs dans le formulaire.',
                        'errors': errors
                    })
        else:
            form = FicheVictimeForm()
        return render(request, 'victimes/victime_form.html', {'form': form})
    except Exception as e:
        # Si c'est une requête AJAX, retourner l'erreur en JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Une erreur est survenue: {str(e)}'
            })
        
        messages.error(request, f"Erreur: {str(e)}")
        form = FicheVictimeForm()
        return render(request, 'victimes/victime_form.html', {'form': form})

# MembreFamille CRUD (ajout rapide)
@role_required(['agent', 'responsable', 'admin'])
def membre_create(request, famille_id):
    famille = get_object_or_404(Famille, pk=famille_id)
    
    # Vérifier que l'agent ne peut ajouter que des membres aux familles de ses propres victimes
    if request.user.role == 'agent' and not famille.victimes.filter(cree_par=request.user).exists():
        raise PermissionDenied("Vous ne pouvez ajouter des membres qu'aux familles des victimes que vous avez créées.")
    
    if request.method == 'POST':
        form = MembreFamilleForm(request.POST)
        if form.is_valid():
            membre = form.save(commit=False)
            membre.famille = famille
            membre.save()
            # Journalisation
            JournalAction.objects.create(
                utilisateur=request.user,
                action="Ajout membre famille",
                details=f"Membre {membre.prenom} {membre.nom} ajouté à la famille {famille.id}"
            )
            messages.success(request, "Membre ajouté à la famille.")
            return redirect('famille_list')
    else:
        form = MembreFamilleForm()
    return render(request, 'victimes/membre_form.html', {'form': form, 'famille': famille})

# DemandeAide CRUD (création)
@login_required
def demande_list(request):
    demandes = DemandeAide.objects.all().order_by('-date_creation')
    return render(request, 'victimes/demande_list.html', {'demandes': demandes})

@role_required(['assistant'])
def demande_create(request):
    if request.method == 'POST':
        form = DemandeAideForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.cree_par = request.user
            demande.save()
            messages.success(request, "Demande d'aide soumise.")
            return redirect('famille_list')
    else:
        form = DemandeAideForm()
    return render(request, 'victimes/demande_form.html', {'form': form})


# Dashboard
@login_required
def dashboard_view(request):
    # Statistiques générales
    total_victimes = FicheVictime.objects.count()
    nouveaux_dossiers = FicheVictime.objects.filter(
        date_creation__month=timezone.now().month,
        date_creation__year=timezone.now().year
    ).count()
    affaires_resolues = DemandeAide.objects.filter(statut='validee').count()
    
    # Calcul du taux de résolution
    total_demandes = DemandeAide.objects.count()
    taux_resolution = (affaires_resolues / total_demandes * 100) if total_demandes > 0 else 0
    
    # Activités récentes (dernières actions du journal)
    activites_recentes = JournalAction.objects.order_by('-date_action')[:10]
    
    # Statistiques spécifiques par rôle
    if request.user.role == 'agent':
        # Statistiques agent
        mes_fiches = FicheVictime.objects.filter(cree_par=request.user).count()
        mes_familles = Famille.objects.filter(victimes__cree_par=request.user).distinct().count()
        mes_activites = JournalAction.objects.filter(utilisateur=request.user).order_by('-date_action')[:5]
        
        context = {
            'mes_fiches': mes_fiches,
            'mes_familles': mes_familles,
            'mes_activites': mes_activites,
            'en_attente': 3,  # Exemple
            'taux_completion': 94,  # Exemple
        }
        return render(request, 'victimes/dashboard_agent.html', context)
    
    # Dashboard général pour autres rôles
    context = {
        'total_victimes': total_victimes,
        'nouveaux_dossiers': nouveaux_dossiers,
        'affaires_resolues': affaires_resolues,
        'taux_resolution': round(taux_resolution, 1),
        'activites_recentes': activites_recentes,
    }
    
    return render(request, 'victimes/dashboard.html', context)

# Authentification
from .forms_auth import LoginForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue {user.username} !")
            return redirect('dashboard')
        else:
            messages.error(request, "Identifiants invalides.")
    else:
        form = LoginForm()
    return render(request, 'victimes/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Déconnexion réussie.")
    return redirect('login')

# Vues AJAX pour ajouter famille et membres depuis la liste des victimes
@role_required(['agent', 'responsable', 'admin'])
def ajouter_famille_ajax(request):
    if request.method == 'POST':
        try:
            victime_id = request.POST.get('victime_id')
            victime = get_object_or_404(FicheVictime, id=victime_id)
            
            # Vérifier que l'agent ne peut ajouter une famille qu'à ses propres victimes
            if request.user.role == 'agent' and victime.cree_par != request.user:
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez ajouter une famille qu\'aux victimes que vous avez créées.'})
            
            # Vérifier si la victime a déjà une famille
            if victime.famille:
                return JsonResponse({'success': False, 'message': 'Cette victime a déjà une famille associée.'})
            
            # Créer la famille
            famille = Famille.objects.create(
                nom_famille=request.POST.get('nom_famille'),
                type_famille=request.POST.get('type_famille', 'nucleaire'),
                adresse=request.POST.get('adresse', ''),
                telephone=request.POST.get('telephone', ''),
                situation_economique=request.POST.get('situation_economique', 'stable'),
                informations_complementaires=request.POST.get('informations_complementaires', '')
            )
            
            # Associer la famille à la victime
            victime.famille = famille
            victime.save()
            
            # Journalisation
            JournalAction.objects.create(
                utilisateur=request.user,
                action="Création famille via AJAX",
                details=f"Famille {famille.nom_famille} créée pour la victime {victime.prenom} {victime.nom} (ID: {famille.id})"
            )
            
            return JsonResponse({'success': True, 'message': 'Famille ajoutée avec succès.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors de la création de la famille: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@role_required(['agent', 'responsable', 'admin'])
def ajouter_membre_ajax(request):
    if request.method == 'POST':
        try:
            famille_id = request.POST.get('famille_id')
            famille = get_object_or_404(Famille, id=famille_id)
            
            # Vérifier que l'agent ne peut ajouter un membre qu'aux familles de ses propres victimes
            if request.user.role == 'agent' and not famille.victimes.filter(cree_par=request.user).exists():
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez ajouter des membres qu\'aux familles des victimes que vous avez créées.'})
            
            # Créer le membre
            membre = MembreFamille.objects.create(
                famille=famille,
                prenom=request.POST.get('prenom'),
                nom=request.POST.get('nom'),
                date_naissance=request.POST.get('date_naissance') or None,
                sexe=request.POST.get('sexe', 'M'),
                relation_victime=request.POST.get('relation_victime'),
                profession=request.POST.get('profession', ''),
                telephone=request.POST.get('telephone', ''),
                email=request.POST.get('email', ''),
                informations_complementaires=request.POST.get('informations_complementaires', '')
            )
            
            # Journalisation
            JournalAction.objects.create(
                utilisateur=request.user,
                action="Ajout membre famille via AJAX",
                details=f"Membre {membre.prenom} {membre.nom} ajouté à la famille {famille.nom_famille} (ID: {membre.id})"
            )
            
            return JsonResponse({'success': True, 'message': 'Membre ajouté avec succès.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors de l\'ajout du membre: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@role_required(['agent', 'responsable', 'admin'])
def victime_details_ajax(request, victime_id):
    """Vue AJAX pour récupérer les détails complets d'une victime"""
    try:
        victime = get_object_or_404(FicheVictime, id=victime_id)
        
        # Vérifier les permissions : agent ne peut voir que ses propres victimes
        if request.user.role == 'agent' and victime.cree_par != request.user:
            return JsonResponse({'success': False, 'message': 'Vous n\'avez pas l\'autorisation de voir cette victime.'})
        
        # Préparer les données de la victime
        victime_data = {
            'id': victime.id,
            'prenom': victime.prenom,
            'nom': victime.nom,
            'date_naissance': victime.date_naissance.strftime('%d/%m/%Y') if victime.date_naissance else None,
            'sexe': victime.get_sexe_display() if victime.sexe else None,
            'nationalite': victime.nationalite,
            'statut_civil': victime.get_statut_civil_display() if victime.statut_civil else None,
            'profession': victime.profession,
            'grade': victime.grade,
            'date_deces': victime.date_deces.strftime('%d/%m/%Y') if victime.date_deces else None,
            'date_deces_raw': victime.date_deces.strftime('%Y-%m-%d') if victime.date_deces else None,
            'lieu_deces': victime.lieu_deces,
            'acte_deces': victime.acte_deces.url if victime.acte_deces else None,
            'adresse': victime.adresse,
            'telephone': victime.telephone,
            'email': victime.email,
            'type_incident': victime.type_incident,
            'date_incident': victime.date_incident.strftime('%d/%m/%Y') if victime.date_incident else None,
            'lieu_incident': victime.lieu_incident,
            'description_incident': victime.description_incident,
            'cree_par': f"{victime.cree_par.first_name} {victime.cree_par.last_name}" if victime.cree_par.first_name or victime.cree_par.last_name else victime.cree_par.username,
            'date_creation': victime.date_creation.strftime('%d/%m/%Y à %H:%M') if victime.date_creation else None,
            'famille': None
        }
        
        # Ajouter les informations de la famille si elle existe
        if victime.famille:
            famille_data = {
                'id': victime.famille.id,
                'nom_famille': victime.famille.nom_famille,
                'type_famille': victime.famille.get_type_famille_display(),
                'adresse': victime.famille.adresse,
                'telephone': victime.famille.telephone,
                'situation_economique': victime.famille.get_situation_economique_display(),
                'membres': []
            }
            
            # Ajouter les membres de la famille
            for membre in victime.famille.membres.all():
                membre_data = {
                    'id': membre.id,
                    'prenom': membre.prenom,
                    'nom': membre.nom,
                    'date_naissance': membre.date_naissance.strftime('%d/%m/%Y') if membre.date_naissance else None,
                    'sexe': membre.get_sexe_display(),
                    'relation_victime': membre.relation_victime,
                    'relation_victime_display': membre.get_relation_victime_display(),
                    'profession': membre.profession,
                    'telephone': membre.telephone,
                    'email': membre.email
                }
                famille_data['membres'].append(membre_data)
            
            victime_data['famille'] = famille_data
        
        return JsonResponse({
            'success': True,
            'victime': victime_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la récupération des détails: {str(e)}'
        })


@role_required(['agent', 'responsable', 'admin'])
def victime_modifier_ajax(request):
    """Vue AJAX pour modifier une victime"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
    
    try:
        victime_id = request.POST.get('victime_id')
        victime = get_object_or_404(FicheVictime, id=victime_id)
        
        # Vérifier les permissions : agent ne peut modifier que ses propres victimes
        if request.user.role == 'agent' and victime.cree_par != request.user:
            return JsonResponse({'success': False, 'message': 'Vous n\'avez pas l\'autorisation de modifier cette victime.'})
        
        # Mettre à jour les champs
        victime.nom = request.POST.get('nom', victime.nom)
        victime.prenom = request.POST.get('prenom', victime.prenom)
        victime.grade = request.POST.get('grade', victime.grade)
        victime.lieu_deces = request.POST.get('lieu_deces', victime.lieu_deces)
        
        # Traitement de la date de décès
        date_deces = request.POST.get('date_deces')
        if date_deces:
            try:
                from datetime import datetime
                victime.date_deces = datetime.strptime(date_deces, '%Y-%m-%d').date()
            except ValueError:
                victime.date_deces = None
        
        # Traitement du fichier acte de décès
        if 'acte_deces' in request.FILES:
            victime.acte_deces = request.FILES['acte_deces']
        
        victime.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Victime modifiée avec succès.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la modification: {str(e)}'
        })
