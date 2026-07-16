# Infra MVP

Infra mínima do NexoVital AI MVP.

Recursos criados:
- Azure Static Web Apps Free
- Azure Container Apps Consumption com backend único (`minReplicas: 0`, `maxReplicas: 1`)
- Azure Speech F0
- Azure AI Language F0
- Budget mensal de US$ 5

Sem Cosmos DB. Sem Storage Account. Sem fila. Sem worker. Sem Key Vault. Sem VNet. Sem Application Insights. Sem Entra ID.

## Pré-requisitos

- Azure CLI com Bicep
- Docker
- imagem pública do backend no GHCR

## 1. Publicar imagem do backend no GHCR

```bash
docker build -t ghcr.io/<github-user>/nexovital-backend:<tag> ./backend
docker login ghcr.io
docker push ghcr.io/<github-user>/nexovital-backend:<tag>
```

Se pacote GHCR estiver privado, Container Apps não conseguirá puxar imagem neste template mínimo.

## 2. Ajustar parâmetros

Edite `infra/parameters/demo.bicepparam`:

```bicep
using '../main.bicep'

param location = 'eastus2'
param githubUsername = 'your-github-username'
param repoUrl = 'https://github.com/your-github-username/fiap-04-final'
param backendImageTag = 'latest'
param notificationEmail = 'admin@example.com'
```

## 3. Criar resource group

```bash
az group create --name rg-nexovital-demo --location eastus2
```

## 4. Deploy da infraestrutura

```bash
az deployment group create \
  --resource-group rg-nexovital-demo \
  --template-file infra/main.bicep \
  --parameters infra/parameters/demo.bicepparam
```

## 5. Validar template localmente

```bash
az bicep build --file infra/main.bicep
az bicep build-params --file infra/parameters/demo.bicepparam
```

## 6. Publicar frontend no Static Web App

Template cria recurso do Static Web App. Deploy do frontend continua simples:
- conecte repositório `repoUrl` no portal Azure Static Web Apps; ou
- use workflow GitHub padrão do Static Web Apps apontando para `frontend/` com output `dist`

Build do frontend:

```bash
cd frontend
npm install
npm run build
```

## Outputs úteis

Deploy retorna:
- `frontendUrl`
- `backendUrl`
- `backendImage`
- `languageEndpoint`

## Remover tudo

```bash
az group delete --name rg-nexovital-demo --yes --no-wait
```
