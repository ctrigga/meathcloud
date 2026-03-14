import json
import subprocess
import sys
import urllib.request
import time

BASE_URL = "https://api.openf1.org/v1"

def fetch(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))

def slugify(location, year):
    return f"{location.lower().replace(' ', '_').replace('é', 'e').replace('ã', 'a')}_{year}"

def az_blob_list(prefix):
    result = subprocess.run([
        "az", "storage", "blob", "list",
        "--account-name", "stmeathclouddev",
        "--container-name", "raw-data",
        "--prefix", prefix,
        "--auth-mode", "login",
        "--query", "[0].name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    return result.stdout.strip()

def main():
    year = sys.argv[1] if len(sys.argv) > 1 else "2025"
    print(f"=== F1 Backfill {year} ===\n")

    sessions = fetch("sessions", {"year": year, "session_type": "Race"})
    races = [s for s in sessions if s["session_name"] == "Race"]
    races.sort(key=lambda s: s["date_start"])

    print(f"Found {len(races)} races to backfill\n")

    for i, s in enumerate(races, 1):
        slug = slugify(s["location"], year)
        print(f"[{i}/{len(races)}] {s['location']} (session_key={s['session_key']}) → {slug}")

        # Check if already ingested
        blob_name = az_blob_list(f"f1/{slug}/")
        if blob_name:
            print(f"  Already ingested, skipping")
            continue

        # Run ETL
        result = subprocess.run([
            sys.executable, "scripts/f1_etl.py",
            "--session-key", str(s["session_key"]),
            "--race-name", slug
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ETL FAILED: {result.stderr.strip()}")
            continue

        # Wait for blob to appear
        time.sleep(15)
        blob_name = az_blob_list(f"f1/{slug}/")
        if not blob_name:
            print(f"  No blob found for {slug}, skipping flatten")
            continue

        # Download blob
        tmp = f"/tmp/{slug}.json"
        subprocess.run([
            "az", "storage", "blob", "download",
            "--account-name", "stmeathclouddev",
            "--container-name", "raw-data",
            "--name", blob_name,
            "--file", tmp,
            "--auth-mode", "login"
        ], capture_output=True, text=True)

        # Flatten
        flatten = subprocess.run([
            sys.executable, "scripts/f1_flatten.py", tmp
        ], capture_output=True, text=True)

        if flatten.returncode != 0:
            print(f"  FLATTEN FAILED: {flatten.stderr.strip()}")
        else:
            print(f"  Done")

        time.sleep(15)  # pause between races

    print(f"\nBackfill complete.")

if __name__ == "__main__":
    main()
