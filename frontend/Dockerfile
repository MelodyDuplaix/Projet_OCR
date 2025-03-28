# Utiliser une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /frontend

# Copier les fichiers nécessaires
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers
COPY . .

# Exposer le port utilisé par Flask
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "run_prod.py"]