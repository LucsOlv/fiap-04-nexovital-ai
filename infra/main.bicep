targetScope = 'resourceGroup'

@description('Nome do projeto usado como prefixo dos recursos.')
param projectName string = 'nexovital'

@description('Ambiente único do MVP.')
@allowed([
  'demo'
])
param environment string = 'demo'

@description('Região Azure para deploy.')
param location string = 'eastus2'

@description('URL completa da imagem Docker do backend no ACR.')
param backendImage string

@description('Servidor de login do ACR.')
param acrLoginServer string

@description('Usuário admin do ACR.')
param acrUsername string

@description('Senha admin do ACR.')
@secure()
param acrPassword string

@description('URL do repositório GitHub do projeto.')
param repoUrl string

@description('Email para alerta de orçamento.')
param notificationEmail string

@description('Tags extras opcionais.')
param tags object = {}

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id, projectName, environment))
var defaultTags = union({
  project: 'NexoVital AI'
  environment: environment
  managedBy: 'Bicep'
  repository: repoUrl
}, tags)

var staticWebAppName = '${projectName}-${environment}-swa-${suffix}'
var managedEnvironmentName = '${projectName}-${environment}-cae'
var backendAppName = '${projectName}-${environment}-backend'
var speechName = take('${projectName}${environment}speech${suffix}', 63)
var languageName = take('${projectName}${environment}language${suffix}', 63)
var budgetName = '${projectName}-${environment}-budget'

module cognitiveServices 'modules/cognitive-services.bicep' = {
  name: 'cognitive-services'
  params: {
    speechName: speechName
    languageName: languageName
    location: location
    tags: defaultTags
  }
}

module containerApps 'modules/container-apps.bicep' = {
  name: 'container-apps'
  params: {
    environmentName: managedEnvironmentName
    backendName: backendAppName
    location: location
    backendImage: backendImage
    acrLoginServer: acrLoginServer
    acrUsername: acrUsername
    acrPassword: acrPassword
    speechKey: cognitiveServices.outputs.speechKey
    speechRegion: cognitiveServices.outputs.speechRegion
    languageKey: cognitiveServices.outputs.languageKey
    languageEndpoint: cognitiveServices.outputs.languageEndpoint
    tags: defaultTags
  }
}

module staticWebApp 'modules/static-web-app.bicep' = {
  name: 'static-web-app'
  params: {
    swaName: staticWebAppName
    location: location
    repoUrl: repoUrl
    tags: defaultTags
  }
}

module budget 'modules/budget.bicep' = {
  name: 'budget'
  params: {
    budgetName: budgetName
    notificationEmail: notificationEmail
  }
}

output frontendUrl string = staticWebApp.outputs.frontendUrl
output backendUrl string = containerApps.outputs.backendUrl
output speechResourceName string = speechName
output languageResourceName string = languageName
output languageEndpoint string = cognitiveServices.outputs.languageEndpoint
output repoUrlOutput string = repoUrl
