---
title: "Infrastructure as Code with Bicep: Deploying a Windows 11 Dev VM"
date: 2026-03-05
draft: false
tags: ["azure", "bicep", "iac", "windows", "devops"]
---

# Infrastructure as Code with Bicep: Deploying a Windows 11 Dev VM

Day 3 of the cloud engineering transition. Today's goal was twofold — learn Infrastructure as Code using Azure Bicep, and solve a real problem: getting a proper Windows development environment accessible from an iPad via Microsoft's Windows App.

The result is a Windows 11 VM provisioned entirely from code, with auto-shutdown at midnight, RDP access locked down via NSG, and a static public IP that doesn't change between reboots. All deployed with a single command.

---

## Why Infrastructure as Code?

Up until now everything Azure-related in this project has been provisioned through the portal — clicking through wizards, filling in forms, hitting deploy. That works, but it has problems:

- It's not repeatable — recreating the same environment means remembering every setting
- It's not version controlled — there's no history of what changed and when
- It's not documentable — you can't read a portal session like you can read code

IaC solves all of this. The entire infrastructure lives in a file, committed to git, deployable with one command. If the VM gets deleted or corrupted, redeployment takes 4 minutes.

---

## Why Bicep?

Bicep is Microsoft's native IaC language for Azure — it compiles down to ARM templates but is much more readable. The alternative is Terraform, which has broader multi-cloud support, but for an Azure-focused portfolio Bicep made sense as a starting point. It integrates cleanly with the Azure CLI and VS Code has excellent Bicep extension support.

---

## The Template Structure

The full template lives at `infra/dev-vm/main.bicep` in the repo. Here's how it's organized.

### Parameters and Variables

```bicep
@description('Username for the VM')
param adminUsername string

@description('Password for the VM')
@secure()
param adminPassword string

@description('Location for all resources')
param location string = resourceGroup().location

var vmName = 'dev-vm'
var vmSize = 'Standard_D2s_v3'
var vnetName = 'dev-vnet'
var subnetName = 'dev-subnet'
var nsgName = 'dev-nsg'
var publicIpName = 'dev-pip'
var nicName = 'dev-nic'
```

The `@secure()` decorator on `adminPassword` tells Bicep to treat it as a secret — it won't appear in deployment logs or outputs. Credentials are passed in via a parameters file that's excluded from git via `.gitignore`.

### Networking

Four networking resources get provisioned in the right dependency order — Bicep figures out the order automatically based on resource references:

- **NSG** with a single inbound rule allowing RDP (port 3389)
- **Public IP** with Standard SKU and Static allocation so the IP doesn't change between reboots
- **VNet** with a `10.0.0.0/16` address space and a `/24` subnet
- **NIC** connecting the VM to the subnet and public IP

### The VM

```bicep
resource vm 'Microsoft.Compute/virtualMachines@2023-03-01' = {
  name: vmName
  location: location
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      adminPassword: adminPassword
    }
    storageProfile: {
      imageReference: {
        publisher: 'MicrosoftWindowsDesktop'
        offer: 'windows-11'
        sku: 'win11-25h2-pro'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Standard_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}
```

One thing worth noting — B-series VMs are being phased out in Azure. D2s_v3 is the current equivalent at a similar price point (~$0.10/hour).

### Auto-Shutdown

```bicep
resource autoShutdown 'Microsoft.DevTestLab/schedules@2018-09-15' = {
  name: 'shutdown-computevm-${vmName}'
  location: location
  properties: {
    status: 'Enabled'
    taskType: 'ComputeVmShutdownTask'
    dailyRecurrence: {
      time: '0500'
    }
    timeZoneId: 'Eastern Standard Time'
    targetResourceId: vm.id
    notificationSettings: {
      status: 'Disabled'
    }
  }
}
```

Auto-shutdown at midnight EST (05:00 UTC) via Azure DevTest Labs schedules. If I forget to deallocate manually, Azure handles it automatically. The VM deallocates rather than just shutting down — meaning compute billing stops entirely.

### Output

```bicep
output vmPublicIP string = publicIp.properties.ipAddress
```

After deployment the public IP prints directly to the terminal. No hunting through the portal.

---

## The Deployment

```bash
# Create the resource group
az group create --name rg-dev-vm --location eastus

# Deploy the template
az deployment group create \
  --resource-group rg-dev-vm \
  --template-file infra/dev-vm/main.bicep \
  --parameters @infra/dev-vm/dev-vm.parameters.json
```

3 minutes and 43 seconds later:

```json
"outputs": {
  "vmPublicIP": {
    "type": "String",
    "value": "20.106.160.134"
  }
}
```

Plugged that IP into Windows App on the iPad, connected as `devadmin`, and was in a full Windows 11 desktop within minutes.

---

## Cost Management

The D2s_v3 runs at roughly $0.10/hour. With auto-shutdown at midnight and manual deallocation when done, realistic monthly cost for occasional use is $2-5. Well within the Azure credit budget.

To manually deallocate from the terminal when done for the day:

```bash
az vm deallocate --resource-group rg-dev-vm --name dev-vm
```

To start it back up:

```bash
az vm start --resource-group rg-dev-vm --name dev-vm
```

---

## What I Learned

**Bicep dependency resolution is smart.** Resources reference each other using `.id` properties and Bicep figures out the deployment order automatically. No need to manually specify dependencies in most cases.

**Parameters files keep secrets out of code.** The `@secure()` decorator combined with a gitignored parameters file means credentials never touch the repo. Same pattern works for API keys, connection strings, and any other sensitive values.

**IaC makes rebuilding trivial.** The entire environment — networking, compute, scheduling — deploys in under 4 minutes from a single command. That's the real value of IaC over portal clicks.

**Azure free trial has VM size restrictions.** B-series VMs weren't available on the trial subscription. Converting to Pay-As-You-Go (while keeping the $200 credit) unlocked the full VM catalog. Worth doing early.

---

## What's Next

The Bicep template is a solid foundation. Next steps are expanding it — adding a managed disk for persistent storage, locking down the NSG to specific IP ranges rather than open RDP, and eventually wiring the VM provisioning into the GitHub Actions pipeline so infrastructure changes deploy the same way the site does.

The full Bicep template is in the [GitHub repo](https://github.com/ctrigga/meathcloud) under `infra/dev-vm/`.
