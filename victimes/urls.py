from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('familles/', views.famille_list, name='famille_list'),
    path('familles/ajouter/', views.famille_create, name='famille_create'),
    path('familles/ajouter/victime/<int:victime_id>/', views.famille_create, name='famille_create_victime'),
    path('familles/<int:pk>/modifier/', views.famille_update, name='famille_update'),
    path('familles/<int:pk>/supprimer/', views.famille_delete, name='famille_delete'),
    path('victimes/', views.victime_list, name='victime_list'),
    path('victimes/ajouter/', views.victime_create, name='victime_create'),
    path('demandes/', views.demande_list, name='demande_list'),
    path('suivi-aides/', views.suivi_aides, name='suivi_aides'),
    path('familles/<int:famille_id>/membre/ajouter/', views.membre_create, name='membre_create'),
    path('familles/<int:famille_id>/detail/', views.famille_detail_modal, name='famille_detail_modal'),
    path('demandes/ajouter/', views.demande_create, name='demande_create'),
    path('demandes/<int:demande_id>/valider/', views.demande_valider, name='demande_valider'),
    path('demandes/<int:demande_id>/refuser/', views.demande_refuser, name='demande_refuser'),
    path('demandes/validation/', views.demandes_a_valider, name='demandes_a_valider'),
    path('rapport/', views.rapport_familles_aidees, name='rapport_familles_aidees'),
    # URLs AJAX pour ajouter famille et membres depuis la liste des victimes
    path('famille/ajouter/', views.ajouter_famille_ajax, name='ajouter_famille_ajax'),
    path('membre/ajouter/', views.ajouter_membre_ajax, name='ajouter_membre_ajax'),
    # URL AJAX pour récupérer les détails d'une victime
    path('victime/details/<int:victime_id>/', views.victime_details_ajax, name='victime_details_ajax'),
    # URL AJAX pour modifier une victime
    path('victime/modifier/<int:victime_id>/', views.victime_modifier_ajax, name='victime_modifier_ajax'),
    # URL AJAX pour créer une demande d'aide
    path('demande/creer/', views.demande_create_ajax, name='demande_create_ajax'),
    # URLs pour l'administration
    path('administration/utilisateurs/', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('administration/journal/', views.journal_actions, name='journal_actions'),
    path('administration/utilisateur/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
]
