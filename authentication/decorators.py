from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def login_required_custom(view_func):
    """
    Décorateur personnalisé qui vérifie soit Django auth, soit session technicien
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier si c'est un admin Django
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # Vérifier si c'est un technicien (session)
        elif request.session.get('is_technicien'):
            # Ajouter le technicien à la requête pour y accéder dans les vues
            from techniciens.models import Technicien
            try:
                technicien_id = request.session.get('technicien_id')
                if technicien_id:
                    request.technicien = Technicien.objects.get(id=technicien_id)
            except:
                pass
            return view_func(request, *args, **kwargs)

        # Non connecté
        else:
            messages.error(request, 'Veuillez vous connecter pour accéder à cette page.')
            return redirect('login')

    return _wrapped_view


def admin_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur est un administrateur
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Veuillez vous connecter pour accéder à cette page.')
            return redirect('login')

        if not request.user.is_superuser:
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def technicien_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur est un technicien
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier la session technicien
        if not request.session.get('is_technicien'):
            messages.error(request, 'Accès réservé aux techniciens.')
            return redirect('dashboard')

        # Récupérer le technicien depuis la session
        from techniciens.models import Technicien
        try:
            technicien_id = request.session.get('technicien_id')
            if technicien_id:
                request.technicien = Technicien.objects.get(id=technicien_id)
        except Technicien.DoesNotExist:
            messages.error(request, 'Technicien non trouvé.')
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return _wrapped_view