---
title: "Day 5: Building an F1 Data Pipeline with OpenF1 and Azure"
date: 2026-03-09
draft: false
tags: ["azure", "python", "data-engineering", "f1", "github-actions"]
---

I'm an F1 fan. So when it came time to build out my data engineering portfolio, 
pointing a pipeline at Formula 1 telemetry data was a no-brainer.

## The Goal

Build an automated pipeline that ingests F1 race data into Azure Blob Storage 
after every Grand Prix — without me having to do anything. No manual triggers, 
no leaving my laptop on, no babysitting.

## The Data Source

[OpenF1](https://openf1.org) is a free, open-source API that provides real-time 
and historical F1 data — lap times, pit stops, telemetry, weather, driver info — 
all of it. No API key required for historical data. It's genuinely one of the 
nicest public APIs I've worked with.

For a proof of concept I pulled the 2025 Abu Dhabi Grand Prix — the 
championship decider where Lando Norris clinched his first title. The race 
session key is `9839` and the data includes 1,156 laps across 20 drivers, 
47 stints, and 154 weather samples. About 1MB of JSON per race.

## The ETL Script

`scripts/f1_etl.py` follows the same pattern as the weather pipeline from Day 4:

- **Extract** — hit the OpenF1 API across five endpoints: `sessions`, `drivers`, 
`laps`, `stints`, and `weather`
- **Transform** — light touches only: find the fastest lap, count pit stops per 
driver, validate session type
- **Load** — bundle everything into a single JSON payload and upload to 
`raw-data/f1/{race_name}/race_{timestamp}.json` in Azure Blob Storage

The script accepts `--session-key` and `--race-name` arguments so it can ingest 
any race, not just Abu Dhabi. Both args are required together or neither — 
passing one without the other exits with a clear error message.

A few defensive touches worth mentioning:

- **Session type guard** — if the session key resolves to a Sprint or Qualifying 
session the script aborts rather than silently ingesting the wrong data
- **404 handling** — the OpenF1 laps endpoint returns a 404 for sessions that 
haven't happened yet. The script catches this gracefully and continues with 
empty arrays rather than crashing
- **Argument validation** — `--session-key` and `--race-name` must be provided 
together, and race names are validated against a simple regex to keep blob paths 
clean
- **RBAC** — same lesson as Day 4. Deploying a storage account doesn't 
automatically grant your identity access to it. The `Storage Blob Data 
Contributor` role assignment is a separate step that catches people out

## The Smart Scheduler

This is the part I'm most proud of. Rather than hardcoding a cron time or 
manually triggering ingestion after each race, `scripts/f1_scheduler.py` 
figures it out automatically.

It fetches the full 2026 race calendar from OpenF1, calculates 
`race_start_time + 3.5 hours` for every session, and checks whether any 
trigger window falls within the current run. If it does, it fires the ETL 
with the correct session key and race name for that event.

The 3.5 hour offset accounts for a full race distance plus buffer for safety 
cars, red flags, or a chaotic Melbourne finish.

## GitHub Actions as the Orchestrator

The scheduler runs as a GitHub Actions workflow on a 5-minute cron. No Azure 
Data Factory pipelines, no Azure Functions, no always-on compute. Just a 
workflow file that already lives in my repo:
```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
```

Authentication to Azure uses a service principal stored as a GitHub Actions 
secret (`AZURE_CREDENTIALS`), created with the minimum required scope — 
`Storage Blob Data Contributor` on the data engineering resource group only.

## Lessons Learned: GitHub Actions Cron Is Not Precise

The first real test was the 2026 Australian Grand Prix. The race started at 
`04:00 UTC` and the scheduler was set to trigger at `07:30 UTC`. It missed.

The workflow run landed at `07:40 UTC` — 4 minutes late, just outside the 
original 6-minute trigger window. GitHub Actions cron on the free tier can 
be anywhere from 1 to 15 minutes late depending on runner availability.

The fix was simple — widen `TRIGGER_WINDOW_MINUTES` from `6` to `20`, giving 
a 40-minute window total. Wide enough to absorb any runner delay, narrow enough 
that two back-to-back races could never accidentally overlap.

Melbourne data was recovered manually by running the ETL directly:
```bash
python scripts/f1_etl.py --session-key 11234 --race-name melbourne_2026
```

## First Race of the 2026 Era

The Melbourne data tells an interesting story about the new season. 22 drivers 
on the grid — Cadillac made their debut with Sergio Perez (#11) and Valtteri 
Bottas (#77), and Sauber completed their transition to Audi. Verstappen set the 
fastest lap at 82.091s. Stroll somehow managed 4 pit stops. Hadjar and 
Hulkenberg both recorded 0 stints suggesting early retirements.

Both races are now sitting in blob storage:
```
raw-data/f1/abu_dhabi_2025/race_2026-03-08_00-48-11.json   1,055,018 bytes
raw-data/f1/melbourne_2026/race_2026-03-09_01-40-40.json     921,658 bytes
```

## What's Next

The raw JSON landing in blob storage is just the start. Next steps:

- Parse and flatten the lap time data into a format suitable for analysis
- Build a simple visualization on meath.cloud showing race pace and strategy
- Explore Azure Data Factory for more complex transformation pipelines

The data engineering foundation is in place. Time to do something interesting 
with the data.