import json
import urllib.request
import argparse
import sys
from datetime import datetime, timezone

BASE_URL = "https://api.openf1.org/v1"
DEFAULT_SESSION_KEY = 9839      # 2025 Abu Dhabi Grand Prix - fallback POC
DEFAULT_RACE_NAME = "abu_dhabi_2025"

def fetch(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    print(f"  Fetching: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  WARNING: No data available yet for this session ({endpoint})")
            return []
        raise

def main():
    parser = argparse.ArgumentParser(description="F1 Race ETL")
    parser.add_argument("--session-key", type=int, default=DEFAULT_SESSION_KEY)
    parser.add_argument("--race-name", type=str, default=DEFAULT_RACE_NAME)
    args = parser.parse_args()
    # Detect if args were explicitly passed
    session_key_provided = "--session-key" in sys.argv
    race_name_provided = "--race-name" in sys.argv

    # Enforce both or neither
    if session_key_provided != race_name_provided:
        print("ERROR: --session-key and --race-name must be provided together.")
        print("  Example: python scripts/f1_etl.py --session-key 11234 --race-name australia_2026")
        sys.exit(1)

    # Basic race name format check
    if race_name_provided:
        import re
        if not re.match(r'^[a-z0-9_]+$', args.race_name):
            print("ERROR: --race-name must be lowercase letters, numbers, and underscores only.")
            print("  Example: australia_2026, abu_dhabi_2025")
            sys.exit(1)

    SESSION_KEY = args.session_key
    RACE_NAME = args.race_name.lower().replace(" ", "_")

    print(f"=== F1 ETL - {RACE_NAME} (Race) ===")
    print(f"Session key: {SESSION_KEY}\n")

    # Pull session metadata
    print("[ Session ]")
    sessions = fetch("sessions", {"session_key": SESSION_KEY})
    session = sessions[0]
    if session["session_type"] != "Race" or session["session_name"] != "Race":
        print(f"  WARNING: session_key {SESSION_KEY} is a {session['session_name']} "
              f"not a Race. Aborting.")
        sys.exit(1)
    print(f"  Name:     {session['session_name']}")
    print(f"  Type:     {session['session_type']}")
    print(f"  Country:  {session['country_name']}")
    print(f"  Circuit:  {session['circuit_short_name']}")
    print(f"  Start:    {session['date_start']}")
    print(f"  End:      {session['date_end']}")

    # Pull drivers
    print("\n[ Drivers ]")
    drivers = fetch("drivers", {"session_key": SESSION_KEY})
    drivers_by_number = {d["driver_number"]: d for d in drivers}
    for d in sorted(drivers, key=lambda x: x["driver_number"]):
        print(f"  #{d['driver_number']:>2}  {d['name_acronym']}  {d.get('team_name', 'N/A')}")

    print(f"\nTotal drivers: {len(drivers)}")

    # Pull lap times
    print("\n[ Lap Times ]")
    laps = fetch("laps", {"session_key": SESSION_KEY})
    print(f"  Total laps fetched: {len(laps)}")
    completed = [l for l in laps if l.get("lap_duration") is not None]
    # Quick sanity check - show fastest lap
    if completed:
        fastest = min(completed, key=lambda x: x["lap_duration"])
        driver = drivers_by_number.get(fastest["driver_number"], {})
        print(f"  Fastest lap: {fastest['lap_duration']:.3f}s  "
              f"by #{fastest['driver_number']} {driver.get('name_acronym','?')} "
              f"on lap {fastest['lap_number']}")
    else:
        print("  No completed laps available yet.")

    # Pull stints (pit stop strategy)
    print("\n[ Stints ]")
    stints = fetch("stints", {"session_key": SESSION_KEY})
    print(f"  Total stints fetched: {len(stints)}")
    # Count stops per driver
    stops_per_driver = {}
    for s in stints:
        n = s["driver_number"]
        stops_per_driver[n] = stops_per_driver.get(n, 0) + 1
    for num, count in sorted(stops_per_driver.items()):
        acronym = drivers_by_number.get(num, {}).get("name_acronym", "?")
        print(f"  #{num:>2} {acronym}: {count} stints ({count - 1} stop{'s' if count - 1 != 1 else ''})")

    # Pull weather
    print("\n[ Weather ]")
    weather = fetch("weather", {"session_key": SESSION_KEY})
    print(f"  Total weather samples: {len(weather)}")
    if weather:
        w = weather[0]
        print(f"  Sample: air={w.get('air_temperature')}°C  "
              f"track={w.get('track_temperature')}°C  "
              f"humidity={w.get('humidity')}%  "
              f"rainfall={w.get('rainfall')}")
        
        # Bundle payload
    print("\n[ Bundling Payload ]")
    payload = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "session": session,
        "drivers": drivers,
        "laps": laps,
        "stints": stints,
        "weather": weather,
    }
    print(f"  Keys: {list(payload.keys())}")

    # Upload to blob storage
    print("\n[ Uploading to Blob Storage ]")
    from azure.storage.blob import BlobServiceClient
    from azure.identity import DefaultAzureCredential

    account_url = "https://stmeathclouddev.blob.core.windows.net"
    container = "raw-data"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    blob_name = f"f1/{RACE_NAME}/race_{timestamp}.json"

    credential = DefaultAzureCredential()
    client = BlobServiceClient(account_url=account_url, credential=credential)
    blob_client = client.get_blob_client(container=container, blob=blob_name)

    data = json.dumps(payload, indent=2)
    blob_client.upload_blob(data, overwrite=True)

    print(f"  Uploaded: {blob_name}")
    print(f"  Size: {len(data):,} bytes")
    print("\nETL complete.")

if __name__ == "__main__":
    main()

    