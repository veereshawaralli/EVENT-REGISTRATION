#!/usr/bin/env bash
# Vercel build script — collects static files

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/install/bin/activate 2>/dev/null || source venv/bin/activate

echo "2. Installing dependencies..."
pip install -r requirements.txt

echo "3. Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "4. Build complete! Static files are in 'staticfiles' directory."
