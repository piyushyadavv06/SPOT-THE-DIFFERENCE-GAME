# ============================================================
#  frontend/screens/lose_screen.py
#  FIXED: BGM paused on enter, SFX via AudioManager, no overlap
# ============================================================

import pygame, math, random, os
from ui_config import C, txt, draw_stars, draw_transition

# ============================================================
# DARK THEME
# ============================================================

D = {
    "bg":      (10,  12,  24),
    "card":    (20,  24,  42),
    "accent":  (108, 92, 231),
    "danger":  (255, 80, 110),
    "text":    (240, 245, 255),
    "sub":     (120, 125, 150),
    "btn_sec": (30,  35,  60),
    "border":  (40,  45,  75),
    "white":   (255, 255, 255),
}

# ============================================================
# PARTICLES
# ============================================================

class _ColdEmber:

    def __init__(self, W, H):
        self.reset(W, H, initial_burst=True)

    def reset(self, W, H, initial_burst=False):
        self.x = random.uniform(0, W)
        self.y = (
            random.uniform(0, H)
            if initial_burst
            else H + random.uniform(10, 50)
        )
        self.vx   = random.uniform(-0.5, 0.5)
        self.vy   = random.uniform(-0.5, -2.5)
        self.size = random.uniform(2, 6)
        self.color = random.choice([
            (70,  80, 140),
            (40,  50, 100),
            (100, 60,  90),
            (108, 92, 231),
        ])
        self.base_alpha = random.randint(40, 150)

    def update(self, dt, W, H, mouse_pos):
        self.vx += math.sin(self.y * 0.05) * 0.02
        if mouse_pos:
            mx, my = mouse_pos
            dx = self.x - mx
            dy = self.y - my
            dist = math.hypot(dx, dy)
            if 0 < dist < 120:
                force = (120 - dist) * 0.03
                self.vx += (dx / dist) * force * (dt * 60)
                self.vy += (dy / dist) * force * (dt * 60)
        self.vx *= 0.96
        self.vy  = min(self.vy * 0.98, -0.5)
        self.x  += self.vx * (dt * 60)
        self.y  += self.vy * (dt * 60)
        if self.y < -20:
            self.reset(W, H)

    def draw(self, surf):
        s = pygame.Surface(
            (int(self.size * 2), int(self.size * 2)),
            pygame.SRCALPHA,
        )
        pygame.draw.circle(
            s, (*self.color, self.base_alpha),
            (int(self.size), int(self.size)),
            int(self.size),
        )
        surf.blit(s, (int(self.x) - int(self.size), int(self.y) - int(self.size)))


# ============================================================
# SOUND HELPER
# ============================================================

def _load_sound(filename):
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "assets", "sounds", filename)
    try:
        snd = pygame.mixer.Sound(path)
        return snd
    except Exception as e:
        print(f"[LoseScreen] Could not load sound '{filename}': {e}")
        return None


# ============================================================
# LOSE SCREEN
# ============================================================

