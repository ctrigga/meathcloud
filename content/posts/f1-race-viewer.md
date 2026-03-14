---
title: "Day 6: Building an F1 Race Viewer with Azure and Hugo"
date: 2026-03-14
draft: false
tags: ["azure", "python", "data-engineering", "f1", "hugo", "javascript"]
---

With the F1 data pipeline running automatically after every race, the next step 
was making the data actually useful — turning raw JSON in blob storage into 
something you'd actually want to look at.

## What We Built

The [F1 page](/f1/) on this site shows:

- Full race results with finishing positions
- Fastest lap indicator per race
- Tyre strategy visualization for every driver
- Pit stop times on hover
- A race selector covering the full 2025 season and 2026 onwards

All of it updates automatically after each race with zero manual intervention.

## The Flatten Pipeline

Raw race data from OpenF1 comes in at around 1MB per race — 1,000+ lap records, 
telemetry, weather samples. That's too heavy to serve directly to a browser. 

`scripts/f1_flatten.py` sits between the raw blob storage and the site. It 
reads the raw JSON, derives what the frontend actually needs, and writes a 
lean summary JSON to `static/f1/{race_name}/summary.json`. Melbourne 2026 
goes from 921KB raw down to a much more manageable summary.

Key derivations:
- **Finishing order** — OpenF1 doesn't give you a explicit results table. 
We sort by max lap number completed, then by timestamp of the last lap to 
break ties for drivers on the same lap count
- **Fastest lap** — simple min on `lap_duration` across all completed laps
- **Pit stop data** — fetched live from the OpenF1 pit endpoint using the 
session key stored in the blob, so older ingested races don't need 
re-ingestion to get pit times

## The Race Index

`static/f1/index.json` is a lightweight manifest of all available races — 
winner, fastest lap, date, and slug. The frontend loads this first to build 
the race selector dropdown, then fetches the full summary only when a race 
is selected. Keeps the initial page load fast.

## Tyre Strategy Visualization

Each driver gets a horizontal bar broken into stints, color coded by compound:

- 🔴 Soft
- 🟡 Medium  
- ⚪ Hard
- 🟢 Intermediate
- 🔵 Wet

Stint dividers are marked with a dark border so same-compound back-to-back 
stints are visually distinct. Hovering over any stint shows the compound, 
lap range, and pit stop time for that stop — including flagging abnormal 
stops caused by red flags or VSC periods.

## Backfilling the 2025 Season

The pipeline was built mid-season so we needed to backfill all 24 races from 
the 2025 championship. `scripts/f1_backfill.py` loops through the OpenF1 
race calendar, runs the ETL for each session, and skips any races already 
in blob storage.

Lesson learned: OpenF1 rate limits aggressive requests. A 15 second sleep 
between races keeps things polite and avoids 429 errors.

## Mobile Friendly Pit Stop Details

The tyre strategy bars are interactive on both desktop and mobile. On desktop, 
hovering over any stint bar shows a tooltip with the compound, lap range, and 
pit stop time. On mobile where hover doesn't exist, tapping a bar shows the 
same information in a popup below the strategy chart. Tap the same bar again 
to dismiss it.

Pit stop times come from the OpenF1 pit endpoint and show both the total lane 
duration (full time in the pit lane) and the stationary stop duration where 
available. Abnormal stops caused by red flags or VSC periods are flagged 
automatically — anything over 60 seconds is marked as abnormal.

## What's Next

The raw lap time data sitting in blob storage opens up some interesting 
possibilities — race pace comparisons between drivers, sector time analysis, 
championship points progression over the season. That's the next frontier 
for the data engineering side of this project.

For now though, the viewer does exactly what it needs to do. Check it out 
at [meath.cloud/f1](/f1/).