---
title: "Data Engineering on Azure: Building My First ETL Pipeline"
date: 2026-03-05
draft: false
tags: ["azure", "python", "data-engineering", "etl", "blob-storage", "bicep"]
---

# Data Engineering on Azure: Building My First ETL Pipeline

Day 4 of the cloud engineering transition. Today I crossed into data engineering territory — spinning up Azure Storage and Data Factory infrastructure with Bicep, then writing a Python ETL pipeline that pulls live weather data and lands it in Azure Blob Storage.

It's a simple pipeline by design, but it covers the full ETL pattern that every data engineering project is built on.

---

## The Infrastructure

Before writing any Python, I provisioned the data engineering foundation using Bicep — keeping the IaC habit going from Day 3.

Two resources in the template:

**Azure Storage Account** with a `raw-data` blob container for landing data:

```bicep
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
```

**Azure Data Factory** with a system-assigned managed identity:

```bicep
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
```

The managed identity is important — it gives Data Factory its own identity in Azure AD so it can authenticate to other Azure services without hardcoded credentials. Same principle as `DefaultAzureCredential` in Python.

Deployed with a single command:

```bash
az group create --name rg-data-engineering --location eastus

az deployment group create \
  --resource-group rg-data-engineering \
  --template-file infra/data-engineering/main.bicep
```

Outputs after deployment:
```
storageAccountName     : stmeathclouddev
dataFactoryName        : adfmeathclouddev
storageAccountEndpoint : https://stmeathclouddev.blob.core.windows.net/
```

---

## The ETL Pipeline

ETL stands for Extract, Transform, Load — the three stages of any data pipeline:

- **Extract** — pull data from a source
- **Transform** — clean, reshape, or enrich it
- **Load** — land it somewhere useful

Today's pipeline hits all three using the Open-Meteo API (free, no API key required) as the data source and Azure Blob Storage as the destination.

### Extract — Pulling Weather Data

```python
latitude = 38.9072
longitude = -77.0369
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=temperature_2m,precipitation,windspeed_10m"

with urllib.request.urlopen(url) as response:
    raw_data = response.read()
    weather_data = json.loads(raw_data)
```

`urllib.request` is Python's built-in HTTP library — no install needed. The API returns a JSON response with current conditions and hourly forecasts.

### Transform — Converting to Imperial Units

```python
temp_f = round((weather_data['current_weather']['temperature'] * 9/5) + 32, 1)
windspeed_mph = round(weather_data['current_weather']['windspeed'] * 0.621371, 1)

print(f"Current temperature: {temp_f}°F")
print(f"Current windspeed: {windspeed_mph} mph")
```

Simple unit conversion from Celsius/km/h to Fahrenheit/mph. In a more complex pipeline this stage might clean dirty data, join multiple sources, or reshape the structure entirely.

### Load — Landing in Azure Blob Storage

```python
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=f"https://{storage_account}.blob.core.windows.net/",
    credential=credential
)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
blob_name = f"weather/dc_{timestamp}.json"

blob_client = blob_service_client.get_blob_client(
    container=container_name,
    blob=blob_name
)

blob_client.upload_blob(json_data, overwrite=True)
```

Each run creates a new timestamped JSON file in the `raw-data` container — so data accumulates over time rather than overwriting. Running this hourly would build a historical weather dataset.

---

## The Permissions Gotcha

The first upload attempt hit an authorization error:

```
azure.core.exceptions.HttpResponseError: AuthorizationPermissionMismatch
```

The storage account was provisioned but my Azure CLI account didn't have write permissions to it. The fix was assigning the **Storage Blob Data Contributor** role:

```bash
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <your-object-id> \
  --scope "/subscriptions/<sub-id>/resourceGroups/rg-data-engineering/providers/Microsoft.Storage/storageAccounts/stmeathclouddev"
```

Role assignments take a few minutes to propagate through Azure AD. After waiting and rerunning the script it uploaded cleanly.

This is an important pattern — in Azure, provisioning a resource and having permission to use it are two separate things. RBAC (Role Based Access Control) controls access explicitly. Good security practice, but something to plan for when building pipelines.

---

## The Result

Running the script produces:

```
Connected to Azure Blob Storage account: stmeathclouddev
Fetching weather data...
Current temperature: 49.6°F
Current windspeed: 8.6 mph
Uploading to blob: weather/dc_2026-03-05_22-57-36.json
Successfully uploaded to stmeathclouddev/raw-data/weather/dc_2026-03-05_22-57-36.json
```

The JSON file sits in Azure Blob Storage, visible in the portal under the `raw-data` container. Every run adds another timestamped file — run it on a schedule and you've got a growing historical dataset.

---

## What I Learned

**ETL is a universal pattern.** Every data pipeline regardless of scale is some variation of extract, transform, load. Understanding it at this small scale makes the bigger tools (Data Factory, Databricks, Spark) easier to reason about.

**RBAC is separate from provisioning.** Creating a resource doesn't automatically grant you permission to use it. Role assignments are explicit and take time to propagate — something to account for when automating deployments.

**`urllib.request` is underrated.** For simple API calls you don't need requests or httpx — Python's standard library handles it fine. Save the extra dependencies for when you actually need them.

**Timestamped blob naming is a data engineering convention.** Landing files with timestamps rather than fixed names preserves history and makes pipelines idempotent — you can rerun them without losing previous data.

---

## What's Next

The pipeline works but it only runs when I manually execute the script. The next step is scheduling it — using Azure Data Factory to trigger the pipeline automatically on a schedule, so data accumulates without any manual intervention. After that, adding a transformation step that processes the raw JSON into a clean flat structure ready for analysis.

The full script is in the [GitHub repo](https://github.com/ctrigga/meathcloud) under `scripts/weather_etl.py`, and the Bicep template is under `infra/data-engineering/`.