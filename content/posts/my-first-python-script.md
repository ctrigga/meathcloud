---
title: "My First Python Script: Querying Azure Resources"
date: 2026-02-28
draft: false
tags: ["python", "azure", "automation", "powershell"]
---

# My First Python Script: Querying Azure Resources

One of my goals with this site is to document the transition from traditional sysadmin work into cloud engineering — and that means learning Python. I've been able to read Python for a while, but writing it is a different story. Today I wrote my first real script, and I figured the best way to learn was to do something I already know how to do, just in a new language.

---

## What I Would Have Done in PowerShell

As a sysadmin with a Windows and Azure background, querying Azure resources in PowerShell is second nature:

```powershell
Connect-AzAccount
Get-AzResourceGroup | ForEach-Object {
    Write-Host "`nResource Group: $($_.ResourceGroupName) | Location: $($_.Location)"
    Get-AzResource -ResourceGroupName $_.ResourceGroupName | ForEach-Object {
        Write-Host "  - $($_.Name) ($($_.ResourceType))"
    }
}
```

Straightforward. Connect, get resource groups, loop through them, list what's inside. I've written variations of this more times than I can count.

The goal today was to do the exact same thing in Python.

---

## Setting Up the Environment

Before writing any code I had to get my Python environment sorted. On Mac with Homebrew, Python installs cleanly but pip is restricted from installing packages globally — a protection Homebrew puts in place to avoid conflicts.

The solution is a virtual environment, which is standard practice in Python development anyway:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install azure-identity azure-mgmt-resource azure-mgmt-compute
```

The `.venv` folder lives in my project directory but gets ignored by git. Every time I open a new terminal session I activate it with `source .venv/bin/activate` before running any Python scripts.

---

## The Script

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

credential = DefaultAzureCredential()
subscription_id = "your-subscription-id"

client = ResourceManagementClient(credential, subscription_id)

for group in client.resource_groups.list():
    print(f"\nResource Group: {group.name} | Location: {group.location}")
    
    resources = client.resources.list_by_resource_group(group.name)
    for resource in resources:
        print(f"  - {resource.name} ({resource.type})")
```

It worked on the first run. Here's what it's actually doing:

**Imports** — Python pulls in only what it needs. `DefaultAzureCredential` handles authentication and `ResourceManagementClient` is the SDK client for interacting with Azure Resource Manager.

**Authentication** — This is the part that impressed me most coming from PowerShell. `DefaultAzureCredential` automatically uses my existing `az login` session — no hardcoded passwords, no API keys sitting in the script, no secrets to accidentally commit to GitHub. It checks a chain of credential sources in order and uses whatever is available. In production you'd use a managed identity or service principal and this same line of code handles that too without any changes.

**The client** — `ResourceManagementClient` takes the credential and subscription ID and gives you a clean interface to Azure's REST APIs. No manual HTTP requests, no token management.

**The loops** — This is where Python starts to feel familiar coming from PowerShell. The outer loop iterates over resource groups, the inner loop iterates over resources within each group. The `f""` strings for formatting output are cleaner than PowerShell's `$()` syntax once you get used to them.

---

## The Output

Running the script printed out every resource group in my subscription with all resources nested underneath — my Static Web App, DNS zones, and everything else I've provisioned so far. Seeing live Azure data come back from a script I wrote myself made the whole thing click.

---

## What Felt Different

A few things stood out coming from a PowerShell background:

**No cmdlets** — PowerShell's verb-noun structure (`Get-AzResourceGroup`) is very readable but hides a lot of what's happening. Python's SDK feels closer to the metal — you're working with objects and methods directly, which makes it clearer what the API is actually doing.

**Indentation matters** — Python uses indentation to define code blocks instead of curly braces or `{}`. Coming from PowerShell this felt weird for about ten minutes and then made total sense.

**Virtual environments** — There's no real PowerShell equivalent to this. The concept of isolating dependencies per project is new but immediately makes sense — especially when you're working on multiple projects with potentially conflicting package versions.

---

## What's Next

This was a deliberately simple first script — the Python equivalent of a Hello World for Azure automation. From here the plan is to build more complex scripts: automating resource provisioning, pulling cost data, eventually wiring Python scripts into the site itself to display live Azure data.

Every script gets committed to the [GitHub repo](https://github.com/yourusername) alongside this site.