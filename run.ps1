# Auto-generated script to start the Django development server correctly

Write-Host "Updating and checking virtual environment packages..." -ForegroundColor Yellow
.\venv\Scripts\pip.exe install -r requirements.txt | Out-Null

Write-Host "Starting Django server..." -ForegroundColor Green
.\venv\Scripts\python.exe manage.py runserver
