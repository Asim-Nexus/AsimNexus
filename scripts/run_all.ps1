Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      AsimNexus Ultimate Launcher       " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting API Backend (Core)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd $PWD; python -m uvicorn app:app --host 127.0.0.1 --port 8000`""

Write-Host "Starting RAG & CEE Cosmos Engine..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd $PWD; python main.py`""

Write-Host "Starting React Web UI (Frontend)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd $PWD\frontend; npm start`""

Write-Host ""
Write-Host "All systems are starting up in separate windows!" -ForegroundColor Green
Write-Host "AsimNexus is now fully interconnected." -ForegroundColor Cyan
