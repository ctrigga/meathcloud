// Data Engineering Foundation
// Storage Account + Azure Data Factory

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Environment name for resource naming.')
param envName string = 'dev'

var storageAccountName = 'stmeathcloud${envName}'
var dataFactoryName = 'adfmeathcloud${envName}'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Blob container for raw data
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
}

resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'raw-data'
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

// Azure Data Factory
resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

output storageAccountName string = storageAccount.name
output dataFactoryName string = dataFactory.name
output storageAccountEndpoint string = storageAccount.properties.primaryEndpoints.blob
