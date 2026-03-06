from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import urllib.request
import json

credential = DefaultAzureCredential()
storage_account = "stmeathclouddev"
container_name = "raw-data"

blob_service_client = BlobServiceClient(
    account_url=f"https://{storage_account}.blob.core.windows.net/",
    credential=credential
)

print(f"Connected to Azure Blob Storage account: {storage_account}")

# Fetch weather data for Washington DC area
latitude = 38.9072
longitude = -77.0369
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=temperature_2m,precipitation,windspeed_10m"

print("Fetching weather data...")
with urllib.request.urlopen(url) as response:
    raw_data = response.read()
    weather_data = json.loads(raw_data)

# Convert to imperial
temp_f = round((weather_data['current_weather']['temperature'] * 9/5) + 32, 1)
windspeed_mph = round(weather_data['current_weather']['windspeed'] * 0.621371, 1)

print(f"Current temperature: {temp_f}°F")
print(f"Current windspeed: {windspeed_mph} mph")

# Prepare blob name with timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
blob_name = f"weather/dc_{timestamp}.json"

# Convert data to JSON string
json_data = json.dumps(weather_data, indent=2)

# Upload to blob storage
print(f"Uploading to blob: {blob_name}")
blob_client = blob_service_client.get_blob_client(
    container=container_name,
    blob=blob_name
)

blob_client.upload_blob(json_data, overwrite=True)
print(f"Successfully uploaded to {storage_account}/{container_name}/{blob_name}")