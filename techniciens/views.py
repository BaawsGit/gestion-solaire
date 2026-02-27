from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Technicien
from .forms import TechnicienForm, TechnicienSearchForm


@login_required
def technicien_list(request):
    """
    Liste tous les techniciens avec recherche et pagination
    """
    # Vérifier si c'est un technicien (accès interdit)
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    # Initialiser le formulaire de recherche
    search_form = TechnicienSearchForm(request.GET or None)
    techniciens = Technicien.objects.all().order_by('-id')

    # Appliquer la recherche si formulaire valide
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        if search_query:
            techniciens = techniciens.filter(
                Q(nom__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(telephone__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

    # Pagination
    paginator = Paginator(techniciens, 10)  # 10 techniciens par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Gestion des Techniciens',
        'techniciens': page_obj,
        'search_form': search_form,
        'total_techniciens': techniciens.count(),
    }

    return render(request, 'techniciens/technicien_list.html', context)


@login_required
def technicien_detail(request, pk):
    """
    Affiche les détails d'un technicien
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    technicien = get_object_or_404(Technicien.objects.select_related('user'), pk=pk)

    # Récupérer les interventions de ce technicien
    interventions = technicien.interventions.all().select_related('client').order_by('-date_intervention')

    # Statistiques des interventions
    interventions_total = interventions.count()
    interventions_en_cours = interventions.filter(statut='en_cours').count()
    interventions_terminees = interventions.filter(statut='terminee').count()
    interventions_annulees = interventions.filter(statut='annulee').count()
    interventions_prevues = interventions.filter(statut='prevue').count()

    context = {
        'page_title': f'Détails Technicien - {technicien.nom}',
        'technicien': technicien,
        'interventions': interventions[:10],  # 10 dernières
        'interventions_total': interventions_total,
        'interventions_en_cours': interventions_en_cours,
        'interventions_terminees': interventions_terminees,
        'interventions_annulees': interventions_annulees,
        'interventions_prevues': interventions_prevues,
    }

    return render(request, 'techniciens/technicien_detail.html', context)


@login_required
def technicien_create(request):
    """
    Crée un nouveau technicien
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = TechnicienForm(request.POST, request.FILES)
        if form.is_valid():
            technicien = form.save()
            messages.success(request, f'Technicien "{technicien.nom}" créé avec succès!')
            return redirect('technicien_list')
    else:
        form = TechnicienForm()

    context = {
        'page_title': 'Ajouter un Nouveau Technicien',
        'form': form,
        'action': 'create',
    }

    return render(request, 'techniciens/technicien_form.html', context)


@login_required
def technicien_update(request, pk):
    """
    Modifie un technicien existant
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    technicien = get_object_or_404(Technicien.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        form = TechnicienForm(request.POST, request.FILES, instance=technicien)
        if form.is_valid():
            technicien = form.save()
            messages.success(request, f'Technicien "{technicien.nom}" modifié avec succès!')
            return redirect('technicien_detail', pk=technicien.id)
    else:
        # Initialiser le formulaire avec les données existantes
        form = TechnicienForm(instance=technicien)

    context = {
        'page_title': f'Modifier Technicien - {technicien.nom}',
        'form': form,
        'technicien': technicien,
        'action': 'update',
    }

    return render(request, 'techniciens/technicien_form.html', context)


@login_required
def technicien_delete(request, pk):
    """
    Supprime un technicien (avec confirmation)
    """
    if hasattr(request.user, 'technicien'):
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    technicien = get_object_or_404(Technicien, pk=pk)

    if request.method == 'POST':
        technicien_nom = technicien.nom

        # Supprimer l'utilisateur Django associé
        if technicien.user:
            technicien.user.delete()
        else:
            technicien.delete()

        messages.success(request, f'Technicien "{technicien_nom}" supprimé avec succès!')
        return redirect('technicien_list')

    # Vérifier si le technicien a des interventions
    interventions_count = technicien.interventions.count()

    context = {
        'page_title': 'Supprimer Technicien',
        'technicien': technicien,
        'interventions_count': interventions_count,
    }

    return render(request, 'techniciens/technicien_confirm_delete.html', context)