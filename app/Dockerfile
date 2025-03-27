# Utiliser une image Python légère
FROM python:3.10-slim

# Installer Tesseract OCR, libGL et autres dépendances système
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    imagemagick \
    zbar-tools \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers
COPY . .

# Exposer le port utilisé par FastAPI
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["python", "app/run_prod.py"]
