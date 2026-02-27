from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'month_display',
        'total_interventions',
        'total_revenue_display',
        'success_rate_display',
        'customer_satisfaction_score',
        'generated_by_display',
        'generated_at'
    )

    list_filter = ('month', 'generated_by')
    search_fields = ('title', 'generated_by__username')
    date_hierarchy = 'generated_at'
    readonly_fields = (
        'generated_at',
        'statistics_data_display',
        'ai_raw_response_display'
    )

    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'month', 'generated_by', 'generated_at')
        }),
        ('Statistiques', {
            'fields': (
                'total_interventions',
                'total_revenue',
                'success_rate',
                'customer_satisfaction_score',
                'avg_intervention_duration'
            )
        }),
        ('Analyse IA', {
            'fields': (
                'summary',
                'recommendations',
                'technical_analysis',
                'predictive_maintenance'
            ),
            'classes': ('collapse',)
        }),
        ('Données techniques', {
            'fields': ('statistics_data_display', 'ai_raw_response_display'),
            'classes': ('collapse',)
        }),
    )

    def month_display(self, obj):
        """Affiche le mois formaté"""
        return obj.month.strftime("%B %Y")

    month_display.short_description = "Période"
    month_display.admin_order_field = 'month'

    def total_revenue_display(self, obj):
        """Affiche le chiffre d'affaires formaté"""
        return f"{obj.total_revenue:,.0f} FCFA"

    total_revenue_display.short_description = "Chiffre d'affaires"

    def success_rate_display(self, obj):
        """Affiche le taux de réussite formaté"""
        return f"{obj.success_rate:.1f}%"

    success_rate_display.short_description = "Taux de réussite"

    def generated_by_display(self, obj):
        """Affiche l'utilisateur qui a généré le rapport"""
        return obj.generated_by.get_full_name() or obj.generated_by.username

    generated_by_display.short_description = "Généré par"

    def statistics_data_display(self, obj):
        """Affiche les données statistiques de manière lisible"""
        stats = obj.get_statistics()
        if not stats:
            return "Aucune donnée"

        # Formater les données
        from django.utils.html import format_html
        lines = []
        lines.append(f"<strong>Total interventions:</strong> {stats.get('total_interventions', 0)}")
        lines.append(f"<strong>Interventions terminées:</strong> {stats.get('completed_interventions', 0)}")
        lines.append(f"<strong>Interventions en cours:</strong> {stats.get('ongoing_interventions', 0)}")
        lines.append(f"<strong>Taux de réussite:</strong> {stats.get('success_rate', 0):.1f}%")
        lines.append(f"<strong>Score de satisfaction:</strong> {stats.get('satisfaction_score', 0):.1f}/10")
        lines.append(f"<strong>Durée moyenne:</strong> {stats.get('avg_duration', 'N/A')}")
        lines.append(f"<strong>Chiffre d'affaires:</strong> {stats.get('total_revenue', 0):,.0f} FCFA")

        return format_html("<br>".join(lines))

    statistics_data_display.short_description = "Données statistiques"

    def ai_raw_response_display(self, obj):
        """Affiche la réponse brute de l'IA"""
        from django.utils.html import format_html
        import json

        if not obj.ai_raw_response:
            return "Aucune réponse IA"

        try:
            if isinstance(obj.ai_raw_response, str):
                data = json.loads(obj.ai_raw_response)
            else:
                data = obj.ai_raw_response

            # Formater en HTML
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"<strong>{key}:</strong><br>")
                    for k, v in value.items():
                        lines.append(f"&nbsp;&nbsp;{k}: {v}<br>")
                else:
                    lines.append(f"<strong>{key}:</strong> {value}")

            return format_html("<br>".join(lines))
        except:
            return str(obj.ai_raw_response)

    ai_raw_response_display.short_description = "Réponse brute de l'IA"

    def get_readonly_fields(self, request, obj=None):
        """Détermine quels champs sont en lecture seule"""
        if obj:  # En édition
            return self.readonly_fields + ('title', 'month', 'generated_by', 'total_interventions',
                                           'total_revenue', 'success_rate', 'customer_satisfaction_score',
                                           'avg_intervention_duration', 'summary', 'recommendations',
                                           'technical_analysis', 'predictive_maintenance')
        return self.readonly_fields