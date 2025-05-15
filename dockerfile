# --- Stage 1: Builder ---
# Utiliser python:3.11-slim-bullseye comme base pour le build
FROM python:3.11-slim-bullseye AS builder

# Définir les variables d'environnement pour Python et l'installation non interactive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Mettre à jour et installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essentiels pour la compilation
    build-essential \
    pkg-config \
    gcc \
    python3-dev \
    # Pour mysqlclient
    default-libmysqlclient-dev \
    default-mysql-client \
    # Pour Pillow
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    # Pour WeasyPrint et autres manipulations PDF/images (incluant vos dépendances)
    poppler-utils \
    libpoppler-cpp-dev \
    # Dépendances pour WeasyPrint (Pango, Cairo, etc.)
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \ # Note: sur Bullseye, c'est libgdk-pixbuf2.0-dev ou libgdk-pixbuf-2.0-0
    libcairo2 \
    libharfbuzz0b \
    libfontconfig1 \
    # Pour Tesseract (si utilisé, car listé dans votre ancien Dockerfile)
    tesseract-ocr \
    libtesseract-dev \
    # Utilitaires
    netcat-traditional \ # Utile dans entrypoint.sh pour attendre la DB
    curl \
    # Nettoyage des caches apt pour réduire la taille de l'image
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt .

# Configuration pour mysqlclient (peut aider si pip a du mal à trouver les headers)
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lmysqlclient"

# Mettre à jour pip et installer wheel, puis les dépendances Python
RUN pip install --no-cache-dir -U pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'application
COPY . .

# Collecter les fichiers statiques
# Il est crucial que DEBUG soit à False pour collectstatic en production.
# Railway injectera les variables d'environnement, y compris SECRET_KEY et DEBUG.
# Pour le build, on peut utiliser des valeurs factices si nécessaire.
RUN DJANGO_SETTINGS_MODULE=config.settings SECRET_KEY="dummy-build-key" DEBUG=0 python manage.py collectstatic --noinput --clear


# --- Stage 2: Runner ---
# Utiliser une image slim pour la production
FROM python:3.11-slim-bullseye AS runner

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE config.settings # Spécifie le module de settings pour Django
ENV HOME=/home/appuser 

WORKDIR /app

# Créer un utilisateur et un groupe non-root pour l'application
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup -d $HOME -s /sbin/nologin -c "Docker image user" appuser

# Copier les dépendances Python installées et l'application depuis le stage builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# S'assurer que le répertoire staticfiles est copié (si STATIC_ROOT est /app/staticfiles)
# COPY --from=builder /app/staticfiles /app/staticfiles # Normalement inclus avec COPY --from=builder /app /app

# Donner la propriété du répertoire de l'application à l'utilisateur non-root
RUN chown -R appuser:appgroup /app $HOME

# Changer pour l'utilisateur non-root
USER appuser

# Copier le script d'entrée et le rendre exécutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exposer le port (Railway le mappera)
EXPOSE 8000

# Définir le script d'entrée comme point d'entrée
ENTRYPOINT ["/entrypoint.sh"]