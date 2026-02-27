from django.contrib import admin
from .models import Intervention


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'technicien', 'type_intervention', 'statut', 'date_intervention',
                    'prix_intervention', 'get_client_kva')
    list_filter = ('type_intervention', 'statut', 'date_intervention')
    search_fields = ('client__nom', 'technicien__nom')
    date_hierarchy = 'date_intervention'

    fields = [
        'client',
        'date_intervention',
        'type_intervention',
        'statut',
        'panne_constatee',
        'pieces_remplacees',
        'notes',
        'technicien',
        'prix_intervention'
    ]

    readonly_fields = ('prix_intervention',)

    def get_client_kva(self, obj):
        """Affiche le KVA du client dans la liste des interventions."""
        if obj.client:
            kva = obj.client.extraire_kva()
            if kva:
                return f"{kva}KVA"
        return "N/A"

    get_client_kva.short_description = "KVA Client"

    def save_model(self, request, obj, form, change):
        # Validation: le client doit avoir un KVA valide
        if obj.client and not obj.client.contient_kva_valide():
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f"Le client '{obj.client.nom}' n'a pas de KVA valide dans son type d'installation: '{obj.client.type_installation}'. "
                "Veuillez corriger le type d'installation du client avant de créer une intervention."
            )

        # Règle 1 : Le fournisseur est toujours celui du client
        if obj.client and obj.client.fournisseur:
            obj.fournisseur = obj.client.fournisseur

        # Règle 2 : Calcul automatique du prix basé sur le KVA du client et le type d'intervention
        if obj.client and not obj.prix_intervention:
            kva = obj.client.extraire_kva()
            if kva:
                # Utiliser la nouvelle fonction de calcul
                from utils import calculer_prix_par_kva_et_type
                obj.prix_intervention = calculer_prix_par_kva_et_type(kva, obj.type_intervention)
            else:
                # Ce cas ne devrait pas arriver grâce à la validation
                obj.prix_intervention = 0

        super().save_model(request, obj, form, change)