# ============================================================
#  frontend/screens/win_screen.py
#  FIXED: BGM paused on enter, SFX via AudioManager, no overlap
# ============================================================

import pygame, math, random, os
from ui_config import C, txt, draw_stars, draw_transition

D = {
    "bg":      (248, 250, 252),
    "card":    (255, 255, 255),
    "accent":  (108, 92, 231),
    "acc_hov": (80,  64, 196),
    "text":    (20,  25,  35),
    "sub":     (130, 135, 150),
    "btn_sec": (235, 240, 245),
    "border":  (225, 230, 240),
    "white":   (255, 255, 255),
}

# ============================================================
# CONFETTI
# ============================================================

class _Confetti:
    def __init__(self, W, H):
        self.reset(W, H, initial_burst=True)

    def reset(self, W, H, initial_burst=False):
        self.x  = random.uniform(0, W)
        self.y  = random.uniform(-H, H) if initial_burst else random.uniform(-50, -10)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(1.0, 4.0)
        self.w  = random.randint(6, 12)
        self.h  = random.randint(5, 9)
        self.color = random.choice([
            (108, 92, 231),
            (0, 210, 248),
            (52, 199, 141),
            (255, 90, 130),
            (240, 200, 30),
        ])
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-5, 5)

    def update(self, dt, W, H, mouse_pos):
        self.vy += 3.5 * dt
        self.vx *= 0.99
        self.vy *= 0.99
        if mouse_pos:
            mx, my = mouse_pos
            dx = self.x - mx
            dy = self.y - my
            dist = math.hypot(dx, dy)
            if 0 < dist < 150:
                force = (150 - dist) * 0.05
                self.vx += (dx / dist) * force * (dt * 60)
                self.vy += (dy / dist) * force * (dt * 60)
                self.spin += (dx / dist) * force * 2
        self.x += self.vx * (dt * 60)
        self.y += self.vy * (dt * 60)
        self.angle += self.spin * (dt * 60)
        if self.y > H + 20:
            self.reset(W, H)

    def draw(self, surf):
        max_dim = int(math.hypot(self.w, self.h)) + 2
        s = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)
        rect = pygame.Rect(
            max_dim // 2 - self.w // 2,
            max_dim // 2 - self.h // 2,
            self.w, self.h,
        )
        pygame.draw.rect(s, self.color, rect, border_radius=2)
        rot_s = pygame.transform.rotate(s, self.angle)
        r = rot_s.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rot_s, r)


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
        print(f"[WinScreen] Could not load sound '{filename}': {e}")
        return None


# ============================================================
# WIN SCREEN
# ============================================================

class WinScreen:

    def __init__(self, app):
        self.app       = app
        self.W, self.H = app["W"], app["H"]
        self.t         = 0.0

        self.confetti = [_Confetti(self.W, self.H) for _ in range(150)]

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
        self.btn_next = pygame.Rect(
            self.card_rect.right - 170,
            self.card_rect.bottom - 70,
            140, 44,
        )

        self._snd_win = _load_sound("win.wav")

    # ========================================================
    # ENTER HOOK  — called by main.py every time this screen
    #               becomes active.
    # ========================================================

    def _on_enter(self):
        """Stop all SFX channels and BGM, then play win stinger in an infinite loop."""
        self.t = 0.0

        audio = self.app["audio"]

        # Pause BGM (so resume works correctly when we leave)
        audio.pause_music()

        # Stop every SFX channel (heartbeat etc.) cleanly
        audio.stop_all_sfx()

        # Play win stinger at sfx volume (NOT affected by BGM mute)
        if self._snd_win:
            self._snd_win.set_volume(audio.sfx_volume)
            self._snd_win.stop()   # ensure no stacking if screen re-entered fast
            self._snd_win.play(loops=-1)

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(e.pos)

    def _handle_click(self, pos):
        current_lvl = self.app.get("selected_level", 1)
        next_lvl    = current_lvl + 1

        if self.btn_menu.collidepoint(pos):
            # Stop win SFX then resume BGM
            if self._snd_win:
                self._snd_win.stop()
            self.app["audio"].resume_music()

            if "local_unlocked" not in self.app:
                self.app["local_unlocked"] = set()
            self.app["local_unlocked"].add(next_lvl)

            self.app["current"] = "level_select"

        elif self.btn_next.collidepoint(pos):
            if self._snd_win:
                self._snd_win.stop()
            self.app["audio"].resume_music()

            if next_lvl <= 9:
                self.app["pending_unlock"] = next_lvl

            self.app["current"] = "level_select"

    # ========================================================
    # UPDATE
    # ========================================================

    def update(self, dt):
        self.t += dt
        mouse_pos = pygame.mouse.get_pos()
        for c in self.confetti:
            c.update(dt, self.W, self.H, mouse_pos)

    # ========================================================
    # DRAW
    # ========================================================

    def draw(self, surface):
        surface.fill(D["bg"])

        r_offset = int(self.t * 15) % 60
        rgc = (234, 238, 245)
        for i in range(-self.H, self.W + self.H, 60):
            pygame.draw.line(surface, rgc,
                             (i + r_offset, 0),
                             (i + r_offset - self.H, self.H), 2)

        for c in self.confetti:
            c.draw(surface)

        self._draw_card(surface)
        draw_transition(surface, self.t)

    # ========================================================
    # CARD
    # ========================================================

    def _draw_card(self, surface):
        mx, my = pygame.mouse.get_pos()
        cr = self.card_rect

        # Drop shadow
        sh = pygame.Surface((cr.w + 40, cr.h + 40), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 15),
                         (0, 0, cr.w + 40, cr.h + 40), border_radius=28)
        surface.blit(sh, (cr.x - 20, cr.y + 15))

        # Accent glow
        c_sh = pygame.Surface((cr.w + 20, cr.h + 20), pygame.SRCALPHA)
        pygame.draw.rect(c_sh, (*D["accent"], 25),
                         (0, 0, cr.w + 20, cr.h + 20), border_radius=28)
        surface.blit(c_sh, (cr.x - 10, cr.y + 5))

        # Card body
        pygame.draw.rect(surface, D["card"], cr, border_radius=22)
        pygame.draw.rect(surface, D["border"], cr, width=2, border_radius=22)

        txt(surface, "LEVEL COMPLETE!", cr.centerx, cr.y + 40,
            24, D["accent"], bold=True, center=True)
        txt(surface, "Outstanding observation skills!", cr.centerx, cr.y + 72,
            13, D["sub"], center=True)

        score = self.app.get("last_score", 0)
        stars = self.app.get("last_stars", 3)

        draw_stars(surface, stars, cr.centerx, cr.y + 115, size=24)
        txt(surface, f"Score: {score}", cr.centerx, cr.y + 145,
            18, D["text"], bold=True, center=True)

        hov_menu = self.btn_menu.collidepoint((mx, my))
        hov_next = self.btn_next.collidepoint((mx, my))

        # Menu button
        pygame.draw.rect(surface, D["btn_sec"], self.btn_menu, border_radius=12)
        if hov_menu:
            pygame.draw.rect(surface, D["sub"], self.btn_menu,
                             width=2, border_radius=12)
        txt(surface, "Menu", self.btn_menu.centerx, self.btn_menu.centery,
            14, D["sub"], bold=True, center=True)

        # Next Level button
        btn_col = D["acc_hov"] if hov_next else D["accent"]
        pygame.draw.rect(surface, btn_col, self.btn_next, border_radius=12)
        txt(surface, "Next Level", self.btn_next.centerx, self.btn_next.centery,
            14, D["white"], bold=True, center=True)