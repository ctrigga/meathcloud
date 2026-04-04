import json
import sys
import subprocess
import time
import urllib.request
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.openf1.org/v1"
REPO_DIR = "/Users/dmeath/meathcloud"
POST_RACE_BUFFER_MINUTES = 30

def fetch(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))

def slugify(location):
    import unicodedata
    text = unicodedata.normalize("NFKD", location)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().replace(" ", "_")

def blob_exists(full_slug):
    result = subprocess.run([
        "az", "storage", "blob", "list",
        "--account-name", "stmeathclouddev",
        "--container-name", "raw-data",
        "--prefix", f"f1/{full_slug}/",
        "--auth-mode", "login",
        "--query", "[0].name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    return bool(result.stdout.strip())

def get_blob_name(full_slug):
    result = subprocess.run([
        "az", "storage", "blob", "list",
        "--account-name", "stmeathclouddev",
        "--container-name", "raw-data",
        "--prefix", f"f1/{full_slug}/",
        "--auth-mode", "login",
        "--query", "[0].name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    return result.stdout.strip()

def main():
    now = datetime.now(timezone.utc)
    year = now.year

    print(f"\n🏎  F1 Sync — {year}")
    print(f"   {now.strftime('%Y-%m-%d %H:%M')} UTC\n")

    sessions = fetch("sessions", {"year": year, "session_type": "Race"})
    races = [s for s in sessions if s["session_name"] == "Race"]
    races.sort(key=lambda s: s["date_start"])

    completed = [
        s for s in races
        if datetime.fromisoformat(s["date_end"]) + timedelta(minutes=POST_RACE_BUFFER_MINUTES) < now
    ]

    print(f"   {len(completed)} completed race(s) found\n")

    missing = []
    for s in completed:
        slug = slugify(s["location"])
        full_slug = f"{slug}_{year}"
        if not blob_exists(full_slug):
            missing.append((s, full_slug))

    if not missing:
        print("   ✓ All races already ingested. Nothing to do.\n")
        sys.exit(0)

    print(f"   {len(missing)} race(s) need ingesting:\n")
    for s, full_slug in missing:
        print(f"   • {s['location']} ({full_slug})")

    print()

    ingested = []
    failed = []

    for i, (s, full_slug) in enumerate(missing, 1):
        print(f"── [{i}/{len(missing)}] {s['location']} ──────────────────────────")

        # ETL
        print(f"   Fetching from OpenF1 (session_key={s['session_key']})...")
        result = subprocess.run([
            sys.executable, f"{REPO_DIR}/scripts/f1_etl.py",
            "--session-key", str(s["session_key"]),
            "--race-name", full_slug
        ], capture_output=True, text=True, cwd=REPO_DIR)

        if result.returncode != 0:
            print(f"   ✗ ETL failed:\n{result.stderr.strip()}")
            failed.append(full_slug)
            continue

        print(f"   ✓ ETL complete")

        # Wait for blob
        print(f"   Waiting for blob...")
        time.sleep(10)
        blob_name = get_blob_name(full_slug)
        if not blob_name:
            print(f"   ✗ Blob not found after ETL, skipping flatten")
            failed.append(full_slug)
            continue

        # Download
        tmp = f"/tmp/{full_slug}.json"
        dl = subprocess.run([
            "az", "storage", "blob", "download",
            "--account-name", "stmeathclouddev",
            "--container-name", "raw-data",
            "--name", blob_name,
            "--file", tmp,
            "--auth-mode", "login"
        ], capture_output=True, text=True)

        if dl.returncode != 0:
            print(f"   ✗ Download failed")
            failed.append(full_slug)
            continue

        # Flatten
        print(f"   Flattening...")
        flatten = subprocess.run([
            sys.executable, f"{REPO_DIR}/scripts/f1_flatten.py", tmp
        ], capture_output=True, text=True, cwd=REPO_DIR)

        if flatten.returncode != 0:
            print(f"   ✗ Flatten failed:\n{flatten.stderr.strip()}")
            failed.append(full_slug)
            continue

        print(f"   ✓ Done\n")
        ingested.append(full_slug)
        time.sleep(5)

    # Summary
    print("══════════════════════════════════════════")
    print(f"   ✓ Ingested : {len(ingested)}")
    if failed:
        print(f"   ✗ Failed   : {len(failed)}  ({', '.join(failed)})")

    # Commit if anything changed
    if ingested:
        print("\n   Committing to git...")
        subprocess.run(["git", "add", "static/f1/"], cwd=REPO_DIR)
        msg = f"sync: ingest {', '.join(ingested)}"
        subprocess.run(["git", "commit", "-m", msg], cwd=REPO_DIR)
        subprocess.run(["git", "push"], cwd=REPO_DIR)
        print("   ✓ Pushed\n")

if __name__ == "__main__":
    main()