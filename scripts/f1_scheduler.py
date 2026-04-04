import json
import sys
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.openf1.org/v1"
POST_RACE_BUFFER_MINUTES = 30  # wait this long after date_end before ingesting

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

def blob_exists(slug):
    """Returns True if a blob already exists for this race slug in stmeathclouddev."""
    result = subprocess.run([
        "az", "storage", "blob", "list",
        "--account-name", "stmeathclouddev",
        "--container-name", "raw-data",
        "--prefix", f"f1/{slug}/",
        "--auth-mode", "login",
        "--query", "[0].name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    return bool(result.stdout.strip())

def main():
    now = datetime.now(timezone.utc)
    print(f"=== F1 Scheduler ===")
    print(f"Current time (UTC): {now.isoformat()}\n")

    sessions = fetch("sessions", {"year": now.year, "session_type": "Race"})
    races = [s for s in sessions if s["session_name"] == "Race"]
    races.sort(key=lambda s: s["date_start"])

    print(f"Found {len(races)} races\n")
    print(f"{'Race':<30} {'End (UTC)':<30} {'Status'}")
    print("-" * 80)

    to_ingest = []

    for s in races:
        slug = slugify(s["location"])
        race_year = s["date_start"][:4]
        full_slug = f"{slug}_{race_year}"

        date_end = datetime.fromisoformat(s["date_end"])
        ingest_after = date_end + timedelta(minutes=POST_RACE_BUFFER_MINUTES)

        if now < ingest_after:
            status = "upcoming / in progress"
        else:
            exists = blob_exists(full_slug)
            if exists:
                status = "already ingested"
            else:
                status = ">>> NEEDS INGEST <<<"
                to_ingest.append((s, full_slug))

        print(f"{s['location']:<30} {s['date_end']:<30} {status}")

    if not to_ingest:
        print("\nNothing to ingest. Exiting.")
        sys.exit(0)

    for s, full_slug in to_ingest:
        print(f"\nIngesting: {s['location']} {race_year} (session_key={s['session_key']}, slug={full_slug})")
        subprocess.run([
            sys.executable, "scripts/f1_etl.py",
            "--session-key", str(s["session_key"]),
            "--race-name", full_slug
        ], check=True)

if __name__ == "__main__":
    main()