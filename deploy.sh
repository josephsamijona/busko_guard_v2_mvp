#!/bin/sh
set -e # Quitte immédiatement si une commande échoue

# Exécuter les migrations (alternativement, utiliser la phase de release de Railway)
# python manage.py migrate --noinput

# Collecter les fichiers statiques (déjà fait dans le Dockerfile, mais pourrait être ici si la logique de build change)
# python manage.py collectstatic --noinput --clear

# Démarrer Gunicorn
# La variable PORT est fournie par l'environnement d'hébergement (Railway)
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3}