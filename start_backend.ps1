# Script para iniciar o backend do Sistema de Detecção de Crimes

# Ativar ambiente virtual se existir
if (Test-Path ".\venv") {
    .\venv\Scripts\Activate.ps1
}

# Iniciar o backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload 