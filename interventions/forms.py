from django import forms
from .models import Intervention
from clients.models import Client
from techniciens.models import Technicien


class InterventionAdminForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = [
            'client', 'technicien', 'date_intervention',
            'type_intervention', 'statut', 'panne_constatee',
            'pieces_remplacees', 'notes', 'prix_intervention'
        ]
        widgets = {
            'date_intervention': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'required': 'required'
                }
            ),
            'prix_intervention': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix en FCFA'
            }),
            'panne_constatee': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Décrire la panne constatée...'
            }),
            'pieces_remplacees': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Liste des pièces remplacées...'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Notes supplémentaires...'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_client_select'
            }),
            'technicien': forms.Select(attrs={'class': 'form-control'}),
            'type_intervention': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # NE PAS MASQUER LE CHAMP PRIX - Laisser visible
        # Seulement ajuster la validation
        if self.instance and self.instance.pk:
            # Pour une modification
            if self.instance.type_intervention == 'reparation':
                self.fields['prix_intervention'].required = True
                self.fields['prix_intervention'].help_text = "Prix à saisir manuellement pour les réparations"
            else:
                self.fields['prix_intervention'].widget.attrs['readonly'] = True
                self.fields['prix_intervention'].help_text = "Prix calculé automatiquement"
        else:
            # Pour une nouvelle intervention
            # Le champ sera géré par JavaScript
            self.fields['prix_intervention'].widget = forms.HiddenInput()


class InterventionTechnicienForm(forms.ModelForm):
    """Formulaire spécifique pour les techniciens - champs limités"""

    class Meta:
        model = Intervention
        fields = ['date_intervention', 'statut', 'panne_constatee', 'pieces_remplacees', 'notes']
        widgets = {
            'date_intervention': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'panne_constatee': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Décrire la panne constatée...'
            }),
            'pieces_remplacees': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Liste des pièces remplacées...'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Notes supplémentaires...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marquer les champs non modifiables comme lecture seule
        self.fields['client_info'] = forms.CharField(
            initial=self.instance.client.nom if self.instance.client else '',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            required=False,
            label="Client"
        )
        self.fields['technicien_info'] = forms.CharField(
            initial=self.instance.technicien.nom if self.instance.technicien else '',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            required=False,
            label="Technicien"
        )
        self.fields['type_info'] = forms.CharField(
            initial=self.instance.get_type_intervention_display(),
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            required=False,
            label="Type d'intervention"
        )
        self.fields['prix_info'] = forms.CharField(
            initial=f"{self.instance.prix_intervention:,} FCFA".replace(",", " "),
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            required=False,
            label="Prix"
        )