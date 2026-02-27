from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from techniciens.models import Technicien


def login_view(request):
    """
    Vue pour la page de connexion - Authentification Django standard
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authentification Django standard
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Vérifier si c'est un technicien
            try:
                technicien = Technicien.objects.get(user=user)
                messages.success(request, f'Bienvenue Technicien {technicien.nom}!')
            except Technicien.DoesNotExist:
                messages.success(request, f'Bienvenue Administrateur {user.username}!')

            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')

    return render(request, 'authentication/login.html')


def logout_view(request):
    """
    Vue pour la déconnexion - Gère admin et technicien
    """
    if request.user.is_authenticated:
        # Déconnexion Django (admin)
        logout(request)
    elif request.session.get('is_technicien'):
        # Déconnexion technicien (session)
        request.session.flush()

    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')


def register_view(request):
    """
    Vue pour l'inscription (réservée aux administrateurs)
    """
    if not request.user.is_superuser:
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')

        # Validation
        if password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
        else:
            # Création de l'utilisateur
            user = User.objects.create_user(
                username=username,
                password=password1,
                email=email,
                is_staff=(user_type == 'admin')
            )

            # Si c'est un technicien, créer aussi le profil technicien
            if user_type == 'technicien':
                technicien = Technicien.objects.create(
                    user=user,
                    nom=username,
                    email=email,
                    telephone='À définir'
                )
                messages.success(request, f'Technicien {username} créé avec succès!')
            else:
                messages.success(request, f'Administrateur {username} créé avec succès!')

            return redirect('register')

    return render(request, 'authentication/register.html')