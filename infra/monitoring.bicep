@description('Location for all resources')
param location string = resourceGroup().location

@description('Storage account resource ID to attach diagnostics to')
param storageAccountId string = '/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-data-engineering/providers/Microsoft.Storage/storageAccounts/stmeathclouddev'

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
  scope: resourceId('Microsoft.Storage/storageAccounts/blobServices', 'stmeathclouddev', 'default')
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
  scope: resourceId('Microsoft.Storage/storageAccounts', 'stmeathclouddev')
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
