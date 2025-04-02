# Verificar se o container já existe
$containerName = "crime_detection_mongodb"
$containerExists = docker ps -a --filter "name=$containerName" --format "{{.Names}}"

if ($containerExists -eq $containerName) {
    Write-Host "Container $containerName já existe. Iniciando..."
    docker start $containerName
} else {
    Write-Host "Criando novo container $containerName..."
    docker run -d `
        --name $containerName `
        -p 27017:27017 `
        -e MONGO_INITDB_ROOT_USERNAME=admin `
        -e MONGO_INITDB_ROOT_PASSWORD=admin123 `
        mongo:latest
}

Write-Host "MongoDB iniciado em localhost:27017"
Write-Host "Usuário: admin"
Write-Host "Senha: admin123" 