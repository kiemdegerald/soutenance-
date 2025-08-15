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
    
    if request.method == 'POST':
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
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Demande validée avec succès.'})
            else:
                messages.success(request, "Demande validée avec succès.")
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'Cette demande est déjà validée.'})
            else:
                messages.info(request, "Cette demande est déjà validée.")
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
    
    return redirect('famille_list')

# Refus des demandes (responsable/admin)
@role_required(['responsable', 'admin'])
def demande_refuser(request, demande_id):
    demande = get_object_or_404(DemandeAide, pk=demande_id)
    
    if request.method == 'POST':
        if demande.statut == 'soumise':
            demande.statut = 'refusee'
            demande.valide_par = request.user
            demande.date_validation = timezone.now()
            demande.save()
            # Journalisation
            JournalAction.objects.create(
                utilisateur=request.user,
                action="Refus de demande",
                details=f"Demande {demande.id} refusée pour la famille {demande.famille.id}"
            )
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Demande refusée avec succès.'})
            else:
                messages.success(request, "Demande refusée avec succès.")
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'Cette demande ne peut pas être refusée.'})
            else:
                messages.info(request, "Cette demande ne peut pas être refusée.")
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
    
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
@role_required(['agent', 'assistant', 'responsable', 'admin'])
def victime_list(request):
    if request.user.role == 'agent':
        # Les agents ne voient que leurs propres fiches victimes
        victimes = FicheVictime.objects.filter(cree_par=request.user).order_by('-date_creation')
    else:
        # Les assistants, responsables et admins voient toutes les fiches
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
@role_required(['assistant', 'responsable', 'admin'])
def demande_list(request):
    if request.user.role == 'assistant':
        # Pour les assistants sociaux, montrer les victimes avec leurs familles pour pouvoir créer des demandes
        victimes = FicheVictime.objects.filter(famille__isnull=False).order_by('-date_creation')
        demandes = DemandeAide.objects.all().order_by('-date_creation')
        context = {
            'victimes': victimes,
            'demandes': demandes,
            'show_victimes': True  # Flag pour indiquer qu'on montre les victimes
        }
        return render(request, 'victimes/demande_list.html', context)
    else:
        # Pour les responsables et admins, montrer seulement les demandes
        demandes = DemandeAide.objects.all().order_by('-date_creation')
        return render(request, 'victimes/demande_list.html', {'demandes': demandes})

@login_required
def suivi_aides(request):
    """Vue pour le suivi des aides avec filtrage par statut"""
    # Récupérer toutes les demandes triées par date de création
    demandes = DemandeAide.objects.all().select_related('famille', 'cree_par', 'valide_par').order_by('-date_creation')
    
    # Statistiques par statut
    stats = {
        'total': demandes.count(),
        'en_attente': demandes.filter(statut='soumise').count(),
        'validees': demandes.filter(statut='validee').count(),
        'refusees': demandes.filter(statut='refusee').count(),
    }
    
    # Filtrage par statut si demandé
    statut_filtre = request.GET.get('statut')
    if statut_filtre and statut_filtre in ['soumise', 'validee', 'refusee']:
        demandes = demandes.filter(statut=statut_filtre)
    
    context = {
        'demandes': demandes,
        'stats': stats,
        'statut_filtre': statut_filtre
    }
    
    return render(request, 'victimes/suivi_aides.html', context)

@role_required(['assistant', 'responsable', 'admin'])
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

