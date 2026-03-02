from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
import argparse

credential = DefaultAzureCredential()
subscription_id = "e64020ae-80db-40fb-b774-3fbafdcf48a0"

parser = argparse.ArgumentParser(description="Check Azure Static Web Apps")
parser.add_argument("--resource-group", type=str, required=True, help="Name of the resource group to check")
args = parser.parse_args()

client = WebSiteManagementClient(credential, subscription_id)
print(f"\nChecking Static Web Apps in resource group: {args.resource_group}\n")

apps = client.static_sites.get_static_sites_by_resource_group(args.resource_group)

print(f"{'App Name':<40} {'Location':<20} {'Tier Status'}")
print("-" * 70)

for app in apps:
    print(f"{app.name:<40} {app.location:<20} {app.sku.tier}")
    print(f"  Hostname   : {app.default_hostname}")
    print(f"  Repository : {app.repository_url}")
    print(f"  Branch     : {app.branch}")
    print(f"  Provider   : {app.provider}")
    print(f"  Staging    : {app.staging_environment_policy}")