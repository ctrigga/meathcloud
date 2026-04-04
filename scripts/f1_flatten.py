import json
import sys
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request

def load_blob(filepath):
    with open(filepath) as f:
        return json.load(f)

def build_drivers_map(data):
    return {d["driver_number"]: d for d in data["drivers"]}

def fetch(endpoint, params=None):
    base_url = "https://api.openf1.org/v1"
    url = f"{base_url}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise

def derive_finishing_order(data, drivers_map):
    laps = data["laps"]

    laps_per_driver = defaultdict(int)
    last_lap_start = {}
    for lap in laps:
        n = lap["driver_number"]
        laps_per_driver[n] = max(laps_per_driver[n], lap["lap_number"])
        if lap.get("date_start"):
            last_lap_start[n] = lap["date_start"]

    for d in data["drivers"]:
        n = d["driver_number"]
        if n not in laps_per_driver:
            laps_per_driver[n] = 0

    ranked = sorted(
        laps_per_driver.keys(),
        key=lambda n: (-laps_per_driver[n], last_lap_start.get(n, ""))
    )

    results = []
    for pos, driver_num in enumerate(ranked, 1):
        d = drivers_map.get(driver_num, {})
        results.append({
            "position": pos,
            "driver_number": driver_num,
            "acronym": d.get("name_acronym", "???"),
            "full_name": d.get("full_name", "Unknown"),
            "team": d.get("team_name", "Unknown"),
            "laps_completed": laps_per_driver[driver_num],
        })

    return results

def get_fastest_lap(data, drivers_map):
    good_laps = [l for l in data["laps"] if l.get("lap_duration") is not None]
    if not good_laps:
        return None
    fastest = min(good_laps, key=lambda x: x["lap_duration"])
    d = drivers_map.get(fastest["driver_number"], {})
    return {
        "driver_number": fastest["driver_number"],
        "acronym": d.get("name_acronym", "???"),
        "full_name": d.get("full_name", "Unknown"),
        "team": d.get("team_name", "Unknown"),
        "lap_number": fastest["lap_number"],
        "lap_duration": fastest["lap_duration"],
        "lap_duration_formatted": f"{int(fastest['lap_duration'] // 60)}:{fastest['lap_duration'] % 60:06.3f}",
    }

def get_strategy(data, drivers_map):
    strategy = []
    for stint in sorted(data["stints"], key=lambda s: (s["driver_number"], s["stint_number"])):
        d = drivers_map.get(stint["driver_number"], {})
        strategy.append({
            "driver_number": stint["driver_number"],
            "acronym": d.get("name_acronym", "???"),
            "team": d.get("team_name", "Unknown"),
            "stint_number": stint["stint_number"],
            "lap_start": stint["lap_start"],
            "lap_end": stint["lap_end"],
            "compound": stint.get("compound", "UNKNOWN"),
            "tyre_age_at_start": stint.get("tyre_age_at_start", 0),
        })
    return strategy

def get_pit_stops(data, drivers_map):
    pits = data.get("pits")

    if not pits:
        session_key = data["session"]["session_key"]
        print(f"  Fetching pit data from OpenF1 (session_key={session_key})...")
        pits = fetch("pit", {"session_key": session_key})

    result = []
    for p in sorted(pits, key=lambda x: (x["driver_number"], x["lap_number"])):
        d = drivers_map.get(p["driver_number"], {})
        lane = p.get("pit_duration") or p.get("lane_duration")
        stop = p.get("stop_duration")
        abnormal = lane and lane > 60
        result.append({
            "driver_number": p["driver_number"],
            "acronym": d.get("name_acronym", "???"),
            "lap_number": p["lap_number"],
            "lane_duration": lane,
            "stop_duration": stop,
            "abnormal": abnormal,
        })
    return result

