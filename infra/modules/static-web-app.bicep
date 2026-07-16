@description('Nome do Azure Static Web App.')
param swaName string

@description('Região Azure.')
param location string

@description('URL do repositório GitHub do projeto.')
param repoUrl string

@description('Tags dos recursos.')
param tags object = {}

resource swa 'Microsoft.Web/staticSites@2022-09-01' = {
  name: swaName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  tags: union(tags, {
    repoUrl: repoUrl
  })
}

output frontendUrl string = 'https://${swa.properties.defaultHostname}'
output defaultHostname string = swa.properties.defaultHostname
