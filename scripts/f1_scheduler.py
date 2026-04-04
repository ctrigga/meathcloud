import json
import sys
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.openf1.org/v1"
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

def main():
    now = datetime.now(timezone.utc)
    print(f"=== F1 Scheduler ===")
    print(f"Current time (UTC): {now.isoformat()}\n")

    # Fetch both Race and Sprint sessions
    race_sessions = fetch("sessions", {"year": now.year, "session_name": "Race"})
    sprint_sessions = fetch("sessions", {"year": now.year, "session_name": "Sprint"})

    all_sessions = (
        [(s, "Race") for s in race_sessions] +
        [(s, "Sprint") for s in sprint_sessions]
    )
    all_sessions.sort(key=lambda x: x[0]["date_start"])

    print(f"Found {len(race_sessions)} race(s), {len(sprint_sessions)} sprint(s)\n")
    print(f"{'Session':<35} {'End (UTC)':<30} {'Status'}")
    print("-" * 85)

    to_ingest = []

    for s, session_type in all_sessions:
        slug = slugify(s["location"])
        year = s["date_start"][:4]
        slug_suffix = "_sprint" if session_type == "Sprint" else ""
        full_slug = f"{slug}_{year}{slug_suffix}"
        blob_prefix = f"f1/{slug}_{year}/{'sprint_' if session_type == 'Sprint' else 'race_'}"

        date_end = datetime.fromisoformat(s["date_end"])
        ingest_after = date_end + timedelta(minutes=POST_RACE_BUFFER_MINUTES)

        label = f"{s['location']} {year} ({session_type})"

        if now < ingest_after:
            status = "upcoming / in progress"
        else:
            exists = blob_exists(blob_prefix)
            if exists:
                status = "already ingested"
            else:
                status = ">>> NEEDS INGEST <<<"
                to_ingest.append((s, full_slug, session_type))

        print(f"{label:<35} {s['date_end']:<30} {status}")

    if not to_ingest:
        print("\nNothing to ingest. Exiting.")
        sys.exit(0)

    for s, full_slug, session_type in to_ingest:
        year = s["date_start"][:4]
        print(f"\nIngesting: {s['location']} {year} {session_type} "
              f"(session_key={s['session_key']}, slug={full_slug})")
        subprocess.run([
            sys.executable, "scripts/f1_etl.py",
            "--session-key", str(s["session_key"]),
            "--race-name", full_slug,
            "--session-type", session_type
        ], check=True)

if __name__ == "__main__":
    main()