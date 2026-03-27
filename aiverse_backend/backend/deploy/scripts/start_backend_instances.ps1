$ErrorActionPreference = "Stop"

Set-Location "D:\ML_Project\aiverse_backend\backend"

Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "manage.py runserver 127.0.0.1:8000"
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "manage.py runserver 127.0.0.1:8001"

Write-Host "Started backend instances on 127.0.0.1:8000 and 127.0.0.1:8001"
