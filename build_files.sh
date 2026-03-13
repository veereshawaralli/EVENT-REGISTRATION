#!/usr/bin/env bash
# Vercel build script — collects static files
pip install -r requirements.txt
python manage.py collectstatic --noinput
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/