class LoseScreen:

    def __init__(self, app):
        self.app       = app
        self.W, self.H = app["W"], app["H"]
        self.t         = 0.0

        self.embers = [_ColdEmber(self.W, self.H) for _ in range(100)]

        card_w, card_h = 360, 240
        self.card_rect = pygame.Rect(
            (self.W - card_w) // 2,
            (self.H - card_h) // 2,
            card_w, card_h,
        )

        self.btn_menu = pygame.Rect(
            self.card_rect.x + 30,
            self.card_rect.bottom - 70,
            140, 44,
        )
        self.btn_retry = pygame.Rect(
            self.card_rect.right - 170,
            self.card_rect.bottom - 70,
            140, 44,
        )

        self._snd_lose = _load_sound("faaah.wav")

    # ========================================================
    # ENTER HOOK  — called by main.py every time this screen
    #               becomes active.
    # ========================================================

    def _on_enter(self):
        """Pause BGM, stop all SFX, then play lose stinger once."""
        self.t = 0.0

        audio = self.app["audio"]

        # Pause BGM so resume() works correctly on the way back
        audio.pause_music()

        # Kill every SFX channel (heartbeat, correct hits, etc.)
        audio.stop_all_sfx()

        # Play lose stinger at sfx volume (NOT affected by BGM mute)
        if self._snd_lose:
            self._snd_lose.set_volume(audio.sfx_volume)
            self._snd_lose.stop()   # no stacking on fast re-entry
            self._snd_lose.play()

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_menu.collidepoint(e.pos):
                    if self._snd_lose:
                        self._snd_lose.stop()
                    self.app["audio"].resume_music()
                    self.app["current"] = "level_select"

                elif self.btn_retry.collidepoint(e.pos):
                    if self._snd_lose:
                        self._snd_lose.stop()
                    self.app["audio"].resume_music()
                    self.app["current"] = "game"

    # ========================================================
    # UPDATE
    # ========================================================

    def update(self, dt):
        self.t += dt
        mouse_pos = pygame.mouse.get_pos()
        for ember in self.embers:
            ember.update(dt, self.W, self.H, mouse_pos)

    # ========================================================
    # DRAW
    # ========================================================

    def draw(self, surface):
        surface.fill(D["bg"])

        r_offset = int(self.t * 10) % 60
        for i in range(-self.H, self.W + self.H, 60):
            pygame.draw.line(
                surface, (15, 18, 30),
                (i + r_offset, 0),
                (i + r_offset - self.H, self.H), 3,
            )

        for ember in self.embers:
            ember.draw(surface)

        self._draw_card(surface)
        draw_transition(surface, self.t)

    # ========================================================
    # CARD
    # ========================================================

    def _draw_card(self, surface):
        mx, my = pygame.mouse.get_pos()
        cr = self.card_rect

        # Drop shadow
        sh = pygame.Surface((cr.w + 60, cr.h + 60), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 40),
                         (0, 0, cr.w + 60, cr.h + 60), border_radius=28)
        surface.blit(sh, (cr.x - 30, cr.y + 20))

        # Card body
        pygame.draw.rect(surface, D["card"], cr, border_radius=22)
        pygame.draw.rect(surface, D["border"], cr, width=2, border_radius=22)

        txt(surface, "MISSION FAILED", cr.centerx, cr.y + 40,
            22, D["danger"], bold=True, center=True)
        txt(surface, "Don't give up! Dust off and try again.",
            cr.centerx, cr.y + 68, 12, D["sub"], center=True)

        score = self.app.get("last_score", 0)
        draw_stars(surface, 0, cr.centerx, cr.y + 105, size=24)
        txt(surface, f"Score: {score}", cr.centerx, cr.y + 135,
            16, D["text"], bold=True, center=True)

        hov_menu  = self.btn_menu.collidepoint((mx, my))
        hov_retry = self.btn_retry.collidepoint((mx, my))

        # Quit / Menu button
        pygame.draw.rect(surface, D["btn_sec"], self.btn_menu, border_radius=12)
        if hov_menu:
            pygame.draw.rect(surface, D["sub"], self.btn_menu,
                             width=2, border_radius=12)
        txt(surface, "Quit", self.btn_menu.centerx, self.btn_menu.centery,
            14, D["sub"], bold=True, center=True)

        # Retry button
        btn_col = (130, 115, 250) if hov_retry else D["accent"]
        pygame.draw.rect(surface, btn_col, self.btn_retry, border_radius=12)
        txt(surface, "Retry Level", self.btn_retry.centerx, self.btn_retry.centery,
            14, D["white"], bold=True, center=True)


# ============================================================
# LEADERBOARD SCREEN
# ============================================================

LD = {
    "bg":       (10,  12,  24),
    "card":     (20,  24,  42),
    "accent":   (108, 92, 231),
    "gold":     (255, 210,  50),
    "silver":   (192, 192, 192),
    "bronze":   (205, 127,  50),
    "text":     (240, 245, 255),
    "sub":      (120, 125, 150),
    "border":   (40,  45,  75),
    "white":    (255, 255, 255),
    "row_even": (25,  30,  52),
    "row_odd":  (18,  22,  40),
}


