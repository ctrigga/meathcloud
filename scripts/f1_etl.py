import json
import urllib.request
import argparse
import sys
import azure.identity
import azure.storage.blob
from datetime import datetime, timezone

BASE_URL = "https://api.openf1.org/v1"
DEFAULT_SESSION_KEY = 9839
DEFAULT_RACE_NAME = "abu_dhabi_2025"

VALID_SESSION_TYPES = ("Race", "Sprint")

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
    parser = argparse.ArgumentParser(description="F1 Race/Sprint ETL")
    parser.add_argument("--session-key", type=int, default=DEFAULT_SESSION_KEY)
    parser.add_argument("--race-name", type=str, default=DEFAULT_RACE_NAME)
    parser.add_argument("--session-type", type=str, default="Race",
                        choices=VALID_SESSION_TYPES,
                        help="Session type to ingest: Race or Sprint")
    args = parser.parse_args()

    session_key_provided = "--session-key" in sys.argv
    race_name_provided = "--race-name" in sys.argv

    if session_key_provided != race_name_provided:
        print("ERROR: --session-key and --race-name must be provided together.")
        print("  Example: python scripts/f1_etl.py --session-key 11234 --race-name australia_2026")
        sys.exit(1)

    if race_name_provided:
        import re
        if not re.match(r'^[a-z0-9_]+$', args.race_name):
            print("ERROR: --race-name must be lowercase letters, numbers, and underscores only.")
            sys.exit(1)

    SESSION_KEY = args.session_key
    RACE_NAME = args.race_name.lower().replace(" ", "_")
    SESSION_TYPE = args.session_type
    blob_prefix = "sprint_" if SESSION_TYPE == "Sprint" else "race_"

    print(f"=== F1 ETL - {RACE_NAME} ({SESSION_TYPE}) ===")
    print(f"Session key: {SESSION_KEY}\n")

    # Pull session metadata
    print("[ Session ]")
    sessions = fetch("sessions", {"session_key": SESSION_KEY})
    session = sessions[0]

    if session["session_name"] != SESSION_TYPE:
        print(f"  WARNING: session_key {SESSION_KEY} is '{session['session_name']}' "
              f"not '{SESSION_TYPE}'. Aborting.")
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
    if completed:
        fastest = min(completed, key=lambda x: x["lap_duration"])
        driver = drivers_by_number.get(fastest["driver_number"], {})
        print(f"  Fastest lap: {fastest['lap_duration']:.3f}s  "
              f"by #{fastest['driver_number']} {driver.get('name_acronym','?')} "
              f"on lap {fastest['lap_number']}")
    else:
        print("  No completed laps available yet.")

    # Pull stints
    print("\n[ Stints ]")
    stints = fetch("stints", {"session_key": SESSION_KEY})
    print(f"  Total stints fetched: {len(stints)}")

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

    # Pull pit stops (sprints may have none — handled gracefully)
    print("\n[ Pit Stops ]")
    pits = fetch("pit", {"session_key": SESSION_KEY})
    print(f"  Total pit stops: {len(pits)}")
    for p in sorted(pits, key=lambda x: (x["driver_number"], x["lap_number"])):
        driver = drivers_by_number.get(p["driver_number"], {})
        stop = f"{p['stop_duration']}s" if p.get("stop_duration") else "N/A"
        lane = p.get("pit_duration")
        print(f"  #{p['driver_number']:>2} {driver.get('name_acronym','?')} "
              f"lap {p['lap_number']:>3} — stop: {stop}  lane: {lane}s")

    # Bundle payload
    print("\n[ Bundling Payload ]")
    payload = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "session_type": SESSION_TYPE,
        "session": session,
        "drivers": drivers,
        "laps": laps,
        "stints": stints,
        "pits": pits,
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
    blob_name = f"f1/{RACE_NAME}/{blob_prefix}{timestamp}.json"

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