# RESQNET: Offline SOS Network (Disaster Resilience - PS2)

Complete working prototype for **CODE FOR INNOVEX '26** matching the architecture and 5-step Live Demo Plan in your presentation.

---

## What's Included in This ZIP
1. **`app.py` (Python Flask + SQLite Server)**:
   - Stores incoming SOS packets in `resqnet.db` (zero internet required).
   - Calculates your exact urgency formula:
     `Urgency Score = (3 × Children) + (2 × Injured) + Type Weight + Minutes Waiting`
   - Automatically flags likely duplicate reports within ~50 meters and allows one-click merging.
   - Tracks case status across `Pending` → `Dispatched` → `Rescued`.
2. **`templates/dashboard.html` (Rescue Team Command Center Dashboard)**:
   - Live auto-updating ranked table of SOS cases, urgency score breakdown, duplicate merge button, status controls, and an offline tactical GPS radar plot.
3. **`templates/victim.html` (Offline-First Mobile Victim App / PWA)**:
   - Runs directly on any Android phone browser connected to your laptop's Wi-Fi hotspot (`http://<LAPTOP_IP>:5000/sos`).
   - Features an **Offline Packet Queue (`localStorage`)**, GPS coordinate capture, an **Out-of-Range Simulator Toggle** for effortless stage demos, and real-time delivery receipts (`✓ CONFIRMED #ID`).
4. **`android_kotlin_reference/ResqNetOfflineManager.kt`**:
   - Native Android Kotlin source module implementing `ConnectivityManager.NetworkCallback` hotspot detection and offline JSON packet queueing.

---

## Quick Start (Run in 60 Seconds)

1. **Install Flask**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the Rescue Server on your Laptop**:
   ```bash
   python app.py
   ```
3. **Open the Command Dashboard on Laptop**:
   - Visit: `http://127.0.0.1:5000/`
   - Click **"Load Demo Cases"** to immediately see ranked cases and duplicate detection in action.

---

## How to Run the 5-Step Live Demo Plan (Slide 06)

1. **Turn on your Laptop's Local Wi-Fi Hotspot** (or connect both Laptop and Android Phone to the same offline phone hotspot with mobile data switched OFF).
2. Find your laptop's local IP address:
   - Windows: Run `ipconfig` in Command Prompt (look for IPv4 Address, e.g., `192.168.137.1` or `192.168.43.xxx`).
   - Mac/Linux: Run `ifconfig` or `ip a`.
3. **Open the Victim App on your Android Phone**:
   - Open Chrome on your phone and go to `http://<YOUR_LAPTOP_IP>:5000/sos`
4. **Execute the Demo Steps in front of the Judges**:
   - **Step 1 & 2**: Show mobile data is OFF and the phone is linked to the local hotspot (`HOTSPOT LINKED` green badge).
   - **Step 3**: Fill in an emergency type, children count, injured count, and tap **Get GPS** → **SEND EMERGENCY SOS**. Show the instant `✓ CONFIRMED` receipt on the phone and the ranked row appearing on the laptop dashboard.
   - **Step 4 (Queue & Reconnect)**: Flip the **"Demo Step 4: Simulate Out-of-Range"** toggle at the top of the phone screen (or walk out of Wi-Fi range). Submit another SOS—it displays `⏳ QUEUED` locally on the phone. Flip the toggle back (or reconnect to Wi-Fi) and watch it automatically sync and switch to `✓ CONFIRMED`!
   - **Step 5 (Rank, Merge & Dispatch)**: On the laptop dashboard, show the urgency score calculation, merge any flagged nearby duplicate, and click **Dispatch** → **Mark Rescued**.


---

## Repository Directory Structure (For GitHub Judges)
```text
resqnet/
├── backend/
│   ├── app.py                      # Flask app and REST API routes
│   ├── database.py                 # SQLite initialization and queries
│   ├── scoring.py                  # Urgency score clustering logic
│   ├── requirements.txt            # Python dependencies (Flask, etc.)
│   └── tests/
│       └── test_resqnet.py         # Pytest suite for backend endpoints
├── android/
│   ├── build.gradle                # Gradle build and dependency config
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml # Permissions for GPS and Wi-Fi
│           ├── java/com/resqnet/
│           │   ├── MainActivity.kt
│           │   └── ResqNetOfflineManager.kt
│           └── res/
│               └── layout/
│                   └── activity_main.xml
├── web/
│   ├── dashboard.html              # Command Center UI
│   └── victim.html                 # PWA fallback for victims
├── docs/
│   └── DOC-20261109-WA0002.pdf     # Reference material
├── ARCHITECTURE.md                 # System data flow and API specs
├── README.md                       # Project setup instructions
└── LICENSE                         # Legal open-source license
```
