#!/usr/bin/env bash
# Vercel build script — collects static files

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "2. Installing dependencies..."
pip install -r requirements.txt

echo "3. Collecting static files..."
python3 manage.py collectstatic --noinput

echo "4. Moving static files to Vercel's build directory..."
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/
