import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solar_maintenance.settings')
django.setup()

from clients.models import Fournisseur

print("=== ÉTAT DES FOURNISSEURS ET LEURS CLIENTS ===")
print()

for fournisseur in Fournisseur.objects.all().prefetch_related('clients'):
    print(f"\nFournisseur: {fournisseur.nom} (ID: {fournisseur.id})")
    print(f"  Email: {fournisseur.email}")
    print(f"  Téléphone: {fournisseur.telephone}")
    print(f"  Nombre de clients: {fournisseur.clients.count()}")

    clients = fournisseur.clients.all()
    if clients.count() > 0:
        print("  Clients associés:")
        for client in clients:
            print(f"    - {client.nom} (Matériels: {client.materiels_fournis or 'VIDE'})")
    else:
        print("  Aucun client associé")