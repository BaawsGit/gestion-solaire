import re


def extraire_kva(type_installation):
    """
    Extrait le nombre de KVA d'une chaîne de type d'installation.
    Retourne None si aucun KVA valide n'est trouvé.
    """
    if not type_installation:
        return None

    # Recherche d'un nombre suivi de "KVA" (insensible à la casse et aux espaces)
    match = re.search(r'(\d+)\s*KVA', type_installation, re.IGNORECASE)

    if match:
        try:
            kva = int(match.group(1))
            return kva
        except ValueError:
            return None

    return None


def valider_kva(type_installation):
    """
    Valide que le type d'installation contient un KVA.
    Retourne (est_valide, message_erreur)
    """
    if not type_installation:
        return False, "Le type d'installation est vide."

    kva = extraire_kva(type_installation)

    if kva is None:
        return False, "Aucun KVA valide trouvé. Format attendu: [nombre]KVA"

    if kva < 1:
        return False, "Le KVA doit être supérieur à 0."

    if kva > 100:
        return False, "Le KVA doit être inférieur ou égal à 100."

    return True, f"KVA valide détecté: {kva}KVA"


def calculer_prix_par_kva_et_type(kva, type_intervention):
    """
    Calcule le prix d'intervention en fonction du KVA et du type d'intervention.
    Tarifs:
        Entretien:
            3KVA -> 15000
            5KVA -> 20000
            8KVA -> 30000
            16KVA -> 35000
            24KVA -> 45000

        Installation:
            3KVA -> 50000
            5KVA -> 75000
            8KVA -> 80000
            16KVA -> 125000
            24KVA -> 200000

        Réparation: Prix manuel (retourne 0)
    """
    if not kva or kva < 1:
        return 0

    # Tarifs selon le type d'intervention
    if type_intervention == 'entretien':
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

    elif type_intervention == 'installation':
        if kva <= 3:
            return 50000
        elif kva <= 5:
            return 75000
        elif kva <= 8:
            return 80000
        elif kva <= 16:
            return 125000
        else:
            return 200000

    # Pour 'reparation', retourner 0 (prix à saisir manuellement)
    return 0