class LeaderboardScreen:

    def __init__(self, app):
        self.app    = app
        self.W      = app["W"]
        self.H      = app["H"]
        self.t      = 0.0
        self.rows   = []
        self.scroll = 0          # top visible row index (for future scrolling)
        self._loading = True
        self._error   = ""

        self.btn_back = pygame.Rect(
            (self.W - 160) // 2, self.H - 70, 160, 44
        )

    # ── enter hook ─────────────────────────────────────────

    def _on_enter(self):
        self.t        = 0.0
        self.scroll   = 0
        self._loading = True
        self._error   = ""
        self.rows     = []
        self._fetch_data()

    def _fetch_data(self):
        try:
            backend = self.app["backend"]
            data    = backend.get_leaderboard()
            if data is None:
                self._error = "Could not reach server."
            else:
                self.rows = data          # list of dicts from backend_client
        except Exception as e:
            self._error = f"Error: {e}"
        finally:
            self._loading = False

    # ── events ─────────────────────────────────────────────

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_back.collidepoint(e.pos):
                    self.app["audio"].resume_music()
                    self.app["current"] = "level_select"
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.app["audio"].resume_music()
                    self.app["current"] = "level_select"

    # ── update ─────────────────────────────────────────────

    def update(self, dt):
        self.t += dt

    # ── draw ───────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(LD["bg"])

        # animated diagonal grid
        r_off = int(self.t * 10) % 60
        for i in range(-self.H, self.W + self.H, 60):
            pygame.draw.line(surface, (15, 18, 30),
                             (i + r_off, 0), (i + r_off - self.H, self.H), 3)

        self._draw_header(surface)

        if self._loading:
            txt(surface, "Loading…", self.W // 2, self.H // 2,
                22, LD["sub"], center=True)
        elif self._error:
            txt(surface, self._error, self.W // 2, self.H // 2,
                18, (255, 80, 110), center=True)
            txt(surface, "Make sure the C++ server is running.",
                self.W // 2, self.H // 2 + 32, 13, LD["sub"], center=True)
        elif not self.rows:
            txt(surface, "No scores yet — be the first!", self.W // 2, self.H // 2,
                20, LD["sub"], center=True)
        else:
            self._draw_table(surface)

        self._draw_back_btn(surface)
        from ui_config import draw_transition
        draw_transition(surface, self.t)

    # ── header ─────────────────────────────────────────────

    def _draw_header(self, surface):
        # Title bar
        bar = pygame.Surface((self.W, 80), pygame.SRCALPHA)
        pygame.draw.rect(bar, (*LD["card"], 230), (0, 0, self.W, 80),
                         border_bottom_left_radius=20, border_bottom_right_radius=20)
        surface.blit(bar, (0, 0))
        pygame.draw.rect(surface, LD["border"], (0, -2, self.W, 82),
                         2, border_bottom_left_radius=20, border_bottom_right_radius=20)

        txt(surface, "LEADERBOARD", self.W // 2, 40,
            26, LD["accent"], bold=True, center=True)

        # Column headings
        col_y = 110
        heads = [("#", 80), ("Player", 280), ("Level", 480),
                 ("Stars", 640), ("Score", 820), ("Date", 1010)]
        for label, cx in heads:
            txt(surface, label, cx, col_y, 12, LD["sub"], bold=True, center=True)

        pygame.draw.line(surface, LD["border"],
                         (40, col_y + 16), (self.W - 40, col_y + 16), 1)

    # ── table ──────────────────────────────────────────────

    def _draw_table(self, surface):
        row_h  = 48
        start_y = 135
        visible = min(len(self.rows), (self.H - 200) // row_h)
        medal_cols = [LD["gold"], LD["silver"], LD["bronze"]]

        for i, row in enumerate(self.rows[self.scroll: self.scroll + visible]):
            rank = self.scroll + i + 1
            ry   = start_y + i * row_h

            # alternating row bg
            row_bg = LD["row_even"] if i % 2 == 0 else LD["row_odd"]
            row_surf = pygame.Surface((self.W - 80, row_h - 4), pygame.SRCALPHA)
            pygame.draw.rect(row_surf, (*row_bg, 200),
                             (0, 0, self.W - 80, row_h - 4), border_radius=10)
            surface.blit(row_surf, (40, ry))

            # rank badge / number
            badge_col = medal_cols[rank - 1] if rank <= 3 else LD["border"]
            pygame.draw.circle(surface, badge_col, (80, ry + row_h // 2 - 2), 16)
            txt(surface, str(rank), 80, ry + row_h // 2 - 2,
                13, LD["bg"] if rank <= 3 else LD["sub"], bold=True, center=True)

            # username
            name_col = medal_cols[rank - 1] if rank <= 3 else LD["text"]
            txt(surface, row.get("username", "?"), 280, ry + row_h // 2 - 2,
                15, name_col, bold=(rank <= 3), center=True)

            # level
            txt(surface, f"Level {row.get('level_id', '?')}", 480, ry + row_h // 2 - 2,
                13, LD["sub"], center=True)

            # stars — use the same draw_stars() helper as level select
            stars = row.get("stars", 0)
            draw_stars(surface, stars, 640, ry + row_h // 2 - 2, size=14)

            # score
            txt(surface, str(row.get("score", 0)), 820, ry + row_h // 2 - 2,
                16, (255, 190, 80), bold=True, center=True)

            # date
            txt(surface, row.get("played_at", ""), 1010, ry + row_h // 2 - 2,
                12, LD["sub"], center=True)

    # ── back button ────────────────────────────────────────

    def _draw_back_btn(self, surface):
        mx, my = pygame.mouse.get_pos()
        hov    = self.btn_back.collidepoint((mx, my))
        col    = (80, 64, 196) if hov else LD["accent"]
        pygame.draw.rect(surface, col, self.btn_back, border_radius=12)
        txt(surface, "← Back", self.btn_back.centerx, self.btn_back.centery,
            14, LD["white"], bold=True, center=True)