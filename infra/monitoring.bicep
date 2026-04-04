@description('Location for all resources')
param location string = resourceGroup().location

// ── Existing resources ───────────────────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: 'stmeathclouddev'
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storageAccount
  name: 'default'
}

// ── Log Analytics Workspace ──────────────────────────────────────────────────
resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-meathcloud-dev'
  location: location
  tags: {
    purpose: 'monitoring'
    environment: 'dev'
    project: 'meathcloud'
  }
  properties: {
    sku: {
      name: 'PerGB2018'  // pay-per-GB, cheapest option
    }
    retentionInDays: 30   // minimum retention, keeps costs near zero
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// ── Diagnostic Settings: stmeathclouddev blob service ───────────────────────
resource blobDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'diag-stmeathclouddev-blob'
  scope: blobService
  properties: {
    workspaceId: workspace.id
    logs: [
      {
        category: 'StorageRead'
        enabled: true
      }
      {
        category: 'StorageWrite'
        enabled: true
      }
      {
        category: 'StorageDelete'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'Transaction'
        enabled: true
      }
    ]
  }
}

// ── Diagnostic Settings: stmeathclouddev storage account (capacity metrics) ─
resource storageDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'diag-stmeathclouddev'
  scope: storageAccount
  properties: {
    workspaceId: workspace.id
    metrics: [
      {
        category: 'Transaction'
        enabled: true
      }
      {
        category: 'Capacity'
        enabled: true
      }
    ]
  }
}

// ── Outputs ──────────────────────────────────────────────────────────────────
output workspaceId string = workspace.id
output workspaceName string = workspace.name
output customerId string = workspace.properties.customerId
