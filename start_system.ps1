# Script para iniciar todo o Sistema de Detecção de Crimes

# Iniciar o backend em uma nova janela
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\start_backend.ps1"

# Aguardar um pouco para o backend iniciar
Start-Sleep -Seconds 5

# Iniciar o frontend em uma nova janela
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\start_frontend.ps1" 