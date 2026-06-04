# ============================================================
#  frontend/screens/level_select.py
#  ADDED: High-res vector audio controls & smooth hover animation
# ============================================================
import pygame, math, random
from ui_config import C, txt, draw_stars, draw_transition, rounded_box, font

HEADING_COLOR = (44, 62, 80)

DIFF_CONFIG = {
    "easy":   {"label": "EASY",   "emoji": "", "color": (52, 199, 141), "color_dk": (35, 160, 110), "bg": (238, 252, 245), "tag_bg": HEADING_COLOR, "rows": [1, 2, 3]},
    "medium": {"label": "MEDIUM", "emoji": "", "color": (108, 92, 231), "color_dk": (80, 64, 196),  "bg": (244, 240, 255), "tag_bg": HEADING_COLOR, "rows": [4, 5, 6]},
    "hard":   {"label": "HARD",   "emoji": "", "color": (255, 90, 130), "color_dk": (220, 55, 100), "bg": (255, 240, 244), "tag_bg": HEADING_COLOR, "rows": [7, 8, 9]},
}

BG          = (248, 250, 252)
WHITE       = (255, 255, 255)
C_TEXT      = ( 20,  25,  35)
C_SUB       = (130, 135, 150)
C_BORDER    = (225, 230, 240)
C_CARD_LCK  = (240, 243, 248)
C_PURPLE    = (108, 92, 231)
C_PURP_HOV  = ( 80,  64, 196)

def lerp(a, b, t): return a + (b - a) * t
def ease_out_cubic(t): return 1 - math.pow(1 - t, 3)
def ease_in_out_cubic(t): return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

class _HiddenKey:
    def __init__(self, W, H):
        edge = random.randint(0, 3)
        if edge == 0:   self.start_x, self.start_y = random.randint(50, W-50), random.randint(20, 80)
        elif edge == 1: self.start_x, self.start_y = random.randint(50, W-50), random.randint(H-80, H-20)
        elif edge == 2: self.start_x, self.start_y = random.randint(20, 80), random.randint(50, H-50)
        else:           self.start_x, self.start_y = random.randint(W-80, W-20), random.randint(50, H-50)
        self.x, self.y = self.start_x, self.start_y
        self.t = 0.0
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update(self, dt):
        self.t += dt
        self.y = self.start_y + math.sin(self.t * 3) * 5

    def draw(self, surf):
        alpha = int(100 + math.sin(self.t * 5) * 100)
        s = pygame.Surface((80, 80), pygame.SRCALPHA)

        pygame.draw.circle(s, (218, 165, 32), (20, 40), 14, 4)
        pygame.draw.circle(s, (255, 215, 0),  (20, 40), 12, 2)
        pygame.draw.rect(s, (218, 165, 32), (32, 37, 40, 6), border_radius=2)
        pygame.draw.rect(s, (255, 223, 0),  (32, 38, 38, 2))
        pygame.draw.rect(s, (218, 165, 32), (55, 42, 6, 12), border_radius=1)
        pygame.draw.rect(s, (218, 165, 32), (65, 42, 6, 10), border_radius=1)

        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 215, 0, int(alpha/3)), (40, 40), 30)
        s.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        self.rect = pygame.Rect(self.x - 40, self.y - 40, 80, 80)
        surf.blit(s, (self.x - 40, self.y - 40))

class _ShatterParticle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        a = random.uniform(0, math.tau)
        v = random.uniform(200, 600)
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.r = random.uniform(3, 8)
        self.color = random.choice([(218, 165, 32), (255, 215, 0), (200, 150, 40)])
        self.life = 2.0; self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 600 * dt

    def draw(self, surf):
        if self.age < self.life:
            alpha = int(255 * (1 - self.age/self.life))
            s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.r, self.r), self.r)
            surf.blit(s, (self.x-self.r, self.y-self.r))

class _Orb:
    def __init__(self, W, H):
        self.x = random.randint(0, W); self.y0 = random.randint(0, H)
        self.r = random.randint(15, 40)
        self.ph, self.fr, self.ab = random.uniform(0, math.tau), random.uniform(0.1, 0.3), random.randint(10, 30)
        self.rx = self.ry = 0.0
        col = random.choice([(108, 92, 231), (0, 210, 248), (52, 199, 141), (255, 90, 130)])
        self.surf = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (*col, 255), (self.r, self.r), self.r)

    def update(self, dt, t, mouse_pos):
        base_x = self.x + math.cos(t * self.fr * 0.8 + self.ph) * 20
        base_y = self.y0 + math.sin(t * self.fr + self.ph) * 30
        if mouse_pos:
            mx, my = mouse_pos
            dx, dy = (base_x + self.rx) - mx, (base_y + self.ry) - my
            dist = math.hypot(dx, dy)
            if 0 < dist < 150:
                push = (150 - dist) * 0.15
                self.rx += (dx / dist) * push * (dt * 60)
                self.ry += (dy / dist) * push * (dt * 60)
        self.rx += (0 - self.rx) * min(1.0, dt * 3.0)
        self.ry += (0 - self.ry) * min(1.0, dt * 3.0)

    def draw(self, main_surf, t):
        x = self.x + math.cos(t * self.fr * 0.8 + self.ph) * 20 + self.rx
        y = self.y0 + math.sin(t * self.fr + self.ph) * 30 + self.ry
        a = self.ab + int(math.sin(t * self.fr * 1.5 + self.ph) * 10)
        self.surf.set_alpha(max(0, min(255, a)))
        main_surf.blit(self.surf, (int(x) - self.r, int(y) - self.r))

class _AmbientBlob:
    def __init__(self, W, H):
        self.x = random.randint(0, W); self.y0 = random.randint(0, H)
        self.r = random.randint(300, 500)
        self.ph, self.fr = random.uniform(0, math.tau), random.uniform(0.05, 0.12)
        col = random.choice([(108, 92, 231), (52, 199, 141), (255, 90, 130), (0, 210, 248)])
        self.surf = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (*col, 6), (self.r, self.r), self.r)

    def draw(self, main_surf, t):
        y = self.y0 + math.sin(t * self.fr + self.ph) * 100
        x = self.x + math.cos(t * self.fr * 0.8 + self.ph) * 100
        main_surf.blit(self.surf, (int(x) - self.r, int(y) - self.r))

class LevelSelectScreen:
    def __init__(self, app):
        self.app        = app
        self.W, self.H  = app["W"], app["H"]
        self.t          = 0.0
        self.msg        = ""
        self.msg_t      = 0.0
        self._orbs      = [_Orb(self.W, self.H) for _ in range(25)]
        self._blobs     = [_AmbientBlob(self.W, self.H) for _ in range(5)]

        self.state      = "NORMAL"
        self.target_lvl = None
        self.anim_t     = 0.0
        self.start_rect = None
        self.anim_scale = 1.0
        self.anim_cx    = 0.0
        self.anim_cy    = 0.0
        self.hidden_key = None
        self.particles  = []

        # ── Floating Audio Controls (Bottom-Left) ─────────────
        _ICON = 44
        self.btn_mute    = pygame.Rect(24, self.H - 68, _ICON, _ICON)
        self.slider_rect = pygame.Rect(76, self.H - 52, 170, 11)
        self.dragging_slider  = False

        # Audio Anim state machine
        self._hover_delay   = 0.0
        self._slider_alpha  = 0.0

    # ----------------------------------------------------------
    # Audio helpers
    # ----------------------------------------------------------

    def _update_volume_ls(self, mouse_x: int):
        rel = mouse_x - self.slider_rect.x
        pct = max(0.0, min(1.0, rel / self.slider_rect.w))
        self.app["audio"].set_music_volume(pct)

    def _draw_audio_controls(self, surface: pygame.Surface):
        """
        Circular speaker-icon button + animated smooth-fading volume slider.
        Floating in the bottom-left corner.
        """
        audio  = self.app["audio"]
        btn    = self.btn_mute
        sr     = self.slider_rect
        mx, my = pygame.mouse.get_pos()
        hov_btn = btn.collidepoint(mx, my)

        # ── 1. Circular icon button ───────────────────────────
        btn_cx, btn_cy = btn.centerx, btn.centery
        btn_r = btn.height // 2

        if audio.muted:
            ring_col = (210, 55, 85)
            icon_col = (210, 55, 85)
            wave_col = (210, 55, 85)
            bg_col   = (255, 236, 240)
        else:
            ring_col = C_PURPLE
            icon_col = C_PURPLE
            wave_col = C_PURPLE
            bg_col   = WHITE

        if hov_btn:
            bg_col = tuple(max(0, c - 18) for c in bg_col)

        pygame.draw.circle(surface, bg_col,   (btn_cx, btn_cy), btn_r)
        pygame.draw.circle(surface, ring_col, (btn_cx, btn_cy), btn_r, 2)

        # ── High-Resolution Vector Speaker Icon (Smoothscaled) ──
        big_size = 60
        big_s = pygame.Surface((big_size, big_size), pygame.SRCALPHA)
        
        # Base rectangle
        pygame.draw.rect(big_s, icon_col, (14, 22, 10, 16), border_radius=4)
        
        # Cone polygon
        cone_pts = [(22, 22), (40, 10), (40, 50), (22, 38)]
        pygame.draw.polygon(big_s, icon_col, cone_pts)
        
        if not audio.muted:
            # Sound Waves
            pygame.draw.arc(big_s, wave_col, (24, 15, 30, 30), -math.pi/3, math.pi/3, 5)
            pygame.draw.arc(big_s, wave_col, (16, 5, 50, 50), -math.pi/4, math.pi/4, 5)
        else:
            # Mute Cross
            pygame.draw.line(big_s, (210, 55, 85), (44, 20), (56, 40), 6)
            pygame.draw.line(big_s, (210, 55, 85), (56, 20), (44, 40), 6)
            
        icon_s = pygame.transform.smoothscale(big_s, (24, 24))
        surface.blit(icon_s, (btn_cx - 12, btn_cy - 12))

        # ── 2. Animated Slider ─────────────────────────────
        if self._slider_alpha <= 0:
            return

        alpha = int(255 * self._slider_alpha)

        sw = sr.width + 24
        sh = btn.height
        slider_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        lx = 12
        ly = (sh - sr.height) // 2

        # pill bg
        pill_bg = WHITE if not audio.muted else (250, 236, 240)
        pygame.draw.rect(slider_s, (*pill_bg, alpha), (0, 0, sw, sh), border_radius=18)
        pygame.draw.rect(slider_s, (*ring_col, min(alpha, 100)), (0, 0, sw, sh), 1, border_radius=18)

        # track
        pygame.draw.rect(slider_s, (210, 202, 234, alpha), (lx, ly, sr.width, sr.height), border_radius=6)

        # fill
        fill_w = max(0, int(sr.width * audio.music_volume))
        if fill_w > 0:
            fc = C_PURPLE if not audio.muted else (195, 155, 170)
            pygame.draw.rect(slider_s, (*fc, alpha), (lx, ly, fill_w, sr.height), border_radius=6)

        # knob
        kx = max(lx, min(lx + sr.width, lx + fill_w))
        ky = ly + sr.height // 2
        kfill = WHITE if not audio.muted else (245, 225, 230)
        pygame.draw.circle(slider_s, (*kfill, alpha),   (kx, ky), 8)
        pygame.draw.circle(slider_s, (*ring_col, alpha), (kx, ky), 8, 2)

        # Label
        lf = font(9, bold=True)
        lbl = lf.render("BGM", True, C_SUB)
        lbl.set_alpha(alpha)
        slider_s.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh - lbl.get_height() - 3))

        surface.blit(slider_s, (btn.right + 6, btn.y))

    # ----------------------------------------------------------
    # Events
    # ----------------------------------------------------------

    def handle_events(self, events):
        for e in events:
            # Slider drag state clearing
            if e.type == pygame.MOUSEBUTTONUP:
                self.dragging_slider = False

            # Slider active movement
            if e.type == pygame.MOUSEMOTION and self.dragging_slider:
                self._update_volume_ls(e.pos[0])

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos

                # Audio Controls (Slider)
                if self.slider_rect.inflate(0, 24).collidepoint(e.pos):
                    # Only click slider if it's faded in
                    if self._slider_alpha > 0:
                        self.dragging_slider = True
                        self._update_volume_ls(mx)
                    continue
                
                # Audio Controls (Mute Toggle)
                if self.btn_mute.collidepoint(e.pos) and not self.dragging_slider:
                    self.app["audio"].toggle_mute()
                    continue

                # Normal screen interaction checks
                if self.state == "SEARCH":
                    if self.hidden_key and self.hidden_key.rect.collidepoint(e.pos):
                        self.state = "FLY"
                        self.anim_t = 0.0
                        self.hidden_key.fly_start_x = self.hidden_key.x
                        self.hidden_key.fly_start_y = self.hidden_key.y
                elif self.state == "NORMAL":
                    self._handle_click(e.pos)

    def _handle_click(self, pos):
        lb_r     = pygame.Rect(self.W - 170, 20, 150, 36)
        logout_r = pygame.Rect(20, 20, 100, 36)
        if lb_r.collidepoint(pos):
            self.app["current"] = "leaderboard"; return
        if logout_r.collidepoint(pos):
            self.app["player_id"] = None
            self.app["current"]   = "login";     return
        for card_rect, lvl_id in self._card_layout():
            if card_rect.collidepoint(pos):
                self._select(lvl_id); return

    def _select(self, lvl_id):
        pid = self.app["player_id"]
        unlocked = (lvl_id == 1 or lvl_id in self.app.get("local_unlocked", set()) or self.app["backend"].is_level_unlocked(pid, lvl_id))
        if not unlocked:
            self.msg, self.msg_t = f"Clear Level {lvl_id - 1} first!", 3.0
            return
        self.app["selected_level"] = lvl_id
        self.app["current"] = "game"

    def _card_layout(self):
        cw, ch, gx = 230, 128, 26
        total_w = 3 * cw + 2 * gx
        sx, sy = (self.W - total_w) // 2, 118
        section_h = ch + 60
        cards  = []
        for row_i, (_, cfg) in enumerate(DIFF_CONFIG.items()):
            for col_i, lvl_id in enumerate(cfg["rows"]):
                cards.append((pygame.Rect(sx + col_i * (cw + gx), sy + row_i * section_h + 42, cw, ch), lvl_id))
        return cards

    # ----------------------------------------------------------
    # Update
    # ----------------------------------------------------------

    def update(self, dt):
        self.t += dt
        if self.msg_t > 0: self.msg_t -= dt

        mouse_pos = pygame.mouse.get_pos()
        for orb in self._orbs: orb.update(dt, self.t, mouse_pos)
        
        # ── Audio Controls Hover Tracker (Fade Animation) ──
        mx, my = pygame.mouse.get_pos()
        hover_zone = pygame.Rect(self.btn_mute.x - 10, self.btn_mute.y - 10,
                                 self.slider_rect.right - self.btn_mute.x + 20,
                                 self.btn_mute.height + 20)
        is_hovering = hover_zone.collidepoint((mx, my)) or self.dragging_slider
        
        if is_hovering:
            self._hover_delay += dt
            if self._hover_delay > 0.15: # 150ms delay before fade in
                self._slider_alpha = min(1.0, self._slider_alpha + dt * 5.0) 
        else:
            self._hover_delay = 0.0
            self._slider_alpha = max(0.0, self._slider_alpha - dt * 3.0)

        # State machines
        if self.state == "NORMAL":
            if self.app.get("pending_unlock"):
                self.target_lvl = self.app["pending_unlock"]
                self.app["pending_unlock"] = None
                self.state = "ZOOM_IN"
                self.anim_t = 0.0
                for r, lvl in self._card_layout():
                    if lvl == self.target_lvl: self.start_rect = r; break
                if not self.start_rect: self.state = "NORMAL"

        elif self.state == "ZOOM_IN":
            # Phase 1 (0-1.3s): locked card zooms to center
            self.anim_t += dt
            p = min(1.0, self.anim_t / 1.3)
            e = ease_out_cubic(p)
            self.anim_scale = lerp(1.0, 1.4, e)
            self.anim_cx = lerp(self.start_rect.centerx, self.W // 2, e)
            self.anim_cy = lerp(self.start_rect.centery, self.H // 2, e)
            if p >= 1.0:
                self.state = "KEY_FLY"
                self.anim_t = 0.0
                # Key starts off-screen left, flies to lock hole
                self._key_sx = -80
                self._key_sy = self.H // 2
                self._key_angle = 0.0
                self._key_ex = self.W // 2
                self._key_ey = self.H // 2

        elif self.state == "KEY_FLY":
            # Phase 2 (0-1.8s): golden key flies in with spin, slows near lock
            self.anim_t += dt
            p = min(1.0, self.anim_t / 1.8)
            e = ease_out_cubic(p)
            self._key_x = lerp(self._key_sx, self._key_ex, e)
            self._key_y = lerp(self._key_sy, self._key_ey, e)
            # Key spins fast then aligns to 0
            self._key_angle = lerp(720, 0, ease_out_cubic(p))
            if p >= 1.0:
                self.state = "KEY_INSERT"
                self.anim_t = 0.0

        elif self.state == "KEY_INSERT":
            # Phase 3 (0-0.9s): key nudges into hole, lock shakes
            self.anim_t += dt
            if self.anim_t >= 0.9:
                self.state = "SHATTER"
                self.anim_t = 0.0
                self.particles = [_ShatterParticle(self.W // 2, self.H // 2) for _ in range(90)]
                if "local_unlocked" not in self.app:
                    self.app["local_unlocked"] = set()
                self.app["local_unlocked"].add(self.target_lvl)
                try:
                    self.app["backend"].unlock_level(self.app["player_id"], self.target_lvl)
                except:
                    pass

        elif self.state == "SHATTER":
            # Phase 4 (0-2.2s): lock explodes into gold particles, card flips to unlocked
            self.anim_t += dt
            for pt in self.particles:
                pt.update(dt)
            if self.anim_t >= 2.2:
                self.state = "ZOOM_OUT"
                self.anim_t = 0.0

        elif self.state == "ZOOM_OUT":
            self.anim_t += dt
            p = min(1.0, self.anim_t / 1.3)
            e = ease_in_out_cubic(p)
            self.anim_scale = lerp(1.4, 1.0, e)
            self.anim_cx = lerp(self.W // 2, self.start_rect.centerx, e)
            self.anim_cy = lerp(self.H // 2, self.start_rect.centery, e)
            if p >= 1.0:
                self.state = "NORMAL"
                self.app["selected_level"] = self.target_lvl
                self.app["current"] = "game"

    # ----------------------------------------------------------
    # Draw
    # ----------------------------------------------------------

    def draw(self, surface):
        surface.fill(BG)
        self._draw_bg(surface)
        self._draw_sections(surface)
        self._draw_header(surface)
        self._draw_toast(surface)
        self._draw_audio_controls(surface)   

        if self.state != "NORMAL":
            self._draw_cinematic_overlay(surface)

        draw_transition(surface, self.t)

    def _draw_cinematic_overlay(self, surface):
        # ── Dim overlay alpha ──────────────────────────────────
        if self.state == "ZOOM_IN":
            alpha = int(lerp(0, 210, min(1.0, self.anim_t / 1.3)))
        elif self.state in ("KEY_FLY", "KEY_INSERT"):
            alpha = 210
        elif self.state == "SHATTER":
            alpha = int(lerp(210, 160, min(1.0, self.anim_t / 2.2)))
        elif self.state == "ZOOM_OUT":
            alpha = int(lerp(160, 0, min(1.0, self.anim_t / 1.3)))
        else:
            alpha = 0

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((5, 5, 20, alpha))
        surface.blit(overlay, (0, 0))

        # Difficulty config for color theming
        cfg = DIFF_CONFIG["easy"]
        for _, c in DIFF_CONFIG.items():
            if self.target_lvl in c["rows"]:
                cfg = c
                break

        s = self.anim_scale
        card_w, card_h = int(230 * s), int(128 * s)
        cx, cy = int(self.anim_cx), int(self.anim_cy)
        card_rect = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)

        # ── Premium glow ring behind card ────────────────────
        glow_r = int(card_w * 0.65 + 20)
        if self.state in ("ZOOM_IN", "KEY_FLY", "KEY_INSERT"):
            glow_a = int(80 * min(1.0, self.anim_t * 2))
        elif self.state == "SHATTER":
            pulse = abs(math.sin(self.anim_t * math.pi * 2))
            glow_r = int(card_w * 0.65 + 20 + pulse * 55)
            glow_a = int(140 * pulse)
        else:
            glow_a = 0

        if glow_a > 0:
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            for ri in range(glow_r, 0, -4):
                ga = int(glow_a * (1 - ri / glow_r) * 0.7)
                pygame.draw.circle(glow_surf, (*cfg["color"], ga), (glow_r, glow_r), ri)
            surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # ── Card body ─────────────────────────────────────────
        # Shadow
        sh_s = pygame.Surface((card_w + 60, card_h + 60), pygame.SRCALPHA)
        pygame.draw.rect(sh_s, (0, 0, 0, 60), (0, 0, card_w + 60, card_h + 60),
                         border_radius=int(22 * s))
        surface.blit(sh_s, (card_rect.x - 30, card_rect.y + 18))

        if self.state in ("ZOOM_IN", "KEY_FLY", "KEY_INSERT"):
            # ── LOCKED card appearance ────────────────────────
            pygame.draw.rect(surface, (15, 12, 38), card_rect, border_radius=int(20 * s))
            pygame.draw.rect(surface, (180, 145, 40), card_rect, max(1, int(2 * s)),
                             border_radius=int(20 * s))

            # Inner card highlight
            hl = pygame.Surface((card_w - 8, 3), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 18))
            surface.blit(hl, (card_rect.x + 4, card_rect.y + 4))

            # ── Premium padlock ───────────────────────────────
            # Shake during KEY_INSERT
            shake_x = shake_y = 0
            if self.state == "KEY_INSERT":
                t = self.anim_t
                intensity = math.sin(t * 35) * (1 - t / 0.9) * 8
                shake_x = int(intensity * math.cos(t * 13))
                shake_y = int(intensity * math.sin(t * 17))

            lk_cx = cx + shake_x
            lk_cy = cy - int(5 * s) + shake_y
            lk_s = s * 1.05  # slightly larger than card scale for drama

            # Shackle (arc)
            arc_rx = int(22 * lk_s)
            arc_ry = int(22 * lk_s)
            arc_rect = pygame.Rect(lk_cx - arc_rx, lk_cy - int(32 * lk_s), arc_rx * 2, arc_ry * 2)
            # Thick shackle with gradient feel (draw twice — shadow then main)
            pygame.draw.arc(surface, (60, 45, 10),
                            arc_rect.inflate(6, 6), 0, math.pi, max(2, int(10 * lk_s)))
            pygame.draw.arc(surface, (200, 160, 30),
                            arc_rect, 0, math.pi, max(2, int(8 * lk_s)))
            pygame.draw.arc(surface, (255, 220, 80),
                            arc_rect.inflate(-4, -4), 0.1, math.pi - 0.1, max(1, int(3 * lk_s)))

            # Lock body
            bw, bh = int(52 * lk_s), int(42 * lk_s)
            body_r = pygame.Rect(lk_cx - bw // 2, lk_cy - int(5 * lk_s), bw, bh)

            # Body shadow
            pygame.draw.rect(surface, (10, 10, 35),
                             body_r.move(0, int(4 * lk_s)), border_radius=int(10 * lk_s))

            # Body gradient (two-tone)
            body_top = pygame.Rect(body_r.x, body_r.y, body_r.w, body_r.h // 2)
            body_bot = pygame.Rect(body_r.x, body_r.centery, body_r.w, body_r.h - body_r.h // 2)
            pygame.draw.rect(surface, (140, 90, 10), body_r, border_radius=int(10 * lk_s))
            pygame.draw.rect(surface, (200, 150, 30), body_top,
                             border_top_left_radius=int(10 * lk_s),
                             border_top_right_radius=int(10 * lk_s))

            # Body shine
            shine = pygame.Surface((body_r.w - 8, 4), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 50))
            surface.blit(shine, (body_r.x + 4, body_r.y + 4))

            # Keyhole — circle + notch
            kh_cx, kh_cy = lk_cx, lk_cy + int(12 * lk_s)
            kh_r = int(7 * lk_s)
            pygame.draw.circle(surface, (20, 15, 40), (kh_cx, kh_cy), kh_r)
            pygame.draw.circle(surface, (15, 10, 30), (kh_cx, kh_cy), kh_r - 1)
            notch_w, notch_h = int(5 * lk_s), int(9 * lk_s)
            pygame.draw.rect(surface, (20, 15, 40),
                             (kh_cx - notch_w // 2, kh_cy, notch_w, notch_h))

            # Level label
            txt(surface, f"Level {self.target_lvl}",
                cx, card_rect.bottom + int(14 * s),
                int(11 * s), (180, 170, 220), center=True, bold=True)

        elif self.state == "SHATTER":
            # ── SHATTERING / UNLOCKING ────────────────────────
            t_norm = min(1.0, self.anim_t / 2.2)

            # Card flips to unlocked during shatter
            flip_p = min(1.0, self.anim_t * 1.25)
            if flip_p < 1.0:
                # Locked card fading out
                card_alpha = int(255 * (1 - flip_p))
                cs = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(cs, (15, 12, 38, card_alpha), (0, 0, card_w, card_h),
                                 border_radius=int(20 * s))
                surface.blit(cs, card_rect.topleft)
            else:
                # Unlocked card fading in
                fade_in = min(1.0, (self.anim_t - 0.8) * 1.25)
                cs = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(cs, (*cfg["bg"], int(255 * fade_in)), (0, 0, card_w, card_h),
                                 border_radius=int(20 * s))
                surface.blit(cs, card_rect.topleft)
                pygame.draw.rect(surface, cfg["color"], card_rect,
                                 max(1, int(2 * s)), border_radius=int(20 * s))

                # Badge
                badge_r = pygame.Rect(
                    card_rect.x + int(16 * s), card_rect.y + int(18 * s),
                    int(42 * s), int(42 * s))
                badge_a = int(255 * fade_in)
                bs = pygame.Surface((badge_r.w, badge_r.h), pygame.SRCALPHA)
                pygame.draw.rect(bs, (*cfg["color"], badge_a),
                                 (0, 0, badge_r.w, badge_r.h), border_radius=int(12 * s))
                surface.blit(bs, badge_r.topleft)
                if fade_in > 0.4:
                    txt(surface, str(self.target_lvl),
                        badge_r.centerx, badge_r.centery,
                        int(20 * s), WHITE, bold=True, center=True)

                # "Unlocked!" label
                if fade_in > 0.3:
                    lf = font(int(15 * s), bold=True)
                    ul_surf = lf.render("🔓  Unlocked!", True, cfg["color"])
                    ul_surf.set_alpha(int(fade_in * 255))
                    surface.blit(ul_surf, (
                        cx - ul_surf.get_width() // 2,
                        card_rect.bottom + 14))

            # Gold particle explosion
            for pt in self.particles:
                pt.draw(surface)

        elif self.state == "ZOOM_OUT":
            # Unlocked card zooms back
            cs = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(cs, (*cfg["bg"], 255), (0, 0, card_w, card_h),
                             border_radius=int(20 * s))
            surface.blit(cs, card_rect.topleft)
            pygame.draw.rect(surface, cfg["color"], card_rect,
                             max(1, int(2 * s)), border_radius=int(20 * s))

            badge_r = pygame.Rect(
                card_rect.x + int(16 * s), card_rect.y + int(18 * s),
                int(42 * s), int(42 * s))
            pygame.draw.rect(surface, cfg["color"], badge_r, border_radius=int(12 * s))
            txt(surface, str(self.target_lvl), badge_r.centerx, badge_r.centery,
                int(20 * s), WHITE, bold=True, center=True)
            txt(surface, f"Level {self.target_lvl:02d}",
                card_rect.x + int(70 * s), card_rect.y + int(22 * s),
                int(16 * s), (30, 35, 55), bold=True)

        # ── Floating KEY (KEY_FLY + KEY_INSERT phases) ────────
        if self.state in ("KEY_FLY", "KEY_INSERT"):
            kx = getattr(self, "_key_x", cx)
            ky = getattr(self, "_key_y", cy)
            angle = getattr(self, "_key_angle", 0.0)

            if self.state == "KEY_INSERT":
                t = self.anim_t
                # Nudge key rightward into the lock hole
                insert_dist = ease_out_cubic(min(1.0, t / 0.9)) * int(18 * s)
                kx = cx + insert_dist
                ky = cy + int(12 * s)  # keyhole position
                angle = 0.0

            key_size = int(70 * s)
            key_surf = pygame.Surface((key_size, key_size), pygame.SRCALPHA)
            ks = key_size / 70

            # Key glow
            glow_ks = pygame.Surface((key_size + 20, key_size + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_ks, (255, 215, 0, 50),
                               ((key_size + 20) // 2, (key_size + 20) // 2),
                               key_size // 2 + 6)
            surface.blit(glow_ks, (int(kx) - (key_size + 20) // 2,
                                   int(ky) - (key_size + 20) // 2))

            # Key ring (circle)
            ring_cx, ring_cy = int(18 * ks), int(35 * ks)
            pygame.draw.circle(key_surf, (180, 140, 30), (ring_cx, ring_cy), int(14 * ks), max(1, int(6 * ks)))
            pygame.draw.circle(key_surf, (255, 215, 0), (ring_cx, ring_cy), int(14 * ks), max(1, int(4 * ks)))
            pygame.draw.circle(key_surf, (255, 235, 100), (ring_cx, ring_cy), int(8 * ks), max(1, int(2 * ks)))

            # Key shaft
            shaft_rect = (ring_cx + int(12 * ks), int(32 * ks), int(35 * ks), int(6 * ks))
            pygame.draw.rect(key_surf, (200, 150, 30), shaft_rect, border_radius=3)
            pygame.draw.rect(key_surf, (255, 215, 0), shaft_rect, border_radius=3)

            # Key teeth (2 teeth on bottom of shaft)
            tooth_x = ring_cx + int(28 * ks)
            pygame.draw.rect(key_surf, (255, 215, 0),
                             (tooth_x, int(38 * ks), int(6 * ks), int(8 * ks)), border_radius=2)
            pygame.draw.rect(key_surf, (255, 215, 0),
                             (tooth_x + int(10 * ks), int(38 * ks), int(5 * ks), int(6 * ks)), border_radius=2)

            # Shine on ring
            pygame.draw.circle(key_surf, (255, 245, 150, 160),
                               (ring_cx - int(4 * ks), ring_cy - int(4 * ks)), int(4 * ks))

            # Rotate and blit
            rotated = pygame.transform.rotozoom(key_surf, angle, 1.0)
            surface.blit(rotated, (int(kx) - rotated.get_width() // 2,
                                   int(ky) - rotated.get_height() // 2))

    def _draw_bg(self, surface):
        r_offset = int(self.t * 15) % 60
        rgc = (234, 238, 245)
        for i in range(-self.H, self.W + self.H, 60):
            pygame.draw.line(surface, rgc, (i + r_offset, 0), (i + r_offset - self.H, self.H), 2)
        for blob in self._blobs: blob.draw(surface, self.t)
        for orb in self._orbs: orb.draw(surface, self.t)

    def _draw_header(self, surface):
        sh = pygame.Surface((self.W, 86), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 8), (0, 0, self.W, 86))
        surface.blit(sh, (0, 5))

        HEADER_BG = (235, 240, 248)
        pygame.draw.rect(surface, HEADER_BG, (0, 0, self.W, 76))
        pygame.draw.rect(surface, C_PURPLE, (0, 0, self.W, 4))

        txt(surface, f"Player: {self.app['player_name']}", 140, 42, 13, C_TEXT, bold=True)
        txt(surface, "SpotQuest", self.W // 2, 40, 22, C_TEXT, bold=True, center=True)

        m = pygame.mouse.get_pos()

        lr = pygame.Rect(20, 22, 104, 34)
        lh = lr.collidepoint(m)
        pygame.draw.rect(surface, (255, 240, 245) if lh else BG, lr, border_radius=18)
        pygame.draw.rect(surface, (255, 160, 180) if lh else C_BORDER, lr, 2, border_radius=18)
        logout_txt_color = (220, 50, 80) if lh else (80, 90, 110)
        txt(surface, "Logout", lr.centerx, lr.centery, 12, logout_txt_color, bold=True, center=True)

        lb = pygame.Rect(self.W - 168, 22, 148, 34)
        bh = lb.collidepoint(m)
        pygame.draw.rect(surface, C_PURPLE if bh else BG, lb, border_radius=18)
        pygame.draw.rect(surface, C_PURP_HOV if bh else C_BORDER, lb, 2, border_radius=18)
        lb_txt_color = WHITE if bh else (80, 90, 110)
        txt(surface, "Leaderboard", lb.centerx, lb.centery, 12, lb_txt_color, bold=True, center=True)

    def _draw_sections(self, surface):
        from game_engine import LEVEL_DEFINITIONS
        pid, backend = self.app["player_id"], self.app["backend"]
        cards = self._card_layout()
        card_idx = 0

        cw, gx = 230, 26
        total_w = 3 * cw + 2 * gx
        sx, sy = (self.W - total_w) // 2, 118
        section_h = 128 + 60

        for row_i, (cat, cfg) in enumerate(DIFF_CONFIG.items()):
            sec_y = sy + row_i * section_h
            pill_w, pill_h = 110, 28
            pill = pygame.Rect(sx, sec_y + 6, pill_w, pill_h)

            psh = pygame.Surface((pill_w + 10, pill_h + 10), pygame.SRCALPHA)
            pygame.draw.rect(psh, (*cfg["tag_bg"], 40), (0, 0, pill_w + 10, pill_h + 10), border_radius=18)
            surface.blit(psh, (pill.x - 5, pill.y - 2))

            pygame.draw.rect(surface, cfg["tag_bg"], pill, border_radius=14)
            txt(surface, f"{cfg['emoji']}  {cfg['label']}", pill.centerx, pill.centery, 12, WHITE, bold=True, center=True)

            ld = LEVEL_DEFINITIONS[cfg["rows"][0]]
            txt(surface, f"Time: {ld['time_limit']}s  |  Diffs: {len(ld['differences'])}", sx + total_w, sec_y + 18, 12, (80, 90, 110), right=True, bold=True)

            pygame.draw.line(surface, C_BORDER, (sx, sec_y + 38), (sx + total_w, sec_y + 38), 1)
            pygame.draw.line(surface, cfg["color"], (sx, sec_y + 38), (sx + 80, sec_y + 38), 3)

            for _ in cfg["rows"]:
                rect, lvl_id = cards[card_idx]; card_idx += 1
                if self.state != "NORMAL" and lvl_id == self.target_lvl:
                    continue
                self._draw_card(surface, rect, lvl_id, cfg, pid, backend)

    def _draw_card(self, surface, rect, lvl_id, cfg, pid, backend):
        from game_engine import LEVEL_DEFINITIONS
        ld = LEVEL_DEFINITIONS[lvl_id]
        unlocked = (lvl_id == 1 or lvl_id in self.app.get("local_unlocked", set()) or backend.is_level_unlocked(pid, lvl_id))
        best = backend.get_best_score(pid, lvl_id)
        # Retrieve stored stars — prefer local cache (set right after a game),
        # then try the backend, so the display is always accurate.
        _cache = self.app.get("best_stars_cache", {})
        if lvl_id in _cache:
            _best_stars = _cache[lvl_id]
        else:
            _best_stars = backend.get_best_stars(pid, lvl_id)

        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint((mx, my))

        if not unlocked:
            pygame.draw.rect(surface, C_CARD_LCK, rect, border_radius=20)
            pygame.draw.rect(surface, C_BORDER, rect, 1, border_radius=20)

            arc_rect = pygame.Rect(rect.centerx - 12, rect.centery - 28, 24, 28)
            pygame.draw.arc(surface, (180, 190, 200), arc_rect, 0, math.pi, 5)
            pygame.draw.arc(surface, (230, 240, 250), arc_rect.inflate(-2, -2), 0, math.pi, 2)

            body_r = pygame.Rect(rect.centerx - 20, rect.centery - 12, 40, 32)
            pygame.draw.rect(surface, (0, 0, 0, 20), body_r.move(0, 3), border_radius=6)
            pygame.draw.rect(surface, (200, 150, 40), body_r, border_radius=6)
            pygame.draw.rect(surface, (240, 190, 75), body_r.inflate(-4,-4), border_radius=4)

            pygame.draw.circle(surface, (50, 40, 30), (rect.centerx, rect.centery), 4)
            pygame.draw.rect(surface, (50, 40, 30), (rect.centerx - 2, rect.centery, 4, 8), border_radius=1)

            txt(surface, f"Level {lvl_id}", rect.centerx, rect.centery + 28, 11, C_SUB, center=True, bold=True)
            return

        lift = 6 if hovered else 0
        px, py = 0.0, 0.0
        if hovered:
            px, py = (mx - rect.centerx) * 0.08, (my - rect.centery) * 0.08

        sh = pygame.Surface((rect.w + 30, rect.h + 30), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 10), (0, 0, rect.w + 30, rect.h + 30), border_radius=28)
        surface.blit(sh, (rect.x - 15, rect.y + 10 - lift))

        c_sh = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
        pygame.draw.rect(c_sh, (*cfg["color"], 60 if hovered else 15), (0, 0, rect.w + 20, rect.h + 20), border_radius=28)
        surface.blit(c_sh, (rect.x - 10, rect.y + 5 - lift))

        draw_rect = rect.move(0, -lift)
        pygame.draw.rect(surface, cfg["bg"], draw_rect, border_radius=20)
        pygame.draw.rect(surface, cfg["color"] if hovered else C_BORDER, draw_rect, width=2 if hovered else 1, border_radius=20)

        hl = pygame.Surface((draw_rect.w - 8, 2), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 100))
        surface.blit(hl, (draw_rect.x + 4, draw_rect.y + 2))

        badge_r = pygame.Rect(draw_rect.x + 16 + px, draw_rect.y + 18 + py, 42, 42)
        pygame.draw.rect(surface, cfg["color"], badge_r, border_radius=12)
        txt(surface, str(lvl_id), badge_r.centerx, badge_r.centery, 20, WHITE, bold=True, center=True)

        txt(surface, f"Level {lvl_id:02d}", draw_rect.x + 70 + px, draw_rect.y + 22 + py, 16, C_TEXT, bold=True)
        txt(surface, ld["title"].title(), draw_rect.x + 70 + px, draw_rect.y + 44 + py, 11, C_SUB)

        if best >= 0:
            # Use the stored star count (from cache or backend), never re-derive from score
            stars = _best_stars if _best_stars > 0 else 1
            draw_stars(surface, stars, draw_rect.centerx + px, draw_rect.bottom - 30 + py, size=17)
            txt(surface, f"Best: {best}", draw_rect.centerx + px, draw_rect.bottom - 54 + py, 11, cfg["color_dk"], center=True, bold=True)
        else:
            pb = pygame.Rect(draw_rect.centerx - 48 + px, draw_rect.bottom - 44 + py, 96, 32)
            pb_color = (60, 80, 100) if hovered else HEADING_COLOR
            pygame.draw.rect(surface, pb_color, pb, border_radius=12)
            if hovered:
                gl = pygame.Surface((pb.w + 12, pb.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(gl, (*pb_color, 80), (0, 0, pb.w + 12, pb.h + 12), border_radius=14)
                surface.blit(gl, (pb.x - 6, pb.y - 6))
            txt(surface, "Play", pb.centerx, pb.centery, 12, WHITE, bold=True, center=True)

    def _draw_toast(self, surface):
        if self.msg_t <= 0: return
        alpha = int(min(255, self.msg_t * 200))
        tw, th = 380, 46
        s = pygame.Surface((tw, th), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, alpha), (0, 0, tw, th), border_radius=14)
        tsh = pygame.Surface((tw + 20, th + 20), pygame.SRCALPHA)
        pygame.draw.rect(tsh, (0, 0, 0, min(20, alpha)), (0, 0, tw + 20, th + 20), border_radius=20)
        surface.blit(tsh, (self.W // 2 - tw // 2 - 10, self.H - 86))
        pygame.draw.rect(s, (255, 160, 180, alpha), (0, 0, tw, th), 2, border_radius=14)
        surface.blit(s, (self.W // 2 - tw // 2, self.H - 76))
        txt(surface, self.msg, self.W // 2, self.H - 54, 13, (220, 50, 80), center=True, bold=True)