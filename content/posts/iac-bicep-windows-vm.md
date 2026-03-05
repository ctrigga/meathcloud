{
  "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Resources/deployments/main",
  "location": null,
  "name": "main",
  "properties": {
    "correlationId": "7f1c98c0-6d9b-43e3-bdac-420e72aeb778",
    "debugSetting": null,
    "dependencies": [
      {
        "dependsOn": [
          {
            "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/networkSecurityGroups/dev-nsg",
            "resourceGroup": "rg-dev-vm",
            "resourceName": "dev-nsg",
            "resourceType": "Microsoft.Network/networkSecurityGroups"
          }
        ],
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/virtualNetworks/dev-vnet",
        "resourceGroup": "rg-dev-vm",
        "resourceName": "dev-vnet",
        "resourceType": "Microsoft.Network/virtualNetworks"
      },
      {
        "dependsOn": [
          {
            "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/publicIPAddresses/dev-pip",
            "resourceGroup": "rg-dev-vm",
            "resourceName": "dev-pip",
            "resourceType": "Microsoft.Network/publicIPAddresses"
          },
          {
            "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/virtualNetworks/dev-vnet",
            "resourceGroup": "rg-dev-vm",
            "resourceName": "dev-vnet",
            "resourceType": "Microsoft.Network/virtualNetworks"
          }
        ],
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/networkInterfaces/dev-nic",
        "resourceGroup": "rg-dev-vm",
        "resourceName": "dev-nic",
        "resourceType": "Microsoft.Network/networkInterfaces"
      },
      {
        "dependsOn": [
          {
            "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/networkInterfaces/dev-nic",
            "resourceGroup": "rg-dev-vm",
            "resourceName": "dev-nic",
            "resourceType": "Microsoft.Network/networkInterfaces"
          }
        ],
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Compute/virtualMachines/dev-vm",
        "resourceGroup": "rg-dev-vm",
        "resourceName": "dev-vm",
        "resourceType": "Microsoft.Compute/virtualMachines"
      },
      {
        "dependsOn": [
          {
            "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Compute/virtualMachines/dev-vm",
            "resourceGroup": "rg-dev-vm",
            "resourceName": "dev-vm",
            "resourceType": "Microsoft.Compute/virtualMachines"
          }
        ],
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.DevTestLab/schedules/shutdown-computevm-dev-vm",
        "resourceGroup": "rg-dev-vm",
        "resourceName": "shutdown-computevm-dev-vm",
        "resourceType": "Microsoft.DevTestLab/schedules"
      }
    ],
    "diagnostics": null,
    "duration": "PT3M43.5145561S",
    "error": null,
    "extensions": [],
    "mode": "Incremental",
    "onErrorDeployment": null,
    "outputResources": [
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Compute/virtualMachines/dev-vm",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.Compute/virtualMachines"
      },
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.DevTestLab/schedules/shutdown-computevm-dev-vm",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.DevTestLab/schedules"
      },
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/networkInterfaces/dev-nic",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.Network/networkInterfaces"
      },
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/networkSecurityGroups/dev-nsg",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.Network/networkSecurityGroups"
      },
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/publicIPAddresses/dev-pip",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.Network/publicIPAddresses"
      },
      {
        "apiVersion": null,
        "extension": null,
        "id": "/subscriptions/e64020ae-80db-40fb-b774-3fbafdcf48a0/resourceGroups/rg-dev-vm/providers/Microsoft.Network/virtualNetworks/dev-vnet",
        "identifiers": null,
        "resourceGroup": "rg-dev-vm",
        "resourceType": "Microsoft.Network/virtualNetworks"
      }
    ],
    "outputs": {
      "vmPublicIP": {
        "type": "String",
        "value": "20.106.160.134"
      }
    },
    "parameters": {
      "adminPassword": {
        "type": "SecureString"
      },
      "adminUsername": {
        "type": "String",
        "value": "devadmin"
      },
      "location": {
        "type": "String",
        "value": "eastus"
      }
    },
    "parametersLink": null,
    "providers": [
      {
        "id": null,
        "namespace": "Microsoft.Network",
        "providerAuthorizationConsentState": null,
        "registrationPolicy": null,
        "registrationState": null,
        "resourceTypes": [
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "networkSecurityGroups",
            "zoneMappings": null
          },
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "publicIPAddresses",
            "zoneMappings": null
          },
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "virtualNetworks",
            "zoneMappings": null
          },
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "networkInterfaces",
            "zoneMappings": null
          }
        ]
      },
      {
        "id": null,
        "namespace": "Microsoft.Compute",
        "providerAuthorizationConsentState": null,
        "registrationPolicy": null,
        "registrationState": null,
        "resourceTypes": [
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "virtualMachines",
            "zoneMappings": null
          }
        ]
      },
      {
        "id": null,
        "namespace": "Microsoft.DevTestLab",
        "providerAuthorizationConsentState": null,
        "registrationPolicy": null,
        "registrationState": null,
        "resourceTypes": [
          {
            "aliases": null,
            "apiProfiles": null,
            "apiVersions": null,
            "capabilities": null,
            "defaultApiVersion": null,
            "locationMappings": null,
            "locations": [
              "eastus"
            ],
            "properties": null,
            "resourceType": "schedules",
            "zoneMappings": null
          }
        ]
      }
    ],
    "provisioningState": "Succeeded",
    "templateHash": "10382969007580334307",
    "templateLink": null,
    "timestamp": "2026-03-05T04:10:20.793232+00:00",
    "validatedResources": null,
    "validationLevel": null
  },
  "resourceGroup": "rg-dev-vm",
  "tags": null,
  "type": "Microsoft.Resources/deployments"
}