def get_weather_snapshot(data):
    samples = data["weather"]
    if not samples:
        return None
    first = samples[0]
    last = samples[-1]
    return {
        "start": {
            "air_temperature": first.get("air_temperature"),
            "track_temperature": first.get("track_temperature"),
            "humidity": first.get("humidity"),
            "rainfall": first.get("rainfall"),
        },
        "end": {
            "air_temperature": last.get("air_temperature"),
            "track_temperature": last.get("track_temperature"),
            "humidity": last.get("humidity"),
            "rainfall": last.get("rainfall"),
        }
    }

def update_race_index(summary, index_path="static/f1/index.json"):
    import os
    import unicodedata

    def slugify(text):
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text.lower().replace(' ', '_')

    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = []

    session_type = summary.get("session_type", "Race")
    slug_suffix = "_sprint" if session_type == "Sprint" else ""
    slug = f"{summary['race'].lower().replace(' ', '_')}_{summary['year']}{slug_suffix}"
    file_path = f"{summary['race'].lower().replace(' ', '_')}_{summary['year']}/{'sprint_summary' if session_type == 'Sprint' else 'summary'}.json"

    entry = {
        "race": summary["race"],
        "year": summary["year"],
        "circuit": summary["circuit"],
        "date": summary["date"],
        "session_type": session_type,
        "slug": slug,
        "file_path": file_path,
        "winner": summary["results"][0]["full_name"] if summary["results"] else "Unknown",
        "winner_team": summary["results"][0]["team"] if summary["results"] else "Unknown",
        "fastest_lap": summary["fastest_lap"]["lap_duration_formatted"] if summary["fastest_lap"] else None,
    }

    existing = next((i for i, r in enumerate(index) if r["slug"] == entry["slug"]), None)
    if existing is not None:
        index[existing] = entry
    else:
        index.append(entry)

    index.sort(key=lambda r: (r["date"], r.get("session_type", "Race")))

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Race index updated: {len(index)} session(s)")

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "/tmp/melbourne_2026.json"
    data = load_blob(filepath)
    drivers_map = build_drivers_map(data)

    session_type = data.get("session_type", "Race")
    results = derive_finishing_order(data, drivers_map)
    fastest_lap = get_fastest_lap(data, drivers_map)
    strategy = get_strategy(data, drivers_map)
    weather = get_weather_snapshot(data)
    pit_stops = get_pit_stops(data, drivers_map)

    summary = {
        "race": data["session"]["location"],
        "year": data["session"]["date_start"][:4],
        "circuit": data["session"]["circuit_short_name"],
        "date": data["session"]["date_start"][:10],
        "session_type": session_type,
        "results": results,
        "fastest_lap": fastest_lap,
        "strategy": strategy,
        "weather": weather,
        "pit_stops": pit_stops,
    }

    print(f"{'Sprint' if session_type == 'Sprint' else 'Race'}: {summary['race']} {summary['year']}")
    print(f"\n{'Pos':<5} {'Driver':<6} {'Name':<25} {'Team':<25} {'Laps'}")
    print("-" * 75)
    for r in results:
        fl = " *** FASTEST LAP" if fastest_lap and r["driver_number"] == fastest_lap["driver_number"] else ""
        print(f"{r['position']:<5} {r['acronym']:<6} {r['full_name']:<25} {r['team']:<25} {r['laps_completed']}{fl}")

    if fastest_lap:
        print(f"\nFastest Lap: {fastest_lap['lap_duration_formatted']} "
              f"by {fastest_lap['acronym']} on lap {fastest_lap['lap_number']}")
    if weather:
        print(f"\nWeather: {weather['start']['air_temperature']}°C air / "
              f"{weather['start']['track_temperature']}°C track at start")

    import os
    import unicodedata

    def slugify(text):
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text.lower().replace(' ', '_')

    slug_suffix = "_sprint" if session_type == "Sprint" else ""
    race_slug = f"{slugify(summary['race'])}_{summary['year']}"
    out_dir = f"static/f1/{race_slug}"
    os.makedirs(out_dir, exist_ok=True)
    out_filename = "sprint_summary.json" if session_type == "Sprint" else "summary.json"
    out_path = f"{out_dir}/{out_filename}"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    update_race_index(summary)
    print(f"\nSummary written to {out_path}")

if __name__ == "__main__":
    main()