@role_required(['assistant'])
def demande_create_ajax(request):
    """Vue AJAX pour créer une demande d'aide"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
    
    try:
        famille_id = request.POST.get('famille_id')
        famille = get_object_or_404(Famille, id=famille_id)
        
        # Créer la demande d'aide
        demande = DemandeAide.objects.create(
            famille=famille,
            type_demande=request.POST.get('type_demande'),
            description=request.POST.get('description'),
            statut='soumise',  # Statut par défaut
            cree_par=request.user
        )
        
        # Journalisation
        JournalAction.objects.create(
            utilisateur=request.user,
            action="Création demande d'aide via AJAX",
            details=f"Demande {demande.get_type_demande_display()} créée pour la famille {famille.nom_famille} (ID: {demande.id})"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Demande d\'aide soumise avec succès.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la création de la demande: {str(e)}'
        })


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
    
    elif request.user.role == 'assistant':
        # Statistiques assistant social
        mes_demandes = DemandeAide.objects.filter(cree_par=request.user).count()
        demandes_validees = DemandeAide.objects.filter(cree_par=request.user, statut='validee').count()
        demandes_en_attente = DemandeAide.objects.filter(cree_par=request.user, statut='soumise').count()
        demandes_refusees = DemandeAide.objects.filter(cree_par=request.user, statut='refusee').count()
        
        # Familles suivies (familles pour lesquelles j'ai créé des demandes)
        familles_suivies = Famille.objects.filter(demandes__cree_par=request.user).distinct().count()
        
        # Calcul du taux de validation de mes demandes
        taux_validation = (demandes_validees / mes_demandes * 100) if mes_demandes > 0 else 0
        
        # Mes activités récentes
        mes_activites = JournalAction.objects.filter(utilisateur=request.user).order_by('-date_action')[:5]
        
        # Demandes récentes créées par moi
        demandes_recentes = DemandeAide.objects.filter(cree_par=request.user).order_by('-date_creation')[:5]
        
        context = {
            'mes_demandes': mes_demandes,
            'demandes_validees': demandes_validees,
            'demandes_en_attente': demandes_en_attente,
            'demandes_refusees': demandes_refusees,
            'familles_suivies': familles_suivies,
            'taux_validation': round(taux_validation, 1),
            'mes_activites': mes_activites,
            'demandes_recentes': demandes_recentes,
        }
        return render(request, 'victimes/dashboard_assistant.html', context)
    
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
@role_required(['agent', 'assistant', 'responsable', 'admin'])
def ajouter_famille_ajax(request):
    if request.method == 'POST':
        try:
            victime_id = request.POST.get('victime_id')
            victime = get_object_or_404(FicheVictime, id=victime_id)
            
            # Vérifier que l'agent ne peut ajouter une famille qu'à ses propres victimes
            # Les assistants ne peuvent pas ajouter de familles
            if request.user.role == 'agent' and victime.cree_par != request.user:
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez ajouter une famille qu\'aux victimes que vous avez créées.'})
            elif request.user.role == 'assistant':
                return JsonResponse({'success': False, 'message': 'Les assistants sociaux ne peuvent pas créer de familles.'})
            
            # Vérifier si la victime a déjà une famille
            if victime.famille:
                return JsonResponse({'success': False, 'message': 'Cette victime a déjà une famille associée.'})
            
            # Créer la famille
            famille = Famille.objects.create(
                nom_famille=request.POST.get('nom_famille'),
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

@role_required(['agent', 'assistant', 'responsable', 'admin'])
def ajouter_membre_ajax(request):
    if request.method == 'POST':
        try:
            famille_id = request.POST.get('famille_id')
            famille = get_object_or_404(Famille, id=famille_id)
            
            # Vérifier que l'agent ne peut ajouter un membre qu'aux familles de ses propres victimes
            # Les assistants ne peuvent pas ajouter de membres
            if request.user.role == 'agent' and not famille.victimes.filter(cree_par=request.user).exists():
                return JsonResponse({'success': False, 'message': 'Vous ne pouvez ajouter des membres qu\'aux familles des victimes que vous avez créées.'})
            elif request.user.role == 'assistant':
                return JsonResponse({'success': False, 'message': 'Les assistants sociaux ne peuvent pas ajouter de membres aux familles.'})
            
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

@role_required(['agent', 'assistant', 'responsable', 'admin'])
def victime_details_ajax(request, victime_id):
    """Vue AJAX pour récupérer les détails complets d'une victime"""
    try:
        victime = get_object_or_404(FicheVictime, id=victime_id)
        
        # Vérifier les permissions : agent ne peut voir que ses propres victimes
        # Les assistants, responsables et admins peuvent voir toutes les victimes
        if request.user.role == 'agent' and victime.cree_par != request.user:
            return JsonResponse({'success': False, 'message': 'Vous n\'avez pas l\'autorisation de voir cette victime.'})
        
        # Préparer les données de la victime
        victime_data = {
            'id': victime.id,
            'nom_complet': f"{victime.prenom} {victime.nom}",
            'prenom': victime.prenom,
            'nom': victime.nom,
            'date_naissance': victime.date_naissance.strftime('%Y-%m-%d') if victime.date_naissance else '',
            'sexe': victime.sexe,
            'sexe_display': victime.get_sexe_display() if victime.sexe else None,
            'nationalite': victime.nationalite,
            'statut_civil': victime.statut_civil,
            'etat_civil': victime.get_statut_civil_display() if victime.statut_civil else '',
            'profession': victime.profession,
            'adresse': victime.adresse,
            'grade': victime.grade,
            'date_deces': victime.date_deces.strftime('%Y-%m-%d') if victime.date_deces else '',
            'date_deces_display': victime.date_deces.strftime('%d/%m/%Y') if victime.date_deces else None,
            'lieu_deces': victime.lieu_deces,
            'acte_deces': victime.acte_deces.url if victime.acte_deces else None,
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
def victime_modifier_ajax(request, victime_id):
    """Vue AJAX pour modifier une victime"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
    
    try:
        victime = get_object_or_404(FicheVictime, id=victime_id)
        
        # Vérifier les permissions : agent ne peut modifier que ses propres victimes
        if request.user.role == 'agent' and victime.cree_par != request.user:
            return JsonResponse({'success': False, 'message': 'Vous n\'avez pas l\'autorisation de modifier cette victime.'})
        
        # Mettre à jour les champs d'identité
        if 'nom_complet' in request.POST:
            nom_complet = request.POST.get('nom_complet', '').strip()
            if nom_complet:
                # Diviser le nom complet en prénom et nom
                parties = nom_complet.split(' ', 1)
                if len(parties) >= 2:
                    victime.prenom = parties[0]
                    victime.nom = parties[1]
                else:
                    victime.nom = parties[0]
                    
        if 'sexe' in request.POST:
            victime.sexe = request.POST.get('sexe', victime.sexe)
            
        # Traitement de la date de naissance
        if 'date_naissance' in request.POST:
            date_naissance = request.POST.get('date_naissance')
            if date_naissance:
                try:
                    from datetime import datetime
                    victime.date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
        if 'etat_civil' in request.POST:
            etat_civil = request.POST.get('etat_civil')
            if etat_civil:
                victime.statut_civil = etat_civil
        
        if 'grade' in request.POST:
            victime.grade = request.POST.get('grade', victime.grade)
        
        # Traitement de la date de décès
        if 'date_deces' in request.POST:
            date_deces = request.POST.get('date_deces')
            if date_deces:
                try:
                    from datetime import datetime
                    victime.date_deces = datetime.strptime(date_deces, '%Y-%m-%d').date()
                except ValueError:
                    pass
        
        if 'lieu_deces' in request.POST:
            victime.lieu_deces = request.POST.get('lieu_deces', victime.lieu_deces)
        
        # Traitement du fichier acte de décès
        if 'acte_deces' in request.FILES:
            victime.acte_deces = request.FILES['acte_deces']
        
        victime.save()
        
        # Journalisation
        JournalAction.objects.create(
            utilisateur=request.user,
            action="Modification fiche victime via AJAX",
            details=f"Fiche victime {victime.prenom} {victime.nom} modifiée (ID: {victime.id})"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Victime modifiée avec succès.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la modification: {str(e)}'
        })
