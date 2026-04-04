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

def blob_exists(prefix):
    result = subprocess.run([
        "az", "storage", "blob", "list",
        "--account-name", "stmeathclouddev",
        "--container-name", "raw-data",
        "--prefix", prefix,
        "--auth-mode", "login",
        "--query", "[0].name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    return bool(result.stdout.strip())

def get_blob_name(prefix):
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

def ingest_session(s, full_slug, session_type, year):
    blob_prefix = f"f1/{slugify(s['location'])}_{year}/{'sprint_' if session_type == 'Sprint' else 'race_'}"
    label = f"{s['location']} {year} ({session_type})"

    print(f"\n── {label} ──────────────────────────────────────")

    # ETL
    print(f"   Fetching from OpenF1 (session_key={s['session_key']})...")
    result = subprocess.run([
        sys.executable, f"{REPO_DIR}/scripts/f1_etl.py",
        "--session-key", str(s["session_key"]),
        "--race-name", full_slug,
        "--session-type", session_type
    ], capture_output=True, text=True, cwd=REPO_DIR)

    if result.returncode != 0:
        print(f"   ✗ ETL failed:\n{result.stderr.strip()}")
        return False

    print(f"   ✓ ETL complete")

    # Wait for blob
    print(f"   Waiting for blob...")
    time.sleep(10)
    blob_name = get_blob_name(blob_prefix)
    if not blob_name:
        print(f"   ✗ Blob not found after ETL, skipping flatten")
        return False

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
        return False

    # Flatten
    print(f"   Flattening...")
    flatten = subprocess.run([
        sys.executable, f"{REPO_DIR}/scripts/f1_flatten.py", tmp
    ], capture_output=True, text=True, cwd=REPO_DIR)

    if flatten.returncode != 0:
        print(f"   ✗ Flatten failed:\n{flatten.stderr.strip()}")
        return False

    print(f"   ✓ Done")
    return True

def main():
    now = datetime.now(timezone.utc)
    year = now.year

    print(f"\n🏎  F1 Sync — {year}")
    print(f"   {now.strftime('%Y-%m-%d %H:%M')} UTC\n")

    # Fetch both session types
    race_sessions = fetch("sessions", {"year": year, "session_name": "Race"})
    sprint_sessions = fetch("sessions", {"year": year, "session_name": "Sprint"})

    all_sessions = (
        [(s, "Race") for s in race_sessions] +
        [(s, "Sprint") for s in sprint_sessions]
    )
    all_sessions.sort(key=lambda x: x[0]["date_start"])

    completed = [
        (s, t) for s, t in all_sessions
        if datetime.fromisoformat(s["date_end"]) + timedelta(minutes=POST_RACE_BUFFER_MINUTES) < now
    ]

    print(f"   {len(completed)} completed session(s) found\n")

    missing = []
    for s, session_type in completed:
        slug = slugify(s["location"])
        slug_suffix = "_sprint" if session_type == "Sprint" else ""
        full_slug = f"{slug}_{year}{slug_suffix}"
        blob_prefix = f"f1/{slug}_{year}/{'sprint_' if session_type == 'Sprint' else 'race_'}"

        if not blob_exists(blob_prefix):
            missing.append((s, full_slug, session_type))

    if not missing:
        print("   ✓ All sessions already ingested. Nothing to do.\n")
        sys.exit(0)

    print(f"   {len(missing)} session(s) need ingesting:\n")
    for s, full_slug, session_type in missing:
        print(f"   • {s['location']} {year} ({session_type})")

    print()

    ingested = []
    failed = []

    for i, (s, full_slug, session_type) in enumerate(missing, 1):
        year_str = s["date_start"][:4]
        success = ingest_session(s, full_slug, session_type, year_str)
        if success:
            ingested.append(full_slug)
        else:
            failed.append(full_slug)
        time.sleep(5)

    # Summary
    print("\n══════════════════════════════════════════")
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