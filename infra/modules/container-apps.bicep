@description('Nome do Container Apps Environment.')
param environmentName string

@description('Nome do Container App do backend.')
param backendName string

@description('Região Azure.')
param location string

@description('URL completa da imagem ACR.')
param backendImage string

@description('Servidor de login do ACR.')
param acrLoginServer string

@description('Usuário admin do ACR.')
param acrUsername string

@description('Senha admin do ACR.')
@secure()
param acrPassword string

@description('Chave do Azure Speech.')
@secure()
param speechKey string

@description('Região do Azure Speech.')
param speechRegion string

@description('Chave do Azure AI Language.')
@secure()
param languageKey string

@description('Endpoint do Azure AI Language.')
param languageEndpoint string

@description('Tags dos recursos.')
param tags object = {}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'none'
    }
  }
  tags: tags
}

resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: backendName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
      }
      secrets: [
        {
          name: 'registry-password'
          value: acrPassword
        }
        {
          name: 'azure-speech-key'
          value: speechKey
        }
        {
          name: 'azure-language-key'
          value: languageKey
        }
      ]
      registries: [
        {
          server: acrLoginServer
          username: acrUsername
          passwordSecretRef: 'registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          env: [
            {
              name: 'APP_ENV'
              value: 'demo'
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'CORS_ORIGINS'
              value: '*'
            }
            {
              name: 'AZURE_SPEECH_KEY'
              secretRef: 'azure-speech-key'
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: speechRegion
            }
            {
              name: 'AZURE_LANGUAGE_KEY'
              secretRef: 'azure-language-key'
            }
            {
              name: 'AZURE_LANGUAGE_ENDPOINT'
              value: languageEndpoint
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/health'
                port: 8000
              }
              initialDelaySeconds: 20
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 15
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
  tags: tags
}

output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
