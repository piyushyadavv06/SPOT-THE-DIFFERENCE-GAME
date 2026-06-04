# ============================================================
#  frontend/backend_client.py
#  Python ↔ C++ Server communication
#  Sends commands, receives responses
# ============================================================

import socket
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999
TIMEOUT     = 5.0

class BackendClient:
    def __init__(self):
        self._lock = threading.Lock()
        self._sock = None
        self._connected = False

    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(TIMEOUT)
            self._sock.connect((SERVER_HOST, SERVER_PORT))
            self._connected = True
            print("[Client] Connected to C++ server")
            return True
        except Exception as e:
            print(f"[Client] Cannot connect to server: {e}")
            self._connected = False
            return False

    def _send(self, command: str) -> str:
        if not self._connected:
            return "ERR|Not connected"
        with self._lock:
            try:
                self._sock.sendall((command + "\n").encode())
                data = self._sock.recv(4096).decode().strip()
                return data
            except Exception as e:
                self._connected = False
                return f"ERR|{e}"

    def _parse(self, response: str):
        """Returns (True, data) or (False, error_msg)"""
        if response.startswith("OK"):
            parts = response.split("|", 1)
            return True, (parts[1] if len(parts) > 1 else "")
        elif response.startswith("ERR"):
            parts = response.split("|", 1)
            return False, (parts[1] if len(parts) > 1 else "Error")
        return False, response

    # ---- Auth -----------------------------------------------
    def signup(self, username: str, password: str):
        if not self._connected: return True, 1, username
        r = self._send(f"SIGNUP|{username}|{password}")
        ok, data = self._parse(r)
        if ok:
            parts = data.split("|")
            return True, int(parts[0]), parts[1]
        return False, data, None

    def login(self, username: str, password: str):
        if not self._connected: return True, 1, username
        r = self._send(f"LOGIN|{username}|{password}")
        ok, data = self._parse(r)
        if ok:
            parts = data.split("|")
            return True, int(parts[0]), parts[1]
        return False, data, None

    # ---- Scores ---------------------------------------------
    def save_score(self, player_id, level_id, score, stars, time_taken, wrong, hints):
        r = self._send(f"SAVE_SCORE|{player_id}|{level_id}|{score}|{stars}|{time_taken}|{wrong}|{hints}")
        ok, data = self._parse(r)
        return ok

    def get_best_score(self, player_id, level_id) -> int:
        r = self._send(f"BEST_SCORE|{player_id}|{level_id}")
        ok, data = self._parse(r)
        return int(data) if ok and data.lstrip('-').isdigit() else -1

    def get_best_stars(self, player_id, level_id) -> int:
        """Returns best stars (1-3) for this level, or -1 if never played."""
        r = self._send(f"BEST_STARS|{player_id}|{level_id}")
        ok, data = self._parse(r)
        return int(data) if ok and data.lstrip('-').isdigit() else -1

    def is_level_unlocked(self, player_id, level_id) -> bool:
        if level_id <= 1: return True
        r = self._send(f"IS_UNLOCKED|{player_id}|{level_id}")
        ok, data = self._parse(r)
        return ok and data == "1"

    def get_leaderboard(self):
        r = self._send("LEADERBOARD")
        ok, data = self._parse(r)
        if not ok or data == "EMPTY": return []
        rows = []
        for entry in data.split(";"):
            parts = entry.split(",")
            if len(parts) >= 5:
                rows.append({
                    "username": parts[0],
                    "score":    int(parts[1]),
                    "level_id": int(parts[2]),
                    "stars":    int(parts[3]),
                    "played_at": parts[4][:10]
                })
        return rows

    def calc_score(self, found, total_diffs, time_left, time_limit, wrong, max_lives, hints):
        """Returns (score, stars)"""
        r = self._send(f"CALC_SCORE|{found}|{total_diffs}|{int(time_left)}|{time_limit}|{wrong}|{max_lives}|{hints}")
        ok, data = self._parse(r)
        if ok:
            try:
                parts = data.split("|")
                return int(parts[0]), int(parts[1])
            except: pass
            
        # FIXED: Raise an exception if connection fails so Pygame falls back to local math!
        raise RuntimeError("Backend unreachable, use local math")

    def ping(self) -> bool:
        r = self._send("PING")
        ok, _ = self._parse(r)
        return ok

    def close(self):
        if self._sock:
            try: self._sock.close()
            except: pass