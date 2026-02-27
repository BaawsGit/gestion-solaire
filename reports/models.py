from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Report(models.Model):
    title = models.CharField(max_length=200)
    month = models.DateField()  # Stocke le mois/année du rapport

    # Statistiques
    total_interventions = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    success_rate = models.FloatField(default=0.0)  # en pourcentage

    # NOUVEAUX CHAMPS
    customer_satisfaction_score = models.FloatField(default=0.0)  # Score sur 10
    avg_intervention_duration = models.FloatField(null=True, blank=True)  # en heures

    # Analyse IA
    summary = models.TextField()
    recommendations = models.TextField()
    technical_analysis = models.TextField()
    predictive_maintenance = models.TextField()

    # Métadonnées
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)

    # Données brutes
    statistics_data = models.JSONField(default=dict, blank=True)
    ai_raw_response = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.title} ({self.month.strftime('%B %Y')})"

    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Rapport IA"
        verbose_name_plural = "Rapports IA"

    def get_statistics(self):
        """Retourne les statistiques sous forme de dictionnaire"""
        if isinstance(self.statistics_data, str):
            try:
                return json.loads(self.statistics_data)
            except:
                return {}
        return self.statistics_data or {}

    def get_success_rate_display(self):
        """Retourne le taux de réussite formaté"""
        return f"{self.success_rate:.1f}%"

    def get_avg_duration_display(self):
        """Retourne la durée moyenne formatée de manière lisible"""
        if not self.avg_intervention_duration:
            return "N/A"

        total_seconds = int(self.avg_intervention_duration * 3600)

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

    def get_performance_score_display(self):
        """Retourne le score de performance formaté (pas satisfaction client!)"""
        return f"{self.customer_satisfaction_score:.1f}/10"