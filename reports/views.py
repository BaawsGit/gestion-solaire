from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
import calendar

from interventions.models import Intervention
from techniciens.models import Technicien
from .models import Report
from .ollama_service import OllamaService


# ==================== FONCTIONS UTILITAIRES ====================

def generate_manual_recommendations(stats):
    """Génère des recommandations manuelles basées sur les statistiques"""
    recommendations = []

    # Basé sur le taux de réussite
    success_rate = stats.get('success_rate', 0)
    if success_rate < 70:
        recommendations.append("Améliorer le taux de réussite en formant les techniciens sur les pannes fréquentes.")
    elif success_rate > 90:
        recommendations.append("Maintenir l'excellence opérationnelle actuelle.")

    # Basé sur la durée moyenne
    avg_duration = stats.get('avg_duration_hours')
    if avg_duration and avg_duration > 4:
        recommendations.append("Optimiser les temps d'intervention en standardisant les procédures.")

    # Basé sur le nombre d'interventions
    total_interventions = stats.get('total_interventions', 0)
    if total_interventions > 50:
        recommendations.append("Considérer l'embauche d'un technicien supplémentaire pour gérer la charge.")

    # Recommandations par défaut
    if not recommendations:
        recommendations = [
            "Maintenir un stock suffisant de pièces de rechange courantes.",
            "Planifier des maintenances préventives pour les installations de plus de 2 ans.",
            "Former régulièrement les techniciens sur les nouvelles technologies solaires."
        ]

    return "\n".join([f"- {rec}" for rec in recommendations])


def format_duration(hours_float):
    """Formate une durée en heures décimales en format lisible"""
    if hours_float is None:
        return "N/A"

    total_seconds = int(hours_float * 3600)

    # Si c'est moins d'une minute, afficher en secondes
    if total_seconds < 60:
        return f"{total_seconds} secondes"

    # Si c'est moins d'une heure, afficher en minutes
    if total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if seconds > 0:
            return f"{minutes} minutes {seconds} secondes"
        return f"{minutes} minutes"

    # Pour les durées plus longues, afficher en heures et minutes
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if minutes > 0:
        return f"{hours} heures {minutes} minutes"
    return f"{hours} heures"


# ==================== VUES PRINCIPALES ====================

@login_required
def report_list(request):
    """Liste tous les rapports générés"""
    reports = Report.objects.all().order_by('-generated_at')

    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Vérifier la connexion Ollama
    ollama = OllamaService()
    connection_result = ollama.check_connection()

    context = {
        'page_title': 'Rapports IA',
        'reports': page_obj,
        'ollama_available': connection_result.get('available', False)
    }
    return render(request, 'reports/report_list.html', context)


