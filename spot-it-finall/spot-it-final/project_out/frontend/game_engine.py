# ============================================================
#  frontend/game_engine.py
#  Level loading, game state, click detection
#  Communicates with C++ server for score calculation
# ============================================================

import json, math, os

# ---- Level definitions (ADD YOUR IMAGES HERE) ---------------
# Each level: image paths, differences list, time, lives, difficulty
# differences: list of {cx, cy, radius, desc}
# cx, cy = pixel coords of difference CENTER in the original image
# radius = click tolerance in pixels

LEVEL_DEFINITIONS = {
    # ==================== EASY (3 levels) ====================
    1: {
    "id": 1,
    "title": "Kitchen Morning",
    "category": "easy", "difficulty_label": "Easy",
    "img1": "frontend/assets/levels/easy_1a.png",
    "img2": "frontend/assets/levels/easy_1b.png",
    "time_limit": 90,
    "max_wrong": 5,
    "tolerance": 20,
    "differences": [
        {
            "cx": 261,
            "cy": 37,
            "radius": 42,
            "desc": "Difference 1"
        },
        {
            "cx": 86,
            "cy": 73,
            "radius": 42,
            "desc": "Difference 2"
        },
        {
            "cx": 311,
            "cy": 282,
            "radius": 42,
            "desc": "Difference 3"
        },
        {
            "cx": 520,
            "cy": 444,
            "radius": 56,
            "desc": "Difference 4"
        }
    ]
},
    2: {
    "id": 2,
    "title": "Garden Afternoon",
    "category": "easy", "difficulty_label": "Easy",
    "img1": "frontend/assets/levels/easy_2a.png",
    "img2": "frontend/assets/levels/easy_2b.png",
    "time_limit": 90,
    "max_wrong": 5,
    "tolerance": 20,
    "differences": [
        {
            "cx": 392,
            "cy": 313,
            "radius": 39,
            "desc": "Difference 1"
        },
        {
            "cx": 476,
            "cy": 262,
            "radius": 26,
            "desc": "Difference 2"
        },
        {
            "cx": 209,
            "cy": 321,
            "radius": 34,
            "desc": "Difference 3"
        },
        {
            "cx": 550,
            "cy": 449,
            "radius": 24,
            "desc": "Difference 4"
        }
    ]
},
    3: {
    "id": 3,
    "title": "Bedroom Scene",
    "category": "easy", "difficulty_label": "Easy",
    "img1": "frontend/assets/levels/easy_3a.png",
    "img2": "frontend/assets/levels/easy_3b.png",
    "time_limit": 90,
    "max_wrong": 5,
    "tolerance": 20,
    "differences": [
        {
            "cx": 379,
            "cy": 27,
            "radius": 36,
            "desc": "Difference 1"
        },
        {
            "cx": 716,
            "cy": 178,
            "radius": 43,
            "desc": "Difference 2"
        },
        {
            "cx": 547,
            "cy": 475,
            "radius": 33,
            "desc": "Difference 3"
        },
        {
            "cx": 172,
            "cy": 267,
            "radius": 44,
            "desc": "Difference 4"
        }
    ]
},

    # ==================== MEDIUM (3 levels) ==================
    4: {
    "id": 4,
    "title": "Market",
    "category": "medium", "difficulty_label": "Medium",
    "img1": "frontend/assets/levels/med_1a.png",
    "img2": "frontend/assets/levels/med_1b.png",
    "time_limit": 90,
    "max_wrong": 4,
    "tolerance": 20,
    "differences": [
        {
            "cx": 29,
            "cy": 421,
            "radius": 30,
            "desc": "Difference 1"
        },
        {
            "cx": 87,
            "cy": 340,
            "radius": 30,
            "desc": "Difference 2"
        },
        {
            "cx": 547,
            "cy": 299,
            "radius": 30,
            "desc": "Difference 3"
        },
        {
            "cx": 681,
            "cy": 382,
            "radius": 30,
            "desc": "Difference 4"
        },
        {
            "cx": 773,
            "cy": 400,
            "radius": 41,
            "desc": "Difference 5"
        }
    ]
},
    5: {
    "id": 5,
    "title": "Playground",
    "category": "medium", "difficulty_label": "Medium",
    "img1": "frontend/assets/levels/med_2a.png",
    "img2": "frontend/assets/levels/med_2b.png",
    "time_limit": 90,
    "max_wrong": 4,
    "tolerance": 20,
    "differences": [
        {
            "cx": 528,
            "cy": 44,
            "radius": 33,
            "desc": "Difference 1"
        },
        {
            "cx": 303,
            "cy": 254,
            "radius": 33,
            "desc": "Difference 2"
        },
        {
            "cx": 153,
            "cy": 382,
            "radius": 21,
            "desc": "Difference 3"
        },
        {
            "cx": 140,
            "cy": 278,
            "radius": 26,
            "desc": "Difference 4"
        },
        {
            "cx": 300,
            "cy": 420,
            "radius": 32,
            "desc": "Difference 5"
        }
    ]
}, 
    6: {
    "id": 6,
    "title": "City Street",
    "category": "medium", "difficulty_label": "Medium",
    "img1": "frontend/assets/levels/med_3a.png",
    "img2": "frontend/assets/levels/med_3b.png",
    "time_limit": 90,
    "max_wrong": 4,
    "tolerance": 20,
    "differences": [
        {
            "cx": 671,
            "cy": 415,
            "radius": 37,
            "desc": "Difference 1"
        },
        {
            "cx": 591,
            "cy": 97,
            "radius": 37,
            "desc": "Difference 2"
        },
        {
            "cx": 174,
            "cy": 397,
            "radius": 43,
            "desc": "Difference 3"
        },
        {
            "cx": 401,
            "cy": 354,
            "radius": 32,
            "desc": "Difference 4"
        },
        {
            "cx": 766,
            "cy": 194,
            "radius": 40,
            "desc": "Difference 5"
        }
    ]
},

    # ==================== HARD (3 levels) ====================
    7: {
    "id": 7,
    "title": "Cozy Hearth",
    "category": "hard", "difficulty_label": "Hard",
    "img1": "frontend/assets/levels/hard_1a.png",
    "img2": "frontend/assets/levels/hard_1b.png",
    "time_limit": 90,
    "max_wrong": 3,
    "tolerance": 20,
    "differences": [
        {
            "cx": 726,
            "cy": 43,
            "radius": 20,
            "desc": "Difference 1"
        },
        {
            "cx": 252,
            "cy": 193,
            "radius": 27,
            "desc": "Difference 2"
        },
        {
            "cx": 15,
            "cy": 327,
            "radius": 35,
            "desc": "Difference 3"
        },
        {
            "cx": 581,
            "cy": 373,
            "radius": 41,
            "desc": "Difference 4"
        },
        {
            "cx": 567,
            "cy": 157,
            "radius": 31,
            "desc": "Difference 5"
        },
        {
            "cx": 774,
            "cy": 399,
            "radius": 31,
            "desc": "Difference 6"
        }
    ]
},
    8: {
    "id": 8,
    "title": "Luxury Washroom",
    "category": "hard", "difficulty_label": "Hard",
    "img1": "frontend/assets/levels/hard_2a.png",
    "img2": "frontend/assets/levels/hard_2b.png",
    "time_limit": 90,
    "max_wrong": 3,
    "tolerance": 20,
    "differences": [
        {
            "cx": 46,
            "cy": 323,
            "radius": 37,
            "desc": "Difference 1"
        },
        {
            "cx": 243,
            "cy": 71,
            "radius": 31,
            "desc": "Difference 2"
        },
        {
            "cx": 356,
            "cy": 84,
            "radius": 26,
            "desc": "Difference 3"
        },
        {
            "cx": 615,
            "cy": 309,
            "radius": 34,
            "desc": "Difference 4"
        },
        {
            "cx": 522,
            "cy": 455,
            "radius": 29,
            "desc": "Difference 5"
        },
        {
            "cx": 281,
            "cy": 273,
            "radius": 35,
            "desc": "Difference 6"
        }
    ]
},
    9: {
    "id": 9,
    "title": "Shopping Mall",
    "category": "hard", "difficulty_label": "Hard",
    "img1": "frontend/assets/levels/hard_3a.png",
    "img2": "frontend/assets/levels/hard_3b.png",
    "time_limit": 90,
    "max_wrong": 3,
    "tolerance": 20,
    "differences": [
        {
            "cx": 161,
            "cy": 29,
            "radius": 30,
            "desc": "Difference 1"
        },
        {
            "cx": 560,
            "cy": 231,
            "radius": 34,
            "desc": "Difference 2"
        },
        {
            "cx": 351,
            "cy": 451,
            "radius": 37,
            "desc": "Difference 3"
        },
        {
            "cx": 562,
            "cy": 455,
            "radius": 30,
            "desc": "Difference 4"
        },
        {
            "cx": 767,
            "cy": 419,
            "radius": 36,
            "desc": "Difference 5"
        },
        {
            "cx": 322,
            "cy": 62,
            "radius": 33,
            "desc": "Difference 6"
        }
    ]
},
}

