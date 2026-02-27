"""
Script pour corriger les utilisateurs et techniciens existants
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solar_maintenance.settings')
django.setup()

from django.contrib.auth.models import User
from techniciens.models import Technicien


def corriger_utilisateurs():
    print("=== CORRECTION DES UTILISATEURS ===")

    # 1. Vérifier les techniciens existants
    techniciens = Technicien.objects.all()
    print(f"Nombre de techniciens dans la base: {techniciens.count()}")

    for tech in techniciens:
        print(f"Technicien: {tech.nom}, User: {tech.user}")

    print("\n=== UTILISATEURS EXISTANTS ===")
    for user in User.objects.all():
        print(f"User: {user.username}, Superuser: {user.is_superuser}, Staff: {user.is_staff}")
        try:
            tech = Technicien.objects.get(user=user)
            print(f"  → Technicien associé: {tech.nom}")
        except Technicien.DoesNotExist:
            print("  → Pas de technicien associé")

    # 2. Créer un admin sans technicien
    print("\n=== CRÉATION D'UN ADMIN PROPRE ===")
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@solar.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        admin.set_password('Admin123!')
        admin.save()
        print(f"✅ Admin créé: admin / Admin123!")
    else:
        # S'assurer que cet admin n'a pas de technicien
        Technicien.objects.filter(user=admin).delete()
        print(f"✅ Admin existant nettoyé: admin")

    # 3. S'assurer que les techniciens ont des mots de passe
    print("\n=== VÉRIFICATION DES TECHNICIENS ===")
    techniciens_users = {
        'technicien1': ('Pierre Martin', 'Tech123!'),
        'technicien2': ('Jean Dupont', 'Tech456!'),
    }

    for username, (nom, password) in techniciens_users.items():
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@solar.com'}
        )

        if created:
            user.set_password(password)
            user.save()
            print(f"✅ Utilisateur créé: {username} / {password}")

        # Créer ou mettre à jour le technicien
        tech, created = Technicien.objects.get_or_create(
            user=user,
            defaults={
                'nom': nom,
                'telephone': '+225 01 23 45 67 89',
                'email': f'{username}@solar.com'
            }
        )

        if not created:
            tech.nom = nom
            tech.save()

        print(f"✅ Technicien associé: {nom} → {username}")


if __name__ == '__main__':
    corriger_utilisateurs()