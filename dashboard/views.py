from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.contrib import messages

from clients.models import Client
from techniciens.models import Technicien
from interventions.models import Intervention


@login_required
def dashboard_view(request):
    """
    Vue principale du dashboard - différente selon le type d'utilisateur
    """
    # Vérifier si l'utilisateur a un profil technicien
    is_technicien = hasattr(request.user, 'technicien')

    if is_technicien:
        technicien = request.user.technicien
        return technicien_dashboard(request, technicien)
    else:
        return admin_dashboard(request)


def admin_dashboard(request):
    """
    Dashboard pour l'administrateur - VOIT TOUTES LES STATS
    """
    # Toutes les interventions (tous statuts)
    toutes_interventions = Intervention.objects.all()

    # Statistiques globales
    total_interventions = toutes_interventions.count()
    interventions_en_cours = toutes_interventions.filter(statut='en_cours').count()
    interventions_terminees = toutes_interventions.filter(statut='terminee').count()
    interventions_annulees = toutes_interventions.filter(statut='annulee').count()
    interventions_prevues = toutes_interventions.filter(statut='prevue').count()

    # Revenus totaux (terminées seulement)
    revenus_totaux = toutes_interventions.filter(statut='terminee').aggregate(
        total=Sum('prix_intervention')
    )['total'] or 0

    # TOTAL de TOUTES les interventions (tous statuts) - NOUVEAU
    total_toutes_interventions = toutes_interventions.aggregate(
        total=Sum('prix_intervention')
    )['total'] or 0

    # Autres statistiques
    total_clients = Client.objects.count()
    total_techniciens = Technicien.objects.count()

    # Date d'aujourd'hui pour les comparaisons
    aujourdhui = datetime.now().date()

    # Prochaines interventions (toutes) - modifié pour mieux filtrer
    date_limite = aujourdhui + timedelta(days=30)
    prochaines_interventions = toutes_interventions.filter(
        Q(statut='prevue') | Q(statut='en_cours')
    ).filter(
        date_intervention__lte=date_limite
    ).select_related('client', 'technicien').order_by('-date_intervention')[:10]

    # Interventions récentes
    interventions_recentes = toutes_interventions.select_related(
        'client', 'technicien'
    ).order_by('-date_intervention')[:10]

    context = {
        'title': 'Tableau de Bord Administrateur',
        'page_title': 'Tableau de Bord Administrateur',
        'total_clients': total_clients,
        'total_techniciens': total_techniciens,
        'total_interventions': total_interventions,
        'revenus_totaux': revenus_totaux,
        'total_toutes_interventions': total_toutes_interventions,  # NOUVEAU
        'interventions_en_cours': interventions_en_cours,
        'interventions_terminees': interventions_terminees,
        'interventions_annulees': interventions_annulees,
        'interventions_prevues': interventions_prevues,
        'prochaines_interventions': prochaines_interventions,
        'interventions_recentes': interventions_recentes,
        'aujourdhui': aujourdhui,  # NOUVEAU - pour vérifier les retards
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


def technicien_dashboard(request, technicien):
    """
    Page d'accueil pour les techniciens - UNIQUEMENT SES INTERVENTIONS
    """
    # Interventions assignées à CE technicien
    interventions_assignees = Intervention.objects.filter(
        technicien=technicien
    ).select_related('client').order_by('-date_intervention')

    # Statistiques pour CE technicien uniquement
    interventions_total = interventions_assignees.count()
    interventions_en_cours = interventions_assignees.filter(statut='en_cours').count()
    interventions_terminees = interventions_assignees.filter(statut='terminee').count()
    interventions_annulees = interventions_assignees.filter(statut='annulee').count()
    interventions_prevues = interventions_assignees.filter(statut='prevue').count()

    # Date d'aujourd'hui pour les comparaisons
    aujourdhui = datetime.now().date()

    # Prochaines interventions (pour CE technicien)
    date_limite = aujourdhui + timedelta(days=30)
    prochaines_interventions = interventions_assignees.filter(
        Q(statut='prevue') | Q(statut='en_cours')
    ).filter(
        date_intervention__lte=date_limite
    ).order_by('-date_intervention')[:10]

    # Interventions en retard
    interventions_en_retard = interventions_assignees.filter(
        date_intervention__lt=aujourdhui,
        statut__in=['en_cours', 'prevue']
    )

    context = {
        'title': 'Mon Espace Technicien',
        'page_title': 'Mon Espace Technicien',
        'technicien': technicien,
        'interventions_total': interventions_total,
        'interventions_en_cours': interventions_en_cours,
        'interventions_terminees': interventions_terminees,
        'interventions_annulees': interventions_annulees,
        'interventions_prevues': interventions_prevues,
        'prochaines_interventions': prochaines_interventions,
        'interventions_en_retard': interventions_en_retard,
        'aujourdhui': aujourdhui,  # NOUVEAU
    }

    return render(request, 'dashboard/technicien_dashboard.html', context)


# ============ VUES TEMPORAIRES CORRIGÉES ============


@login_required
def technicien_list_view(request):
    """
    Redirige vers la vraie vue de gestion des techniciens
    """
    return redirect('technicien_list')


@login_required
def intervention_list_view(request):
    """
    Vue temporaire pour les interventions - TOUT LE MONDE
    """
    # Vérifier si c'est un technicien pour personnaliser le message
    if hasattr(request.user, 'technicien'):
        message = "Cette section est en cours de développement. Vous pourrez voir et gérer vos interventions ici."
    else:
        message = "Cette section est en cours de développement. Vous pourrez gérer toutes les interventions ici."

    return render(request, 'dashboard/temp_page.html', {
        'title': 'Interventions',
        'page_title': 'Gestion des Interventions',
        'message': message
    })