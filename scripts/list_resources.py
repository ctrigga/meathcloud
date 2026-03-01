from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

credentials = DefaultAzureCredential()
subscription_id = "e64020ae-80db-40fb-b774-3fbafdcf48a0"

client = ResourceManagementClient(credentials, subscription_id)

for group in client.resource_groups.list():
    print(f"Resource group: {group.name}) | Location {group.location}")

    resources = client.resources.list_by_resource_group(group.name)
    for resource in resources:
        print(f"  - {resource.name} ({resource.type})")