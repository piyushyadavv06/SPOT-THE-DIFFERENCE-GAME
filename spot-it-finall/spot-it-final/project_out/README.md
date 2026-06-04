# 🔍 SPOT THE DIFFERENCE GAME
## Hackathon Project — C++ Backend + Python Frontend

---

## ▶ HOW TO RUN (Windows — Step by Step)

### STEP 1 — Install Python
→ https://python.org/downloads
→ IMPORTANT: Tick "Add Python to PATH" during install

### STEP 2 — Open the frontend folder in VS Code
File → Open Folder → select the `spot_diff` folder

### STEP 3 — Open terminal (Ctrl + ` backtick)

### STEP 4 — Install pygame
```
pip install pygame
```

### STEP 5 — Run the game (frontend only — no C++ needed yet)
```
cd frontend
python main.py
```

The game opens with login screen immediately!
**The game works WITHOUT the C++ server — scores just won't be saved.**

---

## 🖼️ HOW TO ADD YOUR IMAGES

### Option A — Direct (Fastest for Hackathon)
1. Get two similar photos from Unsplash.com or use your own
2. Edit one photo in Paint/GIMP to make 4-6 differences
3. Name and place them:

```
frontend/assets/levels/easy_1a.png    ← original image
frontend/assets/levels/easy_1b.png    ← modified image (with differences)

frontend/assets/levels/easy_2a.png    ← level 2 original
frontend/assets/levels/easy_2b.png    ← level 2 modified

frontend/assets/levels/easy_3a.png    ← level 3
frontend/assets/levels/easy_3b.png

frontend/assets/levels/med_1a.png     ← medium level 1
frontend/assets/levels/med_1b.png
frontend/assets/levels/med_2a.png
frontend/assets/levels/med_2b.png
frontend/assets/levels/med_3a.png
frontend/assets/levels/med_3b.png

frontend/assets/levels/hard_1a.png    ← hard level 1
frontend/assets/levels/hard_1b.png
frontend/assets/levels/hard_2a.png
frontend/assets/levels/hard_2b.png
frontend/assets/levels/hard_3a.png
frontend/assets/levels/hard_3b.png
```

### Option B — Use Marker Tool (Recommended)
```
cd tools
pip install Pillow
python marker_tool.py
```
1. Click "Load Image 1" → pick original photo
2. Click "Load Image 2" → pick your edited photo
3. LEFT CLICK on each difference spot
4. Use radius slider to adjust click size
5. Click "Save Level JSON"
6. Copy the printed dictionary into `frontend/game_engine.py`
   under LEVEL_DEFINITIONS for the right level number

---

## 📐 UPDATE DIFFERENCE COORDINATES

After placing images, open `frontend/game_engine.py` and update
the `differences` list for each level:

```python
"differences": [
    {"cx": 200, "cy": 180, "radius": 35, "desc": "Missing coffee mug"},
    #  ↑cx = X pixel of difference center in your image
    #        ↑cy = Y pixel of difference center
    #                    ↑radius = how close player must click (px)
]
```

Use the Marker Tool to get exact coordinates automatically.

---

## 🖥️ C++ BACKEND SETUP (Optional — for saving scores)

### On Linux/WSL:
```bash
cd backend
g++ -std=c++17 server.cpp -lsqlite3 -o server
./server
```

### On Windows (MinGW):
```
cd backend
g++ -std=c++17 server.cpp -lsqlite3 -lws2_32 -o server.exe
server.exe
```

Then run the Python frontend — it auto-connects on port 9999.

---

## 📁 FILE STRUCTURE

```
spot_diff/
├── frontend/
│   ├── main.py              ← START HERE (python main.py)
│   ├── game_engine.py       ← Level definitions (EDIT THIS to add images)
│   ├── backend_client.py    ← Talks to C++ server
│   ├── ui_config.py         ← Colors, fonts, shared UI helpers
│   ├── screens/
│   │   ├── login_screen.py  ← Login/Signup UI
│   │   ├── level_select.py  ← Level grid UI
│   │   ├── game_screen.py   ← Gameplay (images, HUD, animations)
│   │   ├── win_screen.py    ← Win + confetti screen
│   │   └── lose_screen.py   ← Lose + leaderboard screens
│   └── assets/
│       └── levels/          ← PUT YOUR IMAGES HERE
│           ├── easy_1a.png
│           ├── easy_1b.png
│           └── ... (18 images total)
├── backend/
│   └── server.cpp           ← C++ server (compile separately)
├── data/
│   └── scores.db            ← SQLite database (auto-created)
└── tools/
    └── marker_tool.py       ← GUI to mark difference positions
```

---

## 🎮 GAME FEATURES

✅ Login / Signup with password hashing
✅ 9 levels (3 Easy, 3 Medium, 3 Hard)
✅ Level unlock system (complete previous to unlock next)
✅ Countdown timer (bar changes color: green→orange→red)
✅ Limited lives (wrong clicks reduce lives)
✅ Live score counting (score increases on correct find)
✅ Hint system (reveals a difference, costs 50 points)
✅ Freeze power-up (stops timer 5s, costs 50 points)
✅ Pause/Resume (ESC or P key or button)
✅ Sparkle particles on correct click
✅ Shake animation on wrong click
✅ Pulsing hint animation
✅ Star rating (1-3 stars based on score)
✅ Win screen with confetti
✅ Leaderboard (global top 10)
✅ C++ backend via TCP socket
✅ SQLite database for scores

---

## 🏆 DIFFICULTY SETTINGS

| Difficulty | Time  | Lives | Differences |
|-----------|-------|-------|-------------|
| Easy      | 120s  | 5     | 4           |
| Medium    | 90s   | 4     | 5           |
| Hard      | 60s   | 3     | 6           |

---

## 👥 MEMBER FILE ASSIGNMENTS

| Member | Files |
|--------|-------|
| M1 — Game Engine | `frontend/game_engine.py`, `backend/server.cpp` |
| M2 — Database    | `backend/server.cpp` (DB part), `frontend/backend_client.py` |
| M3 — UI/UX       | All `frontend/screens/*.py`, `frontend/ui_config.py` |
| M4 — Levels      | `tools/marker_tool.py`, `frontend/assets/levels/` |
| M5 — Audio       | Add `pygame.mixer.Sound()` calls in `game_screen.py` |
