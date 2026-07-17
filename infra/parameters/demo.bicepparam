using '../main.bicep'

param location = 'eastus2'
param backendImage = 'ghcr.io/lucsolv/fiap-04-nexovital-ai/backend:latest'
param repoUrl = 'https://github.com/LucsOlv/fiap-04-nexovital-ai'
param notificationEmail = 'lucs.oliv9@gmail.com'
param openRouterApiKey = readEnvironmentVariable('OPENROUTER_API_KEY')
