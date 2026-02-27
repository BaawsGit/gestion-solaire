from django import forms
from django.contrib.auth.models import User
from .models import Technicien
from django.core.exceptions import ValidationError


class TechnicienForm(forms.ModelForm):
    # Champs supplémentaires pour créer l'utilisateur Django
    username = forms.CharField(
        max_length=150,
        label="Identifiant de connexion",
        help_text="Nom d'utilisateur unique pour se connecter"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Mot de passe",
        required=False,
        help_text="Laissez vide pour ne pas changer le mot de passe (en modification)"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmer le mot de passe",
        required=False
    )

    class Meta:
        model = Technicien
        fields = ['nom', 'telephone', 'email', 'photo']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si c'est une modification, préremplir le username
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

        # Ajouter des classes Bootstrap
        for field_name, field in self.fields.items():
            if field_name != 'photo':
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()

        # Validation du mot de passe
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')

        # Vérifier si c'est une création
        if not self.instance.pk and not password:
            raise ValidationError({
                'password': 'Le mot de passe est obligatoire pour la création.'
            })

        # Vérifier la confirmation du mot de passe
        if password and password != confirm_password:
            raise ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas.'
            })

        # Vérifier l'unicité du username
        if username:
            user_query = User.objects.filter(username=username)
            if self.instance and self.instance.user:
                user_query = user_query.exclude(id=self.instance.user.id)

            if user_query.exists():
                raise ValidationError({
                    'username': 'Cet identifiant est déjà utilisé.'
                })

        # Vérifier l'unicité de l'email
        email = cleaned_data.get('email')
        if email:
            tech_query = Technicien.objects.filter(email=email)
            if self.instance:
                tech_query = tech_query.exclude(id=self.instance.id)

            if tech_query.exists():
                raise ValidationError({
                    'email': 'Cet email est déjà utilisé par un autre technicien.'
                })

        return cleaned_data

    def save(self, commit=True):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        email = self.cleaned_data['email']

        # Gestion de l'utilisateur Django
        if self.instance and self.instance.user:
            # Mise à jour de l'utilisateur existant
            user = self.instance.user
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
            user.save()
        else:
            # Création d'un nouvel utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=False  # Les techniciens ne sont pas staff
            )
            self.instance.user = user

        return super().save(commit)


class TechnicienSearchForm(forms.Form):
    """Formulaire de recherche de techniciens"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par nom, email, téléphone, identifiant...',
            'class': 'form-control'
        })
    )