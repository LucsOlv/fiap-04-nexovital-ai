@description('Nome do recurso Azure Speech.')
param speechName string

@description('Nome do recurso Azure AI Language.')
param languageName string

@description('Região Azure.')
param location string

@description('Tags dos recursos.')
param tags object = {}

resource speech 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: {
    name: 'F0'
  }
  properties: {
    customSubDomainName: speechName
  }
  tags: tags
}

resource language 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: languageName
  location: location
  kind: 'TextAnalytics'
  sku: {
    name: 'F0'
  }
  properties: {
    customSubDomainName: languageName
  }
  tags: tags
}

@secure()
output speechKey string = speech.listKeys().key1
output speechRegion string = location
@secure()
output languageKey string = language.listKeys().key1
output languageEndpoint string = 'https://${languageName}.cognitiveservices.azure.com/'
