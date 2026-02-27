from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from interventions.models import Intervention
from interventions.email_service import InterventionEmailService


class Command(BaseCommand):
    help = 'Envoie les rappels 24h avant les interventions'

    def handle(self, *args, **options):
        maintenant = timezone.now()

        self.stdout.write(f"=== COMMANDE RAPPEL ===")
        self.stdout.write(f"Heure d'exécution: {maintenant}")

        # RECHERCHE DES INTERVENTIONS DANS LES 25 PROCHAINES HEURES
        heure_limite = maintenant + timedelta(hours=25)

        self.stdout.write(f"Recherche interventions avant: {heure_limite}")

        interventions = Intervention.objects.filter(
            date_intervention__gte=maintenant,
            date_intervention__lte=heure_limite,
            statut='prevue',
            rappel_envoye=False
        ).select_related('client', 'technicien', 'fournisseur')

        for intervention in interventions:
            # Calculer l'heure exacte du rappel (24h avant)
            heure_rappel = intervention.date_intervention - timedelta(hours=24)

            # Vérifier si nous sommes dans la fenêtre du rappel (±30 min)
            marge = timedelta(minutes=30)
            if maintenant >= (heure_rappel - marge) and maintenant <= (heure_rappel + marge):
                try:
                    self.stdout.write(f"\n→ Intervention #{intervention.id} - Rappel 24h avant")
                    self.stdout.write(f"   Date intervention: {intervention.date_intervention}")
                    self.stdout.write(f"   Heure rappel idéale: {heure_rappel}")

                    InterventionEmailService.envoyer_rappel_24h(intervention)
                    self.stdout.write(self.style.SUCCESS('   ✓ RAPPEL ENVOYÉ'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ✗ Erreur: {str(e)}'))
            else:
                minutes_avant = (heure_rappel - maintenant).total_seconds() / 60
                if minutes_avant > 0:
                    self.stdout.write(f"\n→ Intervention #{intervention.id}")
                    self.stdout.write(f"   Rappel prévu dans: {int(minutes_avant)} minutes")

        self.stdout.write(f"\n=== FIN ===")