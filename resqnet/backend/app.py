import sqlite3
import math
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = "resqnet.db"

TYPE_WEIGHTS = {
    "Trapped / Structural Collapse": 15,
    "Medical Emergency": 12,
    "Flash Flood / Rising Water": 10,
    "Landslide": 10,
    "Fire / Hazard": 8,
    "Food / Water Shortage": 4,
    "Other": 2
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sos_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            victim_name TEXT,
            phone TEXT,
            emergency_type TEXT NOT NULL,
            people_count INTEGER DEFAULT 1,
            children_count INTEGER DEFAULT 0,
            injured_count INTEGER DEFAULT 0,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            duplicate_of INTEGER DEFAULT NULL,
            merged INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def compute_urgency(row, now_dt):
    created_dt = datetime.fromisoformat(row["created_at"])
    minutes_waiting = max(0, int((now_dt - created_dt).total_seconds() // 60))
    type_weight = TYPE_WEIGHTS.get(row["emergency_type"], 5)
    score = (3 * row["children_count"]) + (2 * row["injured_count"]) + type_weight + minutes_waiting
    return score, minutes_waiting, type_weight

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/sos")
def victim_app():
    return render_template("victim.html")

@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({"status": "online", "network": "RESQNET_HOTSPOT", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/sos", methods=["POST"])
def receive_sos():
    data = request.get_json(force=True)
    client_id = data.get("client_id", "")
    victim_name = data.get("victim_name", "Anonymous").strip() or "Anonymous"
    phone = data.get("phone", "N/A").strip() or "N/A"
    emergency_type = data.get("emergency_type", "Flood / Rising Water")
    people_count = max(1, int(data.get("people_count", 1)))
    children_count = max(0, int(data.get("children_count", 0)))
    injured_count = max(0, int(data.get("injured_count", 0)))
    latitude = float(data.get("latitude", 13.0210))
    longitude = float(data.get("longitude", 74.9850))
    notes = data.get("notes", "").strip()
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    cursor = conn.cursor()

    # Check if exact client_id already received (idempotency for retries)
    if client_id:
        cursor.execute("SELECT id FROM sos_requests WHERE client_id = ?", (client_id,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({"status": "confirmed", "sos_id": existing["id"], "duplicate_of": None, "message": "Already recorded"}), 200

    # Check for likely spatial & type duplicate within ~50 meters among active requests
    cursor.execute("SELECT id, latitude, longitude, emergency_type FROM sos_requests WHERE merged = 0 AND status != 'Rescued'")
    active_cases = cursor.fetchall()
    duplicate_of = None
    for case in active_cases:
        dist = haversine_meters(latitude, longitude, case["latitude"], case["longitude"])
        if dist <= 50.0:
            duplicate_of = case["id"]
            break

    cursor.execute('''
        INSERT INTO sos_requests (
            client_id, victim_name, phone, emergency_type,
            people_count, children_count, injured_count,
            latitude, longitude, notes, status, created_at, duplicate_of
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    ''', (
        client_id, victim_name, phone, emergency_type,
        people_count, children_count, injured_count,
        latitude, longitude, notes, created_at, duplicate_of
    ))
    sos_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "confirmed",
        "sos_id": sos_id,
        "duplicate_of": duplicate_of,
        "received_at": created_at,
        "message": f"SOS #{sos_id} confirmed by Rescue Command Server"
    }), 201

@app.route("/api/cases", methods=["GET"])
def list_cases():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sos_requests WHERE merged = 0")
    rows = cursor.fetchall()
    conn.close()

    now_dt = datetime.now(timezone.utc)
    cases = []
    for r in rows:
        score, mins, tw = compute_urgency(r, now_dt)
        cases.append({
            "id": r["id"],
            "client_id": r["client_id"],
            "victim_name": r["victim_name"],
            "phone": r["phone"],
            "emergency_type": r["emergency_type"],
            "people_count": r["people_count"],
            "children_count": r["children_count"],
            "injured_count": r["injured_count"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "notes": r["notes"],
            "status": r["status"],
            "created_at": r["created_at"],
            "duplicate_of": r["duplicate_of"],
            "minutes_waiting": mins,
            "type_weight": tw,
            "urgency_score": score
        })

    # Rank active cases first by urgency_score DESC, then Rescued at bottom
    status_order = {"Pending": 0, "Dispatched": 1, "Rescued": 2}
    cases.sort(key=lambda x: (status_order.get(x["status"], 9), -x["urgency_score"]))
    return jsonify({"cases": cases, "server_time": now_dt.isoformat()})

@app.route("/api/cases/<int:sos_id>/status", methods=["POST"])
def update_status(sos_id):
    data = request.get_json(force=True)
    new_status = data.get("status", "Pending")
    if new_status not in ("Pending", "Dispatched", "Rescued"):
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db()
    conn.execute("UPDATE sos_requests SET status = ? WHERE id = ?", (new_status, sos_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated", "id": sos_id, "new_status": new_status})

@app.route("/api/cases/<int:sos_id>/merge", methods=["POST"])
def merge_duplicate(sos_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sos_requests WHERE id = ?", (sos_id,))
    dup = cursor.fetchone()
    if not dup or not dup["duplicate_of"]:
        conn.close()
        return jsonify({"error": "No target case to merge into"}), 400

    parent_id = dup["duplicate_of"]
    cursor.execute("SELECT * FROM sos_requests WHERE id = ?", (parent_id,))
    parent = cursor.fetchone()
    if parent:
        merged_people = max(parent["people_count"], dup["people_count"])
        merged_children = max(parent["children_count"], dup["children_count"])
        merged_injured = max(parent["injured_count"], dup["injured_count"])
        merged_notes = (parent["notes"] + f" | [Merged SOS #{sos_id} from {dup['victim_name']}: {dup['notes']}]").strip(" |")
        cursor.execute('''
            UPDATE sos_requests
            SET people_count = ?, children_count = ?, injured_count = ?, notes = ?
            WHERE id = ?
        ''', (merged_people, merged_children, merged_injured, merged_notes, parent_id))

    cursor.execute("UPDATE sos_requests SET merged = 1 WHERE id = ?", (sos_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "merged", "merged_id": sos_id, "into_id": parent_id})

@app.route("/api/seed_demo", methods=["POST"])
def seed_demo():
    conn = get_db()
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).timestamp()
    demo_entries = [
        ("DEMO-1", "Ramesh Naik", "9448011223", "Trapped / Structural Collapse", 6, 2, 3, 13.1830, 74.9340, "Roof collapsed near temple road, water rising fast", "Pending", datetime.fromtimestamp(now_ts - 900, tz=timezone.utc).isoformat(), None),
        ("DEMO-2", "Meera Shenoy", "9845122334", "Medical Emergency", 3, 1, 2, 13.1865, 74.9392, "Elderly diabetic patient & infant stranded on 1st floor", "Pending", datetime.fromtimestamp(now_ts - 480, tz=timezone.utc).isoformat(), None),
        ("DEMO-3", "Abdul Razak", "9900112233", "Flash Flood / Rising Water", 4, 0, 0, 13.1832, 74.9341, "Same house cluster near temple road, need boat urgently", "Pending", datetime.fromtimestamp(now_ts - 300, tz=timezone.utc).isoformat(), 1),
        ("DEMO-4", "Kiran Poojary", "9741234567", "Food / Water Shortage", 8, 2, 0, 13.1910, 74.9420, "Community hall shelter out of drinking water", "Dispatched", datetime.fromtimestamp(now_ts - 1500, tz=timezone.utc).isoformat(), None)
    ]
    for entry in demo_entries:
        cursor.execute('''
            INSERT INTO sos_requests (
                client_id, victim_name, phone, emergency_type,
                people_count, children_count, injured_count,
                latitude, longitude, notes, status, created_at, duplicate_of
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', entry)
    conn.commit()
    conn.close()
    return jsonify({"status": "seeded", "count": len(demo_entries)})

@app.route("/api/reset", methods=["POST"])
def reset_db():
    conn = get_db()
    conn.execute("DELETE FROM sos_requests")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='sos_requests'")
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    init_db()
    print("=====================================================")
    print(" RESQNET: OFFLINE SOS NETWORK SERVER")
    print(" Command Center Dashboard : http://127.0.0.1:5000/")
    print(" Mobile Victim SOS App    : http://127.0.0.1:5000/sos")
    print("=====================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
