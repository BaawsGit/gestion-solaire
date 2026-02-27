# interventions/views_calendar.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Intervention
from django.db.models import Q
from datetime import datetime


@login_required
def calendar_view(request):
    """Affiche le calendrier des interventions"""
    context = {
        'page_title': 'Calendrier des Interventions',
    }
    return render(request, 'interventions/calendar.html', context)


@login_required
def calendar_events(request):
    """API qui retourne les événements au format JSON pour FullCalendar"""

    # Récupérer les dates de début et fin depuis la requête
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')

    # Convertir les dates
    start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')) if start_str else None
    end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')) if end_str else None

    # Filtrer les interventions
    if hasattr(request.user, 'technicien'):
        # Technicien : seulement ses interventions
        interventions = Intervention.objects.filter(
            technicien=request.user.technicien
        )
    else:
        # Admin : toutes les interventions
        interventions = Intervention.objects.all()

    # Filtrer par période si spécifiée
    if start_date and end_date:
        interventions = interventions.filter(
            date_intervention__gte=start_date.date(),
            date_intervention__lte=end_date.date()
        )

    # Préparer les événements au format FullCalendar
    events = []
    for intervention in interventions:
        # Définir la couleur selon le statut
        color = '#3788d8'  # Bleu par défaut

        if intervention.statut == 'terminee':
            color = '#28a745'  # Vert
        elif intervention.statut == 'en_cours':
            color = '#ffc107'  # Jaune
        elif intervention.statut == 'annulee':
            color = '#dc3545'  # Rouge
        elif intervention.statut == 'prevue':
            color = '#6c757d'  # Gris

        # Créer l'événement
        event = {
            'id': intervention.id,
            'title': f"{intervention.client.nom} - {intervention.get_type_intervention_display()}",
            'start': intervention.date_intervention.isoformat(),
            'color': color,
            'textColor': '#ffffff',
            'borderColor': '#ffffff',
            'extendedProps': {
                'client': intervention.client.nom,
                'technicien': intervention.technicien.nom if intervention.technicien else 'Non assigné',
                'type': intervention.get_type_intervention_display(),
                'statut': intervention.get_statut_display(),
                'prix': str(intervention.prix_intervention),
                'url': f'/interventions/{intervention.id}/',
            }
        }
        events.append(event)

    return JsonResponse(events, safe=False)