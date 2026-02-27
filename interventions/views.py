from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from .email_service import InterventionEmailService
from .models import Intervention
from .forms import InterventionAdminForm, InterventionTechnicienForm
from clients.models import Client
from techniciens.models import Technicien
from .email_service import InterventionEmailService


@login_required
def intervention_list(request):
    """Liste toutes les interventions avec recherche et filtres"""

    # Vérifier si c'est un technicien (il ne voit que ses interventions)
    if hasattr(request.user, 'technicien'):
        interventions = Intervention.objects.filter(
            technicien=request.user.technicien
        ).select_related('client', 'technicien', 'fournisseur')
    else:
        # Admin voit toutes les interventions
        interventions = Intervention.objects.all().select_related(
            'client', 'technicien', 'fournisseur'
        )

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        interventions = interventions.filter(
            Q(client__nom__icontains=search_query) |
            Q(technicien__nom__icontains=search_query) |
            Q(fournisseur__nom__icontains=search_query)
        )

    # Filtres
    type_filter = request.GET.get('type')
    if type_filter:
        interventions = interventions.filter(type_intervention=type_filter)

    statut_filter = request.GET.get('statut')
    if statut_filter:
        interventions = interventions.filter(statut=statut_filter)

    # Pagination
    paginator = Paginator(interventions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'interventions': page_obj,
        'search_query': search_query,
        'type_filter': type_filter,
        'statut_filter': statut_filter,
        'type_choices': Intervention.TYPE_INTERVENTION_CHOICES,
        'statut_choices': Intervention.STATUT_CHOICES,
        'is_technicien': hasattr(request.user, 'technicien'),
    }
    return render(request, 'interventions/intervention_list.html', context)


@login_required
def intervention_detail(request, pk):
    """Détail d'une intervention"""
    intervention = get_object_or_404(
        Intervention.objects.select_related('client', 'technicien', 'fournisseur'),
        pk=pk
    )

    # Vérifier si le technicien peut voir cette intervention
    if hasattr(request.user, 'technicien'):
        if intervention.technicien != request.user.technicien:
            messages.error(request, 'Accès non autorisé à cette intervention.')
            return redirect('interventions:list')

    return render(request, 'interventions/intervention_detail.html', {
        'intervention': intervention,
        'duree_formatee': intervention.get_duree_formatee(),  # AJOUTER CETTE LIGNE
    })





@login_required
def intervention_create(request):
    """Créer une nouvelle intervention"""
    # Vérifier si c'est un technicien (accès interdit)
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = InterventionAdminForm(request.POST)
        if form.is_valid():
            intervention = form.save(commit=False)

            # Récupérer automatiquement le fournisseur du client
            client = form.cleaned_data['client']
            if client.fournisseur:
                intervention.fournisseur = client.fournisseur

            intervention.save()

            # Envoyer les emails de notification
            try:
                InterventionEmailService.envoyer_notification_creation(intervention, request)
                messages.success(request, 'Intervention créée avec succès et notifications envoyées!')
            except Exception as e:
                messages.warning(request, f'Intervention créée mais erreur lors de l\'envoi des emails: {str(e)}')

            return redirect('interventions:list')
    else:
        form = InterventionAdminForm()

    return render(request, 'interventions/intervention_form.html', {
        'form': form,
        'title': 'Créer une intervention'
    })


@login_required
def intervention_update(request, pk):
    """Modifier une intervention existante"""
    intervention = get_object_or_404(Intervention, pk=pk)

    # Vérifier si c'est un technicien (il ne peut modifier que ses interventions)
    if hasattr(request.user, 'technicien'):
        if intervention.technicien != request.user.technicien:
            messages.error(request, 'Accès non autorisé à cette intervention.')
            return redirect('interventions:list')

        # Technicien : utiliser le formulaire restreint
        form_class = InterventionTechnicienForm
        template_extra = 'technicien'
    else:
        # Admin : utiliser le formulaire complet
        form_class = InterventionAdminForm
        template_extra = 'admin'

    # Sauvegarder l'ancien statut pour l'email
    ancien_statut = intervention.statut

    if request.method == 'POST':
        form = form_class(request.POST, instance=intervention)
        if form.is_valid():
            # Si le client change, mettre à jour le fournisseur (seulement pour admin)
            if 'client' in form.changed_data and not hasattr(request.user, 'technicien'):
                client = form.cleaned_data['client']
                if client.fournisseur:
                    intervention.fournisseur = client.fournisseur

            intervention = form.save()

            # Envoyer un email en cas de changement de statut
            try:
                InterventionEmailService.envoyer_notification_statut(intervention, ancien_statut, request)
            except Exception as e:
                messages.warning(request, f'Mise à jour réussie mais erreur email: {str(e)}')

            messages.success(request, 'Intervention mise à jour avec succès!')
            return redirect('interventions:list')
    else:
        form = form_class(instance=intervention)

    return render(request, 'interventions/intervention_form.html', {
        'form': form,
        'title': 'Modifier une intervention',
        'template_extra': template_extra
    })



@login_required
def intervention_delete(request, pk):
    """Supprimer une intervention"""

    intervention = get_object_or_404(Intervention, pk=pk)

    # Vérifier si c'est un technicien (accès interdit)
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    if request.method == 'POST':
        intervention.delete()
        messages.success(request, 'Intervention supprimée avec succès!')
        return redirect('interventions:list')

    return render(request, 'interventions/intervention_confirm_delete.html', {
        'intervention': intervention
    })


# Vue API pour récupérer le fournisseur d'un client (AJAX)
@login_required
def get_client_fournisseur(request, client_id):
    """Retourne le fournisseur d'un client en JSON (pour AJAX)"""
    try:
        client = Client.objects.get(id=client_id)
        fournisseur = client.fournisseur
        return JsonResponse({
            'success': True,
            'fournisseur_nom': fournisseur.nom if fournisseur else 'Non spécifié',
            'fournisseur_id': fournisseur.id if fournisseur else None,
            'client_kva': client.extraire_kva() if hasattr(client, 'extraire_kva') else None
        })
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Client non trouvé'}, status=404)


@login_required
def get_prix_intervention_api(request, client_id):
    """API pour calculer le prix d'intervention"""
    try:
        client = Client.objects.get(id=client_id)
        type_intervention = request.GET.get('type', '')

        kva = client.extraire_kva() if hasattr(client, 'extraire_kva') else None

        if kva:
            from utils import calculer_prix_par_kva_et_type
            prix = calculer_prix_par_kva_et_type(kva, type_intervention)

            return JsonResponse({
                'success': True,
                'kva': kva,
                'prix': prix,
                'type_intervention': type_intervention,
                'client_nom': client.nom
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Client sans KVA valide'
            })
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Client non trouvé'})