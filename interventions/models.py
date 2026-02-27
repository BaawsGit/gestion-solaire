from django.db import models
from clients.models import Client, Fournisseur
from techniciens.models import Technicien
from django.utils import timezone
from datetime import timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extraire_kva, calculer_prix_par_kva_et_type


class Intervention(models.Model):
    TYPE_INTERVENTION_CHOICES = [
        ('installation', 'Installation'),
        ('reparation', 'Réparation'),
        ('entretien', 'Entretien'),
    ]

    STATUT_CHOICES = [
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('en_cours', 'En cours'),
        ('prevue', 'Prévue'),
    ]

    date_intervention = models.DateTimeField()
    type_intervention = models.CharField(
        max_length=20,
        choices=TYPE_INTERVENTION_CHOICES
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_cours'
    )
    panne_constatee = models.TextField(blank=True, null=True)
    pieces_remplacees = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    prix_intervention = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0
    )

    # NOUVEAUX CHAMPS POUR LE SUIVI DU TEMPS
    duree_cumulee = models.DurationField(
        default=timedelta,
        help_text="Durée totale cumulée en statut 'En cours'"
    )
    dernier_debut_en_cours = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Dernière fois que le statut est passé à 'En cours'"
    )
    temps_en_cours = models.BooleanField(
        default=False,
        help_text="Si l'intervention est actuellement en cours de comptage"
    )
    historique_statuts = models.JSONField(
        default=list,
        blank=True,
        help_text="Historique des changements de statut avec timestamps"
    )

    # Relations avec autres tables
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='interventions'
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interventions',
        editable=False
    )
    technicien = models.ForeignKey(
        Technicien,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interventions'
    )

    rappel_envoye = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Récupérer l'ancien statut si l'objet existe
        ancien_statut = None
        if self.pk:
            ancien_instance = Intervention.objects.filter(pk=self.pk).first()
            if ancien_instance:
                ancien_statut = ancien_instance.statut

        # Gestion du temps selon les changements de statut
        self._gerer_temps_statut(ancien_statut)

        # Règle 1 : Le fournisseur est toujours celui du client
        if self.client and self.client.fournisseur:
            self.fournisseur = self.client.fournisseur

        # Règle 2 : Calcul automatique du prix basé sur l'extraction du KVA et du type d'intervention
        if self.client and not self.prix_intervention:
            type_install = self.client.type_installation
            kva = extraire_kva(type_install)

            if kva:
                # Utiliser la nouvelle fonction qui prend en compte le type d'intervention
                self.prix_intervention = calculer_prix_par_kva_et_type(kva, self.type_intervention)
            else:
                self.prix_intervention = 0

        super().save(*args, **kwargs)

    def _gerer_temps_statut(self, ancien_statut):
        """Gère le comptage du temps selon les changements de statut"""
        now = timezone.now()

        # Initialiser l'historique si vide
        if not self.historique_statuts:
            self.historique_statuts = []

        # Cas 1: Passage à "En cours" depuis autre statut
        if self.statut == 'en_cours' and ancien_statut != 'en_cours':
            self.dernier_debut_en_cours = now
            self.temps_en_cours = True
            self.historique_statuts.append({
                'statut': 'en_cours',
                'timestamp': now.isoformat(),
                'action': 'debut'
            })

        # Cas 2: Sortie de "En cours" vers autre statut
        elif ancien_statut == 'en_cours' and self.statut != 'en_cours':
            if self.dernier_debut_en_cours:
                duree_ecoulee = now - self.dernier_debut_en_cours
                self.duree_cumulee += duree_ecoulee
                self.dernier_debut_en_cours = None
                self.temps_en_cours = False
                self.historique_statuts.append({
                    'statut': ancien_statut,
                    'timestamp': now.isoformat(),
                    'action': 'fin',
                    'duree_ecoulee': str(duree_ecoulee)
                })

        # Cas 3: Passage de "Terminée" à "En cours" (reprise)
        elif self.statut == 'en_cours' and ancien_statut == 'terminee':
            # Le temps cumulé est conservé, on reprend le comptage
            self.dernier_debut_en_cours = now
            self.temps_en_cours = True
            self.historique_statuts.append({
                'statut': 'en_cours',
                'timestamp': now.isoformat(),
                'action': 'reprise',
                'note': 'Reprise après statut Terminée'
            })

        # Cas 4: Passage de "Prévue" à "En cours" (reprise après pause)
        elif self.statut == 'en_cours' and ancien_statut == 'prevue':
            # Le temps cumulé est conservé, on reprend le comptage
            self.dernier_debut_en_cours = now
            self.temps_en_cours = True
            self.historique_statuts.append({
                'statut': 'en_cours',
                'timestamp': now.isoformat(),
                'action': 'reprise',
                'note': 'Reprise après statut Prévue'
            })

        # Cas 5: Passage de "Annulée" à "En cours" (reprise)
        elif self.statut == 'en_cours' and ancien_statut == 'annulee':
            # Le temps cumulé est conservé, on reprend le comptage
            self.dernier_debut_en_cours = now
            self.temps_en_cours = True
            self.historique_statuts.append({
                'statut': 'en_cours',
                'timestamp': now.isoformat(),
                'action': 'reprise',
                'note': 'Reprise après statut Annulée'
            })

    def get_duree_totale(self):
        """Retourne la durée totale en cours (cumulée + temps actuel si en cours)"""
        duree_totale = self.duree_cumulee

        if self.temps_en_cours and self.dernier_debut_en_cours:
            duree_actuelle = timezone.now() - self.dernier_debut_en_cours
            duree_totale += duree_actuelle

        return duree_totale

    def get_duree_formatee(self):
        """Retourne la durée formatée en jours, heures, minutes"""
        duree = self.get_duree_totale()

        if not duree:
            return "0 min"

        total_seconds = int(duree.total_seconds())

        # Calcul des composants
        jours = total_seconds // 86400
        heures = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        secondes = total_seconds % 60

        # Construction du texte
        parts = []
        if jours > 0:
            parts.append(f"{jours}j")
        if heures > 0:
            parts.append(f"{heures}h")
        if minutes > 0:
            parts.append(f"{minutes}min")
        if secondes > 0 and not (jours or heures or minutes):
            parts.append(f"{secondes}s")

        return " ".join(parts) if parts else "0 min"

    def __str__(self):
        return f"Intervention {self.id} - {self.client.nom}"

    class Meta:
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"
        ordering = ['-date_intervention']