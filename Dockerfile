# 1. On part d'une image de base : Python version 3.11
FROM python:3.11-slim

# 2. On définit le dossier de travail à l'intérieur de la "boîte"
WORKDIR /app

# 3. On installe des outils système nécessaires pour tes photos et PDF
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. On copie ta "liste de courses" dans la boîte
COPY requirements.txt /app/

# 5. On demande à Docker d'installer tout ce qui est écrit sur la liste
RUN pip install --no-cache-dir -r requirements.txt

# 6. On copie tout le reste de ton projet (tes dossiers 'clients', 'interventions', etc.)
COPY . /app/

# 7. On dit que l'app utilisera le port 8000
EXPOSE 8000

# 8. La commande pour démarrer ton serveur Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]