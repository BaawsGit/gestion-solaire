from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Client, Fournisseur
from .forms import ClientForm, FournisseurForm, ClientSearchForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
def ajax_create_fournisseur(request):
    """
    Vue pour créer un fournisseur via AJAX (modal)
    """
    if hasattr(request.user, 'technicien'):
        return JsonResponse({
            'success': False,
            'error': 'Accès réservé aux administrateurs.'
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # VERIFIER si ce fournisseur existe déjà
            nom = data.get('nom')
            fournisseur_existant = Fournisseur.objects.filter(nom=nom).first()

            if fournisseur_existant:
                # SI existe déjà, on le retourne
                return JsonResponse({
                    'success': True,
                    'id': fournisseur_existant.id,
                    'nom': fournisseur_existant.nom,
                    'message': 'Fournisseur existant récupéré'
                })

            # Sinon, créer le nouveau fournisseur
            fournisseur = Fournisseur.objects.create(
                nom=data.get('nom'),
                adresse=data.get('adresse', ''),
                telephone=data.get('telephone', ''),
                email=data.get('email', ''),
            )

            return JsonResponse({
                'success': True,
                'id': fournisseur.id,
                'nom': fournisseur.nom
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })



@login_required
def client_list(request):
    """
    Liste tous les clients avec recherche et pagination
    """
    # Vérifier si c'est un technicien (accès interdit)
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    # Initialiser le formulaire de recherche
    search_form = ClientSearchForm(request.GET or None)
    clients = Client.objects.all().select_related('fournisseur').order_by('-id')

    # Appliquer la recherche si formulaire valide
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        if search_query:
            clients = clients.filter(
                Q(nom__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(telephone__icontains=search_query) |
                Q(adresse__icontains=search_query) |
                Q(type_installation__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

    # Pagination
    paginator = Paginator(clients, 10)  # 10 clients par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Gestion des Clients',
        'clients': page_obj,
        'search_form': search_form,
        'total_clients': clients.count(),
    }

    return render(request, 'clients/client_list.html', context)


@login_required
def client_detail(request, pk):
    """
    Affiche les détails d'un client
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    client = get_object_or_404(Client.objects.select_related('fournisseur'), pk=pk)

    # Récupérer les interventions de ce client
    interventions = client.interventions.all().select_related('technicien').order_by('-date_intervention')

    context = {
        'page_title': f'Détails Client - {client.nom}',
        'client': client,
        'interventions': interventions,
        'total_interventions': interventions.count(),
    }

    return render(request, 'clients/client_detail.html', context)


@login_required
def client_create(request):
    """
    Crée un nouveau client
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.nom}" créé avec succès!')
            return redirect('client_list')
    else:
        form = ClientForm()

    context = {
        'page_title': 'Ajouter un Nouveau Client',
        'form': form,
        'action': 'create',
    }

    return render(request, 'clients/client_form.html', context)


@login_required
def client_update(request, pk):
    """
    Modifie un client existant
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.nom}" modifié avec succès!')
            return redirect('client_detail', pk=client.id)
    else:
        form = ClientForm(instance=client)

    context = {
        'page_title': f'Modifier Client - {client.nom}',
        'form': form,
        'client': client,
        'action': 'update',
    }

    return render(request, 'clients/client_form.html', context)


@login_required
def client_delete(request, pk):
    """
    Supprime un client (avec confirmation)
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        client_nom = client.nom
        client.delete()
        messages.success(request, f'Client "{client_nom}" supprimé avec succès!')
        return redirect('client_list')

    context = {
        'page_title': 'Supprimer Client',
        'client': client,
    }

    return render(request, 'clients/client_confirm_delete.html', context)


@login_required
def fournisseur_list(request):
    """
    Liste tous les fournisseurs
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    fournisseurs = Fournisseur.objects.all().order_by('nom')

    context = {
        'page_title': 'Gestion des Fournisseurs',
        'fournisseurs': fournisseurs,
    }

    return render(request, 'clients/fournisseur_list.html', context)


@login_required
def fournisseur_detail(request, pk):
    """
    Affiche les détails d'un fournisseur
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    fournisseur = get_object_or_404(Fournisseur.objects.prefetch_related('clients'), pk=pk)

    # Récupérer les clients de ce fournisseur
    clients = fournisseur.clients.all()

    context = {
        'page_title': f'Détails Fournisseur - {fournisseur.nom}',
        'fournisseur': fournisseur,
        'clients': clients,
        'total_clients': clients.count(),
    }

    return render(request, 'clients/fournisseur_detail.html', context)


@login_required
def fournisseur_update(request, pk):
    """
    Modifie un fournisseur existant
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            fournisseur = form.save()
            messages.success(request, f'Fournisseur "{fournisseur.nom}" modifié avec succès!')
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)

    context = {
        'page_title': f'Modifier Fournisseur - {fournisseur.nom}',
        'form': form,
        'fournisseur': fournisseur,
        'action': 'update',
    }

    return render(request, 'clients/fournisseur_form.html', context)


@login_required
def fournisseur_delete(request, pk):
    """
    Supprime un fournisseur (avec confirmation)
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    clients_count = fournisseur.clients.count()

    if request.method == 'POST':
        # Vérification supplémentaire via POST
        if 'confirm_delete' not in request.POST:
            messages.error(request, 'Veuillez confirmer la suppression.')
            return redirect('fournisseur_detail', pk=pk)

        nom_fournisseur = fournisseur.nom
        fournisseur.delete()
        messages.success(request, f'Fournisseur "{nom_fournisseur}" supprimé avec succès!')
        return redirect('fournisseur_list')

    context = {
        'page_title': 'Supprimer Fournisseur',
        'fournisseur': fournisseur,
        'clients_count': clients_count,
    }

    return render(request, 'clients/fournisseur_confirm_delete.html', context)