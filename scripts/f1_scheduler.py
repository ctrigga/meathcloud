import json
import sys
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.openf1.org/v1"
TRIGGER_OFFSET_HOURS = 3.5
TRIGGER_WINDOW_MINUTES = 20  # matches cron frequency + buffer

def fetch(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    now = datetime.now(timezone.utc)
    print(f"=== F1 Scheduler ===")
    print(f"Current time (UTC): {now.isoformat()}\n")

    # Fetch all 2026 race sessions
    print("Fetching 2026 race calendar...")
    sessions = fetch("sessions", {"year": 2026, "session_type": "Race"})
    sessions.sort(key=lambda s: s["date_start"])

    print(f"Found {len(sessions)} races\n")
    print(f"{'Race':<30} {'Start (UTC)':<30} {'Trigger (UTC)':<30} Status")
    print("-" * 105)

    next_trigger = None

    for s in sessions:
        race_start = datetime.fromisoformat(s["date_start"])
        trigger_time = race_start + timedelta(hours=TRIGGER_OFFSET_HOURS)
        window_start = trigger_time - timedelta(minutes=TRIGGER_WINDOW_MINUTES)
        window_end = trigger_time + timedelta(minutes=TRIGGER_WINDOW_MINUTES)

        if now < race_start:
            status = "upcoming"
        elif window_start <= now <= window_end:
            status = ">>> TRIGGER NOW <<<"
            next_trigger = s
        elif now > trigger_time:
            status = "past"
        else:
            status = "race in progress"

        print(f"{s['location']:<30} {s['date_start']:<30} {trigger_time.isoformat():<30} {status}")

    # Fire ETL if trigger window hit
    if next_trigger:
        print(f"\nTriggering ETL for {next_trigger['location']} "
              f"(session_key={next_trigger['session_key']})")
        subprocess.run([
            sys.executable, "scripts/f1_etl.py",
            "--session-key", str(next_trigger["session_key"]),
            "--race-name", next_trigger["location"]
        ], check=True)
    else:
        print("\nNo trigger due. Exiting.")

if __name__ == "__main__":
    main()