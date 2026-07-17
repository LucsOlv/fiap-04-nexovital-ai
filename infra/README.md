# Infra MVP

Infraestrutura mínima do NexoVital AI.

Recursos:

- Azure Static Web Apps Free;
- Azure Container Apps Consumption com backend único (`minReplicas: 0`, `maxReplicas: 1`);
- Azure Speech F0;
- Azure AI Language F0;
- budget mensal de US$ 5;
- imagem pública do backend no GitHub Container Registry (GHCR).

Sem Cosmos DB, Storage Account, fila, worker, Key Vault, VNet, Application Insights dedicado ou Entra ID.

## Pré-requisitos

- Azure CLI com Bicep;
- Docker;
- imagem pública `ghcr.io/lucsolv/fiap-04-nexovital-ai/backend:latest`;
- variável `OPENROUTER_API_KEY` definida no ambiente;
- resource group `rg-nexovital-demo`.

## 1. Publicar imagem do backend no GHCR

Workflow `.github/workflows/containers.yml` publica imagem em push para `main`. Publicação manual equivalente:

```bash
docker build -t ghcr.io/lucsolv/fiap-04-nexovital-ai/backend:latest ./backend
docker login ghcr.io
docker push ghcr.io/lucsolv/fiap-04-nexovital-ai/backend:latest
```

Pacote GHCR deve ser público. Template não configura credenciais de registro.

## 2. Configurar segredo local

Bash:

```bash
export OPENROUTER_API_KEY='sua-chave'
```

PowerShell:

```powershell
$env:OPENROUTER_API_KEY = 'sua-chave'
```

`infra/parameters/demo.bicepparam` lê valor com `readEnvironmentVariable`. Chave não deve ser versionada nem passada em texto no comando.

## 3. Criar resource group

```bash
az group create --name rg-nexovital-demo --location eastus2
```

## 4. Validar templates

```bash
az bicep build --file infra/main.bicep
az bicep build-params --file infra/parameters/demo.bicepparam
```

## 5. Implantar infraestrutura

```bash
az deployment group create \
  --name nexovital-demo \
  --resource-group rg-nexovital-demo \
  --template-file infra/main.bicep \
  --parameters infra/parameters/demo.bicepparam
```

Workflow `.github/workflows/deploy-azure.yml` usa OIDC e segredo GitHub `OPENROUTER_API_KEY`.

## 6. Frontend

Bicep cria recurso Static Web App. Publicação do frontend ainda depende da conexão do repositório ao Static Web Apps ou workflow específico do serviço.

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

Configure `VITE_API_BASE_URL` com output `backendUrl` antes do build publicado.

## Outputs

- `frontendUrl`;
- `backendUrl`;
- `backendImage`;
- `speechResourceName`;
- `languageResourceName`;
- `languageEndpoint`.

## Remoção

Operação destrutiva:

```bash
az group delete --name rg-nexovital-demo --yes --no-wait
```

Projeto demonstrativo acadêmico. Free tier depende de disponibilidade regional e limites da assinatura.
