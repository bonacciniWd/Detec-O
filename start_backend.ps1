# Script para iniciar o backend
Write-Host "Iniciando API Detec-O..."

# Ativar o ambiente virtual (opcional)
# .\venv\Scripts\Activate

# Executar o FastAPI com uvicorn
uvicorn api.main:app --reload --port 8000

Write-Host "Servidor encerrado." 