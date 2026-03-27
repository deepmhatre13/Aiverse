$ErrorActionPreference = "Stop"

Set-Location "D:\ML_Project\aiverse_backend\backend"

Start-Process -FilePath ".\venv\Scripts\celery.exe" -ArgumentList "-A backend worker --loglevel=info --pool=solo -Q default"
Start-Process -FilePath ".\venv\Scripts\celery.exe" -ArgumentList "-A backend worker --loglevel=info --pool=solo -Q ml_train"

Write-Host "Started Celery workers for queues: default, ml_train"
