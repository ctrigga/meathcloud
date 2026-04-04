targetScope = 'subscription'

@description('Location for all resources')
param location string = 'eastus'

@description('Resource group name')
param resourceGroupName string = 'rg-data-engineering'

// ── RG-scoped resources (workspace + storage diagnostics) ────────────────────
module rgResources 'monitoring-rg.bicep' = {
  name: 'monitoring-rg-resources'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

// ── Subscription activity log → Log Analytics ────────────────────────────────
resource subscriptionDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'diag-activity-log'
  scope: subscription()
  properties: {
    workspaceId: rgResources.outputs.workspaceId
    logs: [
      { category: 'Administrative', enabled: true }
      { category: 'Security',       enabled: true }
      { category: 'ServiceHealth',  enabled: true }
      { category: 'Alert',          enabled: true }
      { category: 'Policy',         enabled: true }
    ]
  }
}

// ── Outputs ──────────────────────────────────────────────────────────────────
output workspaceId string = rgResources.outputs.workspaceId
output workspaceName string = rgResources.outputs.workspaceName
output customerId string = rgResources.outputs.customerId
