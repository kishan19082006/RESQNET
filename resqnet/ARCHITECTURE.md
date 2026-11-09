# RESQNET Technical Architecture & API Specification

## 1. System Data Flow
1. **Victim Phone (Android Kotlin / Mobile PWA)**:
   - Captures `Emergency Type`, `Total People`, `Children Count`, `Injured Count`, `Offline GPS Coordinates (Lat/Lon)`, and `Notes`.
   - Saves packet into local persistent storage (`SharedPreferences` on Android / `localStorage` on PWA) with a unique idempotent `client_id`.
2. **Local Wi-Fi Hotspot Link (~100m Range)**:
   - Operates completely without mobile data or internet.
   - Phone background listener detects the rescue team's laptop hotspot and flushes queued packets via HTTP POST.
3. **Rescue Server (Python Flask + SQLite)**:
   - Computes dynamic urgency score:
     `Score = (3 * Children) + (2 * Injured) + TypeWeight + MinutesWaiting`
   - Runs Haversine spatial clustering (`<= 50 meters`) to flag likely duplicate SOS calls from the same house/building.
4. **Command Center Dashboard**:
   - Displays ranked SOS queue, offline Canvas tactical radar plot, duplicate merge controls, and `Pending -> Dispatched -> Rescued` state transitions.

## 2. REST API Endpoints
- `GET /api/ping` : Hotspot reachability heartbeat.
- `POST /api/sos` : Submit or sync a queued SOS packet; returns `201 Created` confirmation receipt with `sos_id`.
- `GET /api/cases` : Returns all non-merged cases sorted by status and descending `urgency_score`.
- `POST /api/cases/<id>/status` : Updates status (`Pending`, `Dispatched`, `Rescued`).
- `POST /api/cases/<id>/merge` : Merges a flagged duplicate into its parent case.