@login_required
def generate_report(request):
    """Génère un rapport IA pour un mois donné"""

    # Générer les listes de mois et années
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    current_year = datetime.now().year
    years = range(current_year - 2, current_year + 3)  # 3 dernières années

    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        # Vérifier la connexion Ollama d'abord
        ollama = OllamaService()
        connection = ollama.check_connection()

        if not connection.get('available', False):
            messages.error(request,
                           "Ollama n'est pas connecté. "
                           "Vérifiez que le serveur Ollama est en cours d'exécution: "
                           "<code>ollama serve</code>"
                           )
            return render(request, 'reports/generate_report.html', {
                'page_title': 'Générer un rapport IA',
                'months': months,
                'years': years,
                'current_month': month,
                'current_year': year
            })

        # Vérifier que le modèle est disponible
        if not connection.get('model_available', False):
            # Recommander un modèle léger
            messages.warning(request,
                             f"Le modèle '{ollama.model_name}' n'est pas disponible. "
                             "Essayez un modèle plus léger: "
                             "<code>ollama pull phi3</code> ou <code>ollama pull gemma3:4b</code>"
                             )
            return render(request, 'reports/generate_report.html', {
                'page_title': 'Générer un rapport IA',
                'months': months,
                'years': years,
                'current_month': month,
                'current_year': year
            })

        # Filtrer les interventions pour le mois et l'année sélectionnés
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        interventions = Intervention.objects.filter(
            date_intervention__date__gte=start_date.date(),
            date_intervention__date__lte=end_date.date()
        )

        # ==================== CALCULS STATISTIQUES ====================
        total_interventions = interventions.count()

        # Si pas d'interventions, on peut arrêter ici
        if total_interventions == 0:
            messages.warning(request, f"Aucune intervention trouvée pour {start_date.strftime('%B %Y')}")
            return redirect('reports:report_list')

        # Interventions terminées
        completed_interventions = interventions.filter(statut='terminee').count()

        # Taux de réussite
        success_rate = 0
        if total_interventions > 0:
            success_rate = (completed_interventions / total_interventions) * 100

        # Score de performance interne (sur 10) - PAS satisfaction client!
        performance_score = round(success_rate / 10, 1)

        # Durée moyenne (avec la nouvelle méthode get_duree_totale)
        interventions_completed = interventions.filter(statut='terminee')
        total_duration = timedelta()
        count_with_duration = 0

        for intervention in interventions_completed:
            duree = intervention.get_duree_totale() if hasattr(intervention, 'get_duree_totale') else None
            if duree:
                total_duration += duree
                count_with_duration += 1

        avg_duration_display = "N/A"
        avg_duration_hours = None
        if count_with_duration > 0:
            avg_duration_seconds = total_duration.total_seconds() / count_with_duration
            avg_duration_hours = avg_duration_seconds / 3600
            avg_duration_display = format_duration(avg_duration_hours)

        # Chiffre d'affaires total
        total_revenue = interventions.aggregate(
            total=Sum('prix_intervention')
        )['total'] or 0

        # Répartition par type
        interventions_by_type = interventions.values('type_intervention').annotate(
            count=Count('id')
        ).order_by('-count')

        # Top techniciens
        top_technicians = interventions.exclude(technicien=None).values(
            'technicien__nom', 'technicien__id'
        ).annotate(
            intervention_count=Count('id')
        ).order_by('-intervention_count')[:5]

        # Préparer les statistiques pour l'IA
        stats = {
            'total_interventions': total_interventions,
            'completed_interventions': completed_interventions,
            'ongoing_interventions': interventions.filter(statut='en_cours').count(),
            'success_rate': success_rate,
            'performance_score': performance_score,  # CHANGÉ DE satisfaction_score À performance_score
            'avg_duration': avg_duration_display,
            'avg_duration_hours': avg_duration_hours,
            'total_revenue': float(total_revenue),
            'interventions_by_type': list(interventions_by_type),
            'top_technicians': list(top_technicians),
            'month': month,
            'year': year
        }

        # Générer l'analyse IA
        try:
            ai_result = ollama.generate_report_analysis(month, year, stats)

            if ai_result.get('success', False):
                sections = ai_result.get('sections', {})

                # Créer le rapport
                report = Report(
                    title=f"Rapport {calendar.month_name[month]} {year}",
                    month=start_date.date(),
                    generated_by=request.user,
                    total_interventions=total_interventions,
                    total_revenue=total_revenue,
                    success_rate=success_rate,
                    customer_satisfaction_score=performance_score,  # Garder le même nom dans le modèle
                    avg_intervention_duration=avg_duration_hours,
                    summary=sections.get('summary', 'Analyse IA non disponible.'),
                    recommendations=sections.get('recommendations', ''),
                    technical_analysis=sections.get('technical_analysis', ''),
                    predictive_maintenance=sections.get('predictive_maintenance', ''),
                    statistics_data=json.dumps(stats, default=str),
                    ai_raw_response=json.dumps(ai_result, default=str)
                )

                report.save()

                messages.success(request, f"Rapport #{report.id} généré avec succès!")
                return redirect('reports:report_detail', pk=report.id)
            else:
                # Créer un rapport avec analyse manuelle
                error_msg = ai_result.get('error', 'Erreur inconnue')
                messages.warning(request,
                                 f"Rapport généré avec des statistiques, mais l'IA a échoué: {error_msg}. "
                                 "Les recommandations ont été générées manuellement."
                                 )

                # Générer des recommandations manuelles basées sur les stats
                manual_recommendations = generate_manual_recommendations(stats)  # CORRIGÉ: plus de self

                report = Report(
                    title=f"Rapport {calendar.month_name[month]} {year} (sans IA)",
                    month=start_date.date(),
                    generated_by=request.user,
                    total_interventions=total_interventions,
                    total_revenue=total_revenue,
                    success_rate=success_rate,
                    customer_satisfaction_score=performance_score,
                    avg_intervention_duration=avg_duration_hours,
                    summary=f"Rapport statistique pour {calendar.month_name[month]} {year}. "
                            f"Analyse IA indisponible: {error_msg}",
                    recommendations=manual_recommendations,
                    technical_analysis="Analyse technique non disponible (erreur IA).",
                    predictive_maintenance="Prédictions non disponibles (erreur IA).",
                    statistics_data=json.dumps(stats, default=str),
                    ai_raw_response=json.dumps(ai_result, default=str)
                )

                report.save()
                return redirect('reports:report_detail', pk=report.id)

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du rapport: {str(e)}")
            return render(request, 'reports/generate_report.html', {
                'page_title': 'Générer un rapport IA',
                'months': months,
                'years': years,
                'current_month': month,
                'current_year': year
            })

    # GET request: afficher le formulaire
    current_month = datetime.now().month
    current_year = datetime.now().year

    return render(request, 'reports/generate_report.html', {
        'page_title': 'Générer un rapport IA',
        'months': months,
        'years': years,
        'current_month': current_month,
        'current_year': current_year
    })


# ... (les autres vues restent les mêmes)



@login_required
def report_detail(request, pk):
    """Affiche les détails d'un rapport"""
    report = get_object_or_404(Report, pk=pk)

    context = {
        'page_title': f'Rapport #{report.id}',
        'report': report
    }
    return render(request, 'reports/report_detail.html', context)


@login_required
def report_delete(request, pk):
    """Supprime un rapport"""
    report = get_object_or_404(Report, pk=pk)

    if request.method == 'POST':
        report.delete()
        messages.success(request, f"Rapport #{pk} supprimé avec succès!")
        return redirect('reports:report_list')

    return render(request, 'reports/report_confirm_delete.html', {
        'page_title': 'Supprimer le rapport',
        'report': report
    })


# ==================== NOUVELLES VUES POUR API ====================

@login_required
def check_ollama_status(request):
    """API pour vérifier la connexion à Ollama (utilisée par le bouton)"""
    ollama = OllamaService()
    connection_result = ollama.check_connection()

    return JsonResponse(connection_result)


@login_required
def test_ollama_connection(request):
    """Page pour tester la connexion Ollama"""
    ollama = OllamaService()
    connection_result = ollama.check_connection()
    model_test = None

    if connection_result.get('success'):
        model_test = ollama.test_model()

    return render(request, 'reports/test_connection.html', {
        'page_title': 'Tester la connexion Ollama',
        'connection': connection_result,
        'model_test': model_test
    })


# Dans reports/views.py
@login_required
def ollama_config(request):
    """Page de configuration d'Ollama"""
    if request.method == 'POST':
        model_name = request.POST.get('model_name', 'phi3')
        base_url = request.POST.get('base_url', 'http://localhost:11434')

        # Tester la configuration
        ollama = OllamaService(base_url=base_url)
        ollama.model_name = model_name

        connection = ollama.check_connection()

        if connection.get('available'):
            messages.success(request,
                             f"Configuration réussie! Modèle: {model_name}, URL: {base_url}"
                             )
        else:
            messages.error(request,
                           f"Échec de la configuration: {connection.get('message', 'Erreur inconnue')}"
                           )

    # Récupérer les modèles disponibles
    ollama = OllamaService()
    connection = ollama.check_connection()
    available_models = connection.get('models', [])

    return render(request, 'reports/ollama_config.html', {
        'page_title': 'Configuration Ollama',
        'available_models': available_models,
        'current_model': ollama.model_name,
        'current_url': ollama.base_url,
        'connection': connection
    })