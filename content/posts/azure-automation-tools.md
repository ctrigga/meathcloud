---
title: "Python and Azure: Building Real Automation Tools"
date: 2026-03-01
draft: false
tags: ["python", "azure", "automation", "cli", "cost-management"]
---

# Python and Azure: Building Real Automation Tools

After writing my first Python script to list Azure resources, the next step was building something more useful. Today I wrote two scripts that I'll actually use day to day — an Azure cost reporter and a Static Web App status checker. Both taught me new Python concepts while solving real problems.

---

## Script 1: Azure Cost Reporter

The goal was simple — pull my Azure spending for a given time period and display it in a clean readable format, grouped by resource group.

### The Setup

Beyond the standard `azure-identity` package, this script needed the cost management SDK:

```bash
pip3 install azure-mgmt-costmanagement
```

And a new import — `argparse`, Python's built-in library for handling command line arguments. No install needed, it's part of the standard library.

### Date Handling

The Azure Cost Management API requires full ISO 8601 datetime strings — not just dates. This tripped me up initially:

```python
# This fails - API wants full datetime
start = start_date.strftime("%Y-%m-%d")

# This works
start = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
```

The `T` separates date from time, `%H:%M:%S` adds hours/minutes/seconds, and `Z` denotes UTC. A small detail that caused a big error.

### Adding CLI Arguments with argparse

Instead of hardcoding a 30 day lookback period, I added a `--days` argument so the date range is configurable at runtime:

```python
parser = argparse.ArgumentParser(description="Azure Cost Report")
parser.add_argument("--days", type=int, default=30, help="Number of days to look back (default: 30)")
args = parser.parse_args()

end_date = datetime.now()
start_date = end_date - timedelta(days=args.days)
```

`argparse` also generates a `--help` flag automatically:

```bash
python3 scripts/azure_costs.py --help
```

Now the script is flexible — run it different ways depending on what you need:

```bash
# Default 30 days
python3 scripts/azure_costs.py

# Last 7 days
python3 scripts/azure_costs.py --days 7

# Last 60 days
python3 scripts/azure_costs.py --days 60
```

### Formatted Output

The raw API response comes back as a list of rows. Formatting it into a readable table uses Python's f-string alignment syntax:

```python
print(f"{'Resource Group':<40} {'Cost':>10} {'Currency'}")
print("-" * 55)

for row in results.rows:
    cost = row[0]
    resource_group = row[1]
    currency = row[2]
    print(f"{resource_group:<40} ${cost:>9.4f} {currency}")

total = sum(row[0] for row in results.rows)
print(f"{'Total':<40} ${total:>9.4f} USD")
```

- `:<40` left-aligns text in a 40 character wide column
- `:>9.4f` right-aligns a float with 4 decimal places
- `sum(row[0] for row in results.rows)` is a generator expression — a compact way to sum values from a list

### The Output

```
Fetching cost data from 2026-01-30 to 2026-03-01

Resource Group                                Cost Currency
-------------------------------------------------------
cloud-shell-storage-eastus               $   0.0000 USD
z06fan53-rg                              $   0.0528 USD
-------------------------------------------------------
Total                                    $   0.0528 USD
```

Five cents in. The free tier is doing its job.

---

## Script 2: Static Web App Status Checker

The second script checks the status of my Azure Static Web App — pulling live details about the app, its repository connection, and configuration.

### Finding the Right Attributes

The Azure SDK returns objects with a lot of attributes. When I wasn't sure what was available, I used Python's built-in `dir()` to inspect the object:

```python
for app in apps:
    print(dir(app))
```

This prints every attribute and method available on the object — a useful debugging technique when working with unfamiliar SDK objects. From the output I could see exactly what fields were available and pick the meaningful ones.

### The Output

```
Checking Static Web Apps in resource group: CloudSite

App Name                           Tier Status
----------------------------------------------------------------------
MyCloudSite                        East US 2            Free
  Hostname   : white-desert-05116c60f.1.azurestaticapps.net
  Repository : https://github.com/ctrigga/meathcloud
  Branch     : main
  Provider   : GitHub
  Staging    : Enabled
```

One thing worth noting — Azure Static Web Apps don't have a traditional running/stopped status the way virtual machines do. They're either deployed or not. The most meaningful status fields are the pricing tier and whether staging environments are enabled.

### Required Arguments

Unlike the cost script where `--days` was optional with a default, the resource group name is required since there's no sensible default:

```python
parser.add_argument("--resource-group", type=str, required=True, help="Resource group name")
```

If you run the script without it, argparse catches it immediately and tells you exactly what's missing. Building that kind of input validation in from the start is good practice.

---

## What I Learned

A few Python concepts that clicked through building these:

**argparse is powerful and simple.** Adding a proper CLI interface to a script takes about four lines of code and you get input validation, help text, and type checking for free.

**dir() is your friend.** When working with unfamiliar objects or SDKs, printing `dir(object)` to see all available attributes saves a lot of time digging through documentation.

**Generator expressions are concise.** `sum(row[0] for row in results.rows)` is the Python way to do what in PowerShell would be a `ForEach-Object` with an accumulator variable. Once you see the pattern it's very readable.

**The Azure SDK is consistent.** The pattern across all three scripts so far is the same — credential, client, call, iterate. Learning that pattern once means picking up new SDK modules is fast.

---

## What's Next

Both scripts live in the `scripts/` folder of the [GitHub repo](https://github.com/ctrigga/meathcloud). Next up is Infrastructure as Code with Bicep — defining Azure resources in code rather than clicking through the portal, and tying it into the same GitHub Actions pipeline that deploys this site.