from django.db import models
from django.core.exceptions import ValidationError
import re


class Fournisseur(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)  # Nouveau
    date_modification = models.DateTimeField(auto_now=True)  # Nouveau

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['nom']


class Client(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    date_installation = models.DateField()

    type_installation = models.CharField(
        max_length=100,
        help_text="Format obligatoire: [nombre]KVA. Ex: 5KVA 10KWH 10x550W, 3KVA, 8KVA système hybride, etc."
    )

    notes = models.TextField(blank=True, null=True)
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
    )

    # NOUVEAU CHAMP - Ajoutez-le après 'fournisseur' :
    materiels_fournis = models.TextField(
        blank=True,
        null=True,
        help_text="Matériels spécifiques fournis par le fournisseur à ce client"
    )

    def clean(self):
        """
        Validation personnalisée pour s'assurer que le type d'installation contient un KVA.
        Cette méthode est appelée automatiquement par Django dans les formulaires et l'admin.
        """
        super().clean()

        if not self.type_installation:
            raise ValidationError({
                'type_installation': 'Le type d\'installation est obligatoire.'
            })

        # Vérification de la présence du KVA
        if not self.contient_kva_valide():
            raise ValidationError({
                'type_installation': (
                    'Le type d\'installation doit contenir un nombre de KVA. '
                    'Format attendu: [nombre]KVA. '
                    'Exemples valides: "5KVA", "3 KVA", "8KVA système", "16KVA 20KWH"'
                )
            })

        # Vérification que le KVA est dans une plage raisonnable
        kva = self.extraire_kva()
        if kva:
            if kva < 1:
                raise ValidationError({
                    'type_installation': 'Le KVA doit être supérieur à 0.'
                })
            if kva > 100:
                raise ValidationError({
                    'type_installation': 'Le KVA doit être inférieur ou égal à 100.'
                })

    def contient_kva_valide(self):
        """Vérifie si le type d'installation contient un KVA valide."""
        return self.extraire_kva() is not None

    def extraire_kva(self):
        """
        Extrait le nombre de KVA du type d'installation.
        Retourne None si aucun KVA valide n'est trouvé.
        """
        if not self.type_installation:
            return None

        # Recherche d'un nombre suivi de "KVA" (insensible à la casse et aux espaces)
        match = re.search(r'(\d+)\s*KVA', self.type_installation, re.IGNORECASE)

        if match:
            try:
                kva = int(match.group(1))
                return kva
            except ValueError:
                return None

        return None

    def get_kva(self):
        """Retourne le KVA extrait (méthode publique pour les templates)."""
        return self.extraire_kva()

    def get_prix_intervention(self):
        """
        Retourne le prix d'intervention basé sur le KVA.
        Utile pour prévisualiser le prix sans créer d'intervention.
        """
        kva = self.extraire_kva()
        if not kva:
            return 0

        # Tarifs selon les spécifications
        if kva <= 3:
            return 15000
        elif kva <= 5:
            return 20000
        elif kva <= 8:
            return 30000
        elif kva <= 16:
            return 35000
        else:
            return 45000

    def __str__(self):
        kva = self.extraire_kva()
        if kva:
            return f"{self.nom} ({kva}KVA)"
        return f"{self.nom} ({self.type_installation})"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        # Ajout de contraintes supplémentaires si besoin
        constraints = [
            models.UniqueConstraint(
                fields=['telephone', 'email'],
                name='unique_telephone_email'
            )
        ]