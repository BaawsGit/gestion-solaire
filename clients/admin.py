from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import Fournisseur, Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'date_installation': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout d'un placeholder et d'un style pour guider l'utilisateur
        self.fields['type_installation'].widget.attrs.update({
            'placeholder': 'Ex: 5KVA 10KWH 10x550W (OBLIGATOIRE: doit contenir [nombre]KVA)',
            'style': 'width: 80%; padding: 8px;',
            'class': 'kva-input'
        })

        # Si c'est une modification, afficher le KVA détecté
        if self.instance and self.instance.pk:
            kva = self.instance.extraire_kva()
            if kva:
                prix = self.instance.get_prix_intervention()
                # Formater le prix en chaîne avec séparateurs de milliers
                prix_formatted = f"{prix:,}".replace(",", " ")
                self.fields[
                    'type_installation'].help_text += f'<br><span style="color: green;">✓ KVA détecté: {kva}KVA → Prix intervention: {prix_formatted} FCFA</span>'


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'telephone', 'email')
    search_fields = ('nom', 'email', 'telephone')
    list_filter = ('nom',)


class ClientAdmin(admin.ModelAdmin):
    form = ClientForm
    list_display = ('id', 'nom', 'telephone', 'email', 'get_kva_display', 'get_prix_preview', 'fournisseur')
    list_filter = ('fournisseur',)
    search_fields = ('nom', 'email', 'telephone', 'adresse')
    date_hierarchy = 'date_installation'

    # Ajout de colonnes calculées dans la liste
    def get_kva_display(self, obj):
        kva = obj.extraire_kva()
        if kva:
            return format_html('<span style="color: green; font-weight: bold;">{} KVA</span>', kva)
        return format_html('<span style="color: red;">⚠ Aucun KVA</span>')

    get_kva_display.short_description = 'KVA'

    def get_prix_preview(self, obj):
        prix = obj.get_prix_intervention()
        # Formater le prix en chaîne de caractères AVANT de l'utiliser dans format_html
        prix_formatted = f"{prix:,}".replace(",", " ")
        return format_html('<span style="color: blue; font-weight: bold;">{} FCFA</span>', prix_formatted)

    get_prix_preview.short_description = 'Prix intervention'

    # Ajout d'actions personnalisées
    actions = ['valider_kva_clients']

    def valider_kva_clients(self, request, queryset):
        """Action admin pour vérifier le KVA des clients sélectionnés."""
        clients_ok = []
        clients_erreur = []

        for client in queryset:
            if client.contient_kva_valide():
                clients_ok.append(client)
            else:
                clients_erreur.append(client)

        self.message_user(
            request,
            f'{len(clients_ok)} clients avec KVA valide, {len(clients_erreur)} clients sans KVA valide.'
        )

        if clients_erreur:
            erreurs = ", ".join([f"{c.nom} ({c.type_installation})" for c in clients_erreur])
            self.message_user(
                request,
                f'Clients sans KVA valide: {erreurs}',
                level='ERROR'
            )

    valider_kva_clients.short_description = "Valider le KVA des clients sélectionnés"

    # Inclure le fichier JavaScript
    class Media:
        js = ('js/kva-validation.js',)


# Enregistrement des modèles (Fournisseur est déjà enregistré avec @admin.register)
admin.site.register(Client, ClientAdmin)