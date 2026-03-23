#!/usr/bin/env bash
# Render build script — runs on every deploy
set -o errexit   # exit on error

echo "Updating pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate

echo "Setting up superuser..."
python manage.py setup_superuser

echo "Build complete!"