class DiffRegion:
    def __init__(self, d):
        self.cx     = d["cx"]
        self.cy     = d["cy"]
        self.radius = d["radius"]
        self.desc   = d.get("desc", "")
        self.found  = False

class Level:
    def __init__(self, level_id):
        if level_id not in LEVEL_DEFINITIONS:
            raise ValueError(f"Level {level_id} not found")
        d = LEVEL_DEFINITIONS[level_id]
        self.id          = d["id"]
        self.title       = d["title"]
        self.category    = d["category"]
        self.diff_label  = d["difficulty_label"]
        self.img1_path   = d["img1"]
        self.img2_path   = d["img2"]
        self.time_limit  = d["time_limit"]
        self.max_wrong   = d["max_wrong"]
        self.tolerance   = d["tolerance"]
        self.regions     = [DiffRegion(r) for r in d["differences"]]

class GameState:
    def __init__(self):
        self.phase        = "menu"
        self.level        = None
        self.time_left    = 0.0
        self.lives        = 5
        self.score        = 0
        self.wrong_clicks = 0
        self.hints_used   = 0
        self.frozen       = False
        self.freeze_t     = 0.0
        self.regions      = []

    def start(self, level: Level):
        self.level        = level
        self.phase        = "playing"
        self.time_left    = float(level.time_limit)
        self.lives        = level.max_wrong
        self.score        = 0
        self.wrong_clicks = 0
        self.hints_used   = 0
        self.frozen       = False
        self.freeze_t     = 0.0
        self.regions      = [DiffRegion({"cx":r.cx,"cy":r.cy,"radius":r.radius,"desc":r.desc})
                              for r in level.regions]

    def tick(self, dt):
        if self.phase not in ("playing", "how_to_play"): return
        if self.phase == "how_to_play": return
        if self.frozen:
            self.freeze_t -= dt
            if self.freeze_t <= 0: self.frozen = False
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.phase = "lose"

    def _scoring_config(self):
        """Returns (base_pts, time_factor, wrong_pen, lives_bonus) per difficulty."""
        cat = self.level.category if self.level else "easy"
        if cat == "easy":
            return 150, 0.5, 30, 25
        elif cat == "medium":
            return 200, 0.8, 50, 40
        else:  # hard
            return 300, 1.5, 75, 60

    def check_click(self, img_x, img_y):
        if self.phase != "playing": return False
        base_pts, time_factor, wrong_pen, lives_bonus = self._scoring_config()
        for r in self.regions:
            if r.found: continue
            if math.sqrt((img_x-r.cx)**2+(img_y-r.cy)**2) <= r.radius:
                r.found = True
                # Base points + small time bonus (capped so early finds don't explode)
                time_bonus = int(min(self.time_left, self.level.time_limit * 0.5) * time_factor)
                self.score += base_pts + time_bonus
                if self.found_count() == len(self.regions):
                    self.score += self.lives * lives_bonus
                    self.phase = "win"
                return True
        self.wrong_clicks += 1
        self.lives -= 1
        self.score = max(0, self.score - wrong_pen)
        if self.lives <= 0: self.phase = "lose"
        return False

    def use_hint(self):
        for r in self.regions:
            if not r.found:
                cat = self.level.category if self.level else "easy"
                hint_pen = 50 if cat == "easy" else (75 if cat == "medium" else 100)
                self.hints_used += 1
                self.score = max(0, self.score - hint_pen)
                return r
        return None

    def freeze(self):
        if self.phase != "playing": return
        self.frozen = True
        self.freeze_t = 5.0
        cat = self.level.category if self.level else "easy"
        freeze_pen = 40 if cat == "easy" else (60 if cat == "medium" else 80)
        self.score = max(0, self.score - freeze_pen)

    def pause(self):
        if self.phase == "playing": self.phase = "paused"
    def resume(self):
        if self.phase == "paused": self.phase = "playing"

    def open_how_to_play(self):
        if self.phase == "playing": self.phase = "how_to_play"
    def close_how_to_play(self):
        if self.phase == "how_to_play": self.phase = "playing"

    def found_count(self):
        return sum(1 for r in self.regions if r.found)

    def max_score(self):
        if not self.level: return 1000
        return (len(self.regions)*100 + self.level.time_limit*5 + self.level.max_wrong*50)