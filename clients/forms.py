from django import forms
from .models import Client, Fournisseur


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'date_installation': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'materiels_fournis': forms.Textarea(attrs={'rows': 3}),  # NOUVEAU widget
            'type_installation': forms.TextInput(attrs={
                'placeholder': 'Ex: 5KVA 10KWH 10x550W (doit contenir KVA)',
                'class': 'kva-input form-control'
            }),
            'fournisseur': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnaliser les labels et help_text
        self.fields['type_installation'].label = "Type d'installation (KVA)"
        self.fields[
            'type_installation'].help_text = "Format obligatoire: doit contenir [nombre]KVA. Ex: '5KVA 10KWH 10x550W'"

        self.fields['email'].help_text = "L'email doit être unique. Vérifiez qu'il n'existe pas déjà."
        self.fields['telephone'].help_text = "Le téléphone doit être unique. Vérifiez qu'il n'existe pas déjà."

        # Ajouter des classes Bootstrap à tous les champs
        for field_name, field in self.fields.items():
            if field_name not in ['adresse', 'notes'] and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            elif field_name in ['adresse', 'notes']:
                field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        """Validation personnalisée pour l'email"""
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier si l'email existe déjà (sauf pour l'instance actuelle)
            queryset = Client.objects.filter(email=email)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError("Cet email est déjà utilisé par un autre client.")
        return email

    def clean_telephone(self):
        """Validation personnalisée pour le téléphone"""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Vérifier si le téléphone existe déjà (sauf pour l'instance actuelle)
            queryset = Client.objects.filter(telephone=telephone)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé par un autre client.")
        return telephone




class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = '__all__'
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes Bootstrap
        for field_name, field in self.fields.items():
            if field_name not in ['adresse']:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})


class ClientSearchForm(forms.Form):
    """Formulaire de recherche de clients"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par nom, email, téléphone, adresse...',
            'class': 'form-control'
        })
    )