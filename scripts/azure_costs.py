from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta

credential = DefaultAzureCredential()
subscription_id = "e64020ae-80db-40fb-b774-3fbafdcf48a0"

# Define the time range for cost data (last 30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Format dates the way Azure Cost Management API expects
start = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
end = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

print(f"Fetching cost data from {start} to {end}")

client = CostManagementClient(credential)

scope = f"/subscriptions/{subscription_id}"

results = client.query.usage(
    scope=scope,
    parameters={
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {
            "from": start,
            "to": end
        },
        "dataset": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {
                    "name": "Cost",
                    "function": "Sum"
                }
            },
            "grouping": [
                {
                    "type": "Dimension",
                    "name": "ResourceGroup"
                }
            ]
        }
    }
)

print(f"\n{'Resource Group':<40} {'Cost':>10} {'Currency'}")
print("-" * 55)

for row in results.rows:
    cost = row[0]
    resource_group = row[1]
    currency = row[2]
    print(f"{resource_group:<40} ${cost:>9.4f} {currency}")

print("-" * 55)
total = sum(row[0] for row in results.rows)
print(f"{'Total':<40} ${total:>9.4f} USD")