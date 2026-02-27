from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class InterventionEmailService:

    @staticmethod
    def get_base_context(intervention, request=None):
        """Retourne le contexte de base pour tous les emails"""
        # Utiliser l'importation locale pour éviter les problèmes de circular import
        try:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            domain = site.domain
        except:
            # Fallback si le site n'est pas configuré
            domain = 'localhost:8000'

        # Déterminer le protocole
        if request and request.is_secure():
            protocol = 'https://'
        else:
            protocol = 'http://'

        return {
            'intervention': intervention,
            'domain': domain,
            'protocol': protocol,
            'support_email': 'support@solar-maintenance.com',
            'support_phone': '+221 77 123 45 67',
            'admin_email': 'admin@solar-maintenance.com',
        }

    @staticmethod
    def envoyer_notification_creation(intervention, request=None):
        """Envoyer un email lors de la création d'une intervention"""
        if not intervention.technicien or not intervention.technicien.email:
            return

        context = InterventionEmailService.get_base_context(intervention, request)

        # Email au technicien
        sujet_tech = f"[Solar Maintenance] Nouvelle intervention programmée - #{intervention.id}"
        message_tech = render_to_string('interventions/emails/nouvelle_intervention_tech.html', context)

        # Email au client
        if intervention.client and intervention.client.email:
            sujet_client = f"[Solar Maintenance] Votre intervention #{intervention.id} est programmée"
            message_client = render_to_string('interventions/emails/nouvelle_intervention_client.html', context)

            send_mail(
                sujet_client,
                strip_tags(message_client),
                settings.DEFAULT_FROM_EMAIL,
                [intervention.client.email],
                html_message=message_client,
                fail_silently=True
            )

        send_mail(
            sujet_tech,
            strip_tags(message_tech),
            settings.DEFAULT_FROM_EMAIL,
            [intervention.technicien.email],
            html_message=message_tech,
            fail_silently=True
        )

    @staticmethod
    def envoyer_notification_statut(intervention, ancien_statut, request=None):
        """Envoyer un email lors du changement de statut"""
        if intervention.statut != ancien_statut and intervention.client and intervention.client.email:
            context = InterventionEmailService.get_base_context(intervention, request)
            context['ancien_statut'] = ancien_statut

            # Obtenir le display name de l'ancien statut
            statut_dict = dict(intervention.STATUT_CHOICES)
            context['ancien_statut_display'] = statut_dict.get(ancien_statut, ancien_statut)

            sujet = f"[Solar Maintenance] Mise à jour intervention #{intervention.id} - {intervention.get_statut_display()}"
            message = render_to_string('interventions/emails/changement_statut.html', context)

            send_mail(
                sujet,
                strip_tags(message),
                settings.DEFAULT_FROM_EMAIL,
                [intervention.client.email],
                html_message=message,
                fail_silently=True
            )

            # Si l'intervention est terminée, envoyer aussi au technicien
            if intervention.statut == 'terminee' and intervention.technicien and intervention.technicien.email:
                sujet_tech = f"[Solar Maintenance] Intervention #{intervention.id} terminée"
                message_tech = render_to_string('interventions/emails/intervention_terminee_tech.html', context)

                send_mail(
                    sujet_tech,
                    strip_tags(message_tech),
                    settings.DEFAULT_FROM_EMAIL,
                    [intervention.technicien.email],
                    html_message=message_tech,
                    fail_silently=True
                )

    @staticmethod
    def envoyer_rappel_24h(intervention, request=None):
        """Envoyer un rappel 24h avant l'intervention"""
        context = InterventionEmailService.get_base_context(intervention, request)

        sujet = f"[Solar Maintenance] Rappel - Intervention #{intervention.id} demain"
        message = render_to_string('interventions/emails/rappel_24h.html', context)

        destinataires = []
        if intervention.technicien and intervention.technicien.email:
            destinataires.append(intervention.technicien.email)
        if intervention.client and intervention.client.email:
            destinataires.append(intervention.client.email)

        if destinataires:
            send_mail(
                sujet,
                strip_tags(message),
                settings.DEFAULT_FROM_EMAIL,
                destinataires,
                html_message=message,
                fail_silently=True
            )
            intervention.rappel_envoye = True
            intervention.save(update_fields=['rappel_envoye'])