# ============================================================
#  frontend/screens/game_screen.py
#  Main gameplay: images side by side, HUD, particles, hint
#  ENHANCED: Cinematic Day/Night, Fluid Birds, Polished UI
# ============================================================
import pygame, math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ui_config import C, txt, rounded_box, button, draw_stars, font, glow_circle, draw_transition, draw_help_overlay
from game_engine import GameState, Level

HUD = 90  # Slightly taller HUD for better breathing room

# ── Day / Night Theme Palettes ─────────────────────────────
P_DAY = {
    "hud_bg":   (255, 255, 255),
    "text":     (45,  45,  72),
    "sub":      (130, 130, 150),
    "border":   (230, 225, 240),
    "purple":   (124, 92,  191),
    "timer_bg": (245, 243, 250),
}

P_NIGHT = {
    "hud_bg":   (18,  20,  50),
    "text":     (215, 220, 255),
    "sub":      (130, 135, 185),
    "border":   (45,  48,  95),
    "purple":   (168, 130, 255),
    "timer_bg": (25,  28,  65),
}

P_GAME = dict(P_DAY)

def _lerp_col(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def _get_cinematic_bg(t):
    if t < 0.5:
        progress = t * 2.0
        return _lerp_col((235, 245, 255), (255, 140, 100), progress)
    else:
        progress = (t - 0.5) * 2.0
        return _lerp_col((255, 140, 100), (10, 12, 32), progress)

def _load_sound(filename):
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "assets", "sounds", filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"[GameScreen] Could not load sound '{filename}': {e}")
        return None


# ============================================================
# Particle Classes
# ============================================================
class TorchParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-2.0, -0.5)
        self.radius = random.uniform(5, 9)
        self.life = 255.0
        self.decay = random.uniform(8.0, 15.0)

    def update(self, dt):
        f = dt * 60.0
        self.x += self.vx * f
        self.y += self.vy * f
        self.vx *= (0.95 ** f)
        self.radius -= 0.15 * f
        self.life -= self.decay * f

    def draw(self, surface):
        if self.radius <= 0 or self.life <= 0: return
        if self.life > 200:   color = (255, 255, 200)
        elif self.life > 140: color = (255, 200, 50)
        elif self.life > 80:  color = (255, 100, 10)
        else:                 color = (150, 20, 0)
        surf_size = int(self.radius * 2)
        if surf_size <= 0: return
        ps = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        alpha = max(0, min(255, int(self.life)))
        pygame.draw.circle(ps, (*color, alpha), (int(self.radius), int(self.radius)), int(self.radius))
        surface.blit(ps, (int(self.x - self.radius), int(self.y - self.radius)), special_flags=pygame.BLEND_RGBA_ADD)

class Particle:
    def __init__(self, x, y, correct):
        ang = random.uniform(0, math.pi*2)
        spd = random.uniform(2, 6)
        self.x, self.y = x, y
        self.vx = math.cos(ang)*spd
        self.vy = math.sin(ang)*spd - random.uniform(1, 3)
        self.life = 1.0
        self.decay = random.uniform(1.5, 3.0)
        self.r = random.randint(3, 8)
        if correct:
            self.col = random.choice([(93,211,158), (181,234,215), (70,190,140)])
        else:
            self.col = random.choice([(255,107,138), (255,148,168), (240,110,140)])

    def update(self, dt):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 8*dt
        self.life -= self.decay*dt

    def draw(self, s):
        if self.life <= 0: return
        a = max(0, int(self.life*255))
        surf = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.col, a), (self.r, self.r), self.r)
        s.blit(surf, (int(self.x-self.r), int(self.y-self.r)))

class Ring:
    def __init__(self, x, y, col):
        self.x, self.y = x, y
        self.col = col
        self.t = 0.0

    def update(self, dt): self.t += dt*2.5

    @property
    def done(self): return self.t >= 1.0

    def draw(self, s):
        if self.done: return
        r = int(10 + 50*self.t)
        a = max(0, int((1-self.t)*220))
        surf = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.col, a), (r+2, r+2), r, 3)
        s.blit(surf, (self.x-r-2, self.y-r-2))

class HintPulse:
    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r
        self.t = 0.0

    @property
    def done(self): return self.t >= 1.0

    def update(self, dt): self.t += dt*0.35

    def draw(self, s, ox, oy, scale):
        if self.done: return
        scx = int(ox + self.cx*scale)
        scy = int(oy + self.cy*scale)
        sr  = max(1, int(self.r*scale*(3.0 - 2.0*self.t)))
        a   = int(abs(math.sin(self.t*math.pi*5))*200+30)
        surf = pygame.Surface((sr*2+6, sr*2+6), pygame.SRCALPHA)
        dashes = 12
        for i in range(dashes):
            ang = i*(math.pi*2/dashes) + self.t*3
            x1 = int(sr+3 + (sr-4)*math.cos(ang))
            y1 = int(sr+3 + (sr-4)*math.sin(ang))
            x2 = int(sr+3 + sr*math.cos(ang))
            y2 = int(sr+3 + sr*math.sin(ang))
            pygame.draw.line(surf, (124,92,191,a), (x1,y1), (x2,y2), 3)
        s.blit(surf, (scx-sr-3, scy-sr-3))


# ============================================================
# UPDATED: Fluid Birds (Organic, Non-Linear Path, Max 6)
# ============================================================
class Bird:
    def __init__(self, W, H, y_range=(HUD+15, HUD+80)):
        self.W = W
        self.H = H
        self.y_range = y_range
        self._reset(initial=True)

    def _reset(self, initial=False):
        y_min, y_max = self.y_range
        if y_max <= y_min + 4:
            y_max = y_min + 20
        self.base_y     = random.uniform(y_min, y_max)
        self.speed      = random.uniform(70, 110) # Slower, organic speed
        self.flap_t     = random.uniform(0, math.pi * 2)
        self.flap_speed = random.uniform(5, 9)
        self.size       = random.uniform(6, 12)
        self.direction  = random.choice([1, -1])
        
        # Two offsets for a composite sine wave making a more swooping, complex path
        self.y_offset_t1 = random.uniform(0, math.pi * 2)
        self.y_offset_t2 = random.uniform(0, math.pi * 2)
        
        if initial:
            self.x = random.uniform(0, self.W)
        else:
            self.x = -self.size * 5 if self.direction == 1 else self.W + self.size * 5

    def update(self, dt):
        self.x += self.speed * self.direction * dt
        self.flap_t += self.flap_speed * dt
        self.y_offset_t1 += dt * 0.9
        self.y_offset_t2 += dt * 0.4
        
        # Non-linear, complex swooping path using composite waves
        wave1 = math.sin(self.y_offset_t1) * 12.0
        wave2 = math.cos(self.y_offset_t2) * 18.0
        self.y = self.base_y + wave1 + wave2
        
        if self.direction == 1 and self.x > self.W + 70:
            self._reset()
        elif self.direction == -1 and self.x < -70:
            self._reset()

    def draw(self, surface, alpha):
        if alpha < 6: return
        flap = math.sin(self.flap_t) * self.size * 0.4 
        cx, cy = int(self.x), int(self.y)
        s      = self.size
        bw     = int(s * 4 + 6)
        bh     = int(s * 2 + abs(flap) + 8)
        bs     = pygame.Surface((bw, bh), pygame.SRCALPHA)
        ox, oy = bw // 2, bh // 2
        col    = (40, 40, 55, int(min(255, alpha)))
        thick  = max(1, int(s * 0.28))
        
        p_l = [(ox, oy), (ox - int(s*1.2), oy - int(flap*0.8)), (ox - int(s*2.2), oy + int(flap*0.2))]
        p_r = [(ox, oy), (ox + int(s*1.2), oy - int(flap*0.8)), (ox + int(s*2.2), oy + int(flap*0.2))]
        
        pygame.draw.lines(bs, col, False, p_l, thick)
        pygame.draw.lines(bs, col, False, p_r, thick)
        surface.blit(bs, (cx - bw // 2, cy - bh // 2))

# ============================================================
# Twinkling Star
# ============================================================
class TwinklingStar:
    def __init__(self, x, y):
        self.x            = x
        self.y            = y
        self.t            = random.uniform(0, math.pi * 2)
        self.twinkle_spd  = random.uniform(1.4, 4.8)
        self.base_r       = random.uniform(0.7, 2.4)
        self.base_alpha   = random.uniform(110, 235)
        self.cross        = self.base_r > 1.4

    def update(self, dt):
        self.t += self.twinkle_spd * dt

    def draw(self, surface, visibility):
        if visibility < 0.03:
            return
        brightness = 0.45 + 0.55 * abs(math.sin(self.t))
        a = int(self.base_alpha * visibility * brightness)
        if a < 6: return
        r  = max(0.5, self.base_r * (0.82 + 0.18 * brightness))
        ri = max(1, int(r))
        ss = ri * 4 + 6
        st = pygame.Surface((ss, ss), pygame.SRCALPHA)
        sc = ss // 2
        pygame.draw.circle(st, (255, 255, 230, a), (sc, sc), ri)
        if self.cross and ri >= 2:
            arm = int(ri * 2.0)
            lc  = (255, 255, 230, a // 3)
            pygame.draw.line(st, lc, (sc, sc - arm), (sc, sc + arm), 1)
            pygame.draw.line(st, lc, (sc - arm, sc), (sc + arm, sc), 1)
        surface.blit(st, (int(self.x) - ss // 2, int(self.y) - ss // 2))

# ============================================================
# Magnifier Renderer
# ============================================================
class MagnifierRenderer:
    def __init__(self, zoom_radius: int = 60, zoom_factor: float = 1.7):
        self.zoom_radius = zoom_radius
        self.zoom_factor = zoom_factor
        self._lens_cache = {}

    def draw(self, surface, world, mx, my):
        self._blit_zoom(surface, world, mx, my)
        self._blit_lens(surface, mx, my, self.zoom_radius)

    def _blit_zoom(self, dst, world, mx, my):
        r      = self.zoom_radius
        zf     = self.zoom_factor
        src_r  = int(r / zf)
        diam   = r * 2
        src_rect = pygame.Rect(mx - src_r, my - src_r, src_r * 2, src_r * 2)
        src_surf = pygame.Surface((src_r * 2, src_r * 2))
        src_surf.fill((248, 250, 252))
        src_surf.blit(world, (0, 0), src_rect)
        zoomed = pygame.transform.smoothscale(src_surf, (diam, diam)).convert_alpha()
        mask   = pygame.Surface((diam, diam), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
        mask.blit(zoomed, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        dst.blit(mask, (mx - r, my - r))

    def _blit_lens(self, dst, cx, cy, r):
        if r not in self._lens_cache:
            self._lens_cache[r] = self._build_lens(r)
        lens_surf, lcx, lcy = self._lens_cache[r]
        dst.blit(lens_surf, (cx - lcx, cy - lcy))

    def _build_lens(self, r):
        size  = int(r * 2 + r * 2.5)
        surf  = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        lcx, lcy = r + 15, r + 15
        angle    = math.radians(45)
        handle_len = int(r * 1.5)
        handle_w   = int(r * 0.4)
        hw = handle_w // 2
        hx1 = lcx + math.cos(angle) * (r - 2)
        hy1 = lcy + math.sin(angle) * (r - 2)
        hx2 = lcx + math.cos(angle) * (r + handle_len)
        hy2 = lcy + math.sin(angle) * (r + handle_len)
        pygame.draw.line(surf, (40, 40, 45), (hx1, hy1), (hx2, hy2), handle_w)
        pygame.draw.circle(surf, (40, 40, 45), (int(hx1), int(hy1)), hw)
        pygame.draw.circle(surf, (40, 40, 45), (int(hx2), int(hy2)), hw)
        pygame.draw.line(surf, (70, 70, 75), (hx1, hy1), (hx2, hy2), max(2, handle_w // 3))
        collar_x = lcx + math.cos(angle) * r
        collar_y = lcy + math.sin(angle) * r
        pygame.draw.circle(surf, (140, 140, 150), (int(collar_x), int(collar_y)), int(handle_w * 0.75))
        pygame.draw.circle(surf, (50, 50, 60),   (int(collar_x), int(collar_y)), int(handle_w * 0.75), 2)
        ring_w = max(4, r // 7)
        pygame.draw.circle(surf, (50, 50, 55),   (lcx, lcy), r + ring_w + 1, ring_w + 2)
        pygame.draw.circle(surf, (200, 205, 215), (lcx, lcy), r + ring_w,    ring_w)
        pygame.draw.circle(surf, (100, 100, 110), (lcx, lcy), r + 2, 2)
        glare  = pygame.Surface((size, size), pygame.SRCALPHA)
        glare.fill((0, 0, 0, 0))
        pygame.draw.circle(glare, (255, 255, 255, 50), (lcx, lcy), r - 2)
        cutout = pygame.Surface((size, size), pygame.SRCALPHA)
        cutout.fill((255, 255, 255, 255))
        pygame.draw.circle(cutout, (255, 255, 255, 0), (lcx + 6, lcy + 6), r - 2)
        glare.blit(cutout, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(glare, (0, 0))
        pygame.draw.circle(surf, (255, 255, 255, 80), (lcx + r//2, lcy + r//2), r//8)
        return surf, lcx, lcy

# ============================================================
# Main Screen Class
# ============================================================
class GameScreen:
    HEARTBEAT_THRESHOLD = 20.0

    def __init__(self, app):
        self.app       = app
        self.W, self.H = app["W"], app["H"]
        self.gs        = GameState()
        self.loaded_id = None

        self.img1 = self.img2 = None
        self.img1s = self.img2s = None
        self.scale = 1.0
        self.dw = self.dh = 0
        self.x1 = self.x2 = self.iy = 0

        self.particles = []
        self.rings     = []
        self.hint_pulse = None
        self.shake_t   = 0.0
        self.shake_amp = 0.0
        self.torch_particles = []

        self.screen_t = 0.0
        self._shake_surf = pygame.Surface((self.W, self.H))

        self._snd_heartbeat = _load_sound("heartbeat.wav")
        self._heartbeat_playing = False
        self._snd_correct = _load_sound("correct.wav")

        self.flashlight_active = False
        self.flash_radius = 80
        self.halo_width   = 40
        self.total_radius = self.flash_radius + self.halo_width
        self.flash_hole   = pygame.Surface((self.total_radius * 2, self.total_radius * 2), pygame.SRCALPHA)
        for r in range(self.total_radius, 0, -1):
            if r > self.flash_radius:
                ratio     = (r - self.flash_radius) / self.halo_width
                alpha_sub = int(100 * (1 - ratio))
            else:
                ratio     = r / self.flash_radius
                alpha_sub = 100 + int(155 * (1 - ratio**1.5))
            pygame.draw.circle(self.flash_hole, (0, 0, 0, alpha_sub), (self.total_radius, self.total_radius), r)

        self.magnifier_active = False
        self._magnifier  = MagnifierRenderer(zoom_radius=60, zoom_factor=1.7)
        self._world_snap = pygame.Surface((self.W, self.H))

        # ── Button Layout (bottom bar) ──
        BH = 44
        BY = self.H - 56

        self.btn_pause   = pygame.Rect(14,   BY, 110, BH)
        self.btn_hint    = pygame.Rect(134,  BY, 120, BH)
        self.btn_freeze  = pygame.Rect(264,  BY, 130, BH)
        self.btn_flash   = pygame.Rect(404,  BY, 120, BH)
        self.btn_magnify = pygame.Rect(534,  BY, 130, BH)

        _ICON = 44
        self.btn_mute    = pygame.Rect(676, BY, _ICON, BH)
        self.slider_rect = pygame.Rect(726, BY + 16, 170, 11)
        self.dragging_slider = False

        self.btn_quit  = pygame.Rect(self.W - 154, BY, 140, BH)
        
        # Shifted How To Play upward, perfectly aligned to the right-side gap of the header
        self.btn_howto = pygame.Rect(self.W - 135, 28, 120, 34)

        self._hover_delay  = 0.0
        self._slider_alpha = 0.0

        # ──────────────────────────────────────────────────────
        # DAY / NIGHT THEME STATE & ALIGNMENTS
        # ──────────────────────────────────────────────────────
        self.theme_t = 0.0           

        self._trans_active   = False
        self._trans_progress = 0.0   
        self._trans_start    = 0.0   
        self._trans_target   = 0.0   
        self._trans_speed    = 0.35  

        self._cel_y_base   = 45       
        self._sun_anim_x   = 70       
        self._moon_anim_x  = self.W + 70
        self._sun_start_x  = 70
        self._sun_end_x    = 70
        self._moon_start_x = self.W + 70
        self._moon_end_x   = self.W + 70
        self._sun_anim_y   = self._cel_y_base
        self._moon_anim_y  = self._cel_y_base

        self._ray_t = 0.0

        upper_yr = (HUD + 8,  HUD + 55)
        lower_yr = (self.H - 118, self.H - 82)
        # Reduced max birds to 6 (3 in upper region, 3 in lower region)
        self._birds_upper = [Bird(self.W, self.H, upper_yr) for _ in range(3)]
        self._birds_lower = [Bird(self.W, self.H, lower_yr) for _ in range(3)]

        self._stars = []
        for _ in range(120):
            sx = random.uniform(0, self.W)
            sy = random.uniform(HUD + 2, self.H - 72)
            self._stars.append(TwinklingStar(sx, sy))

    def _get_c(self, key):
        return _lerp_col(P_DAY[key], P_NIGHT[key], self.theme_t)

    def _start_theme_transition(self, target):
        if self._trans_active and abs(self._trans_target - target) < 0.01: return
        self._trans_active   = True
        self._trans_progress = 0.0
        self._trans_start    = self.theme_t
        self._trans_target   = target

        going_night = target > 0.5
        if going_night:
            self._sun_start_x  = self._sun_anim_x
            self._sun_end_x    = -150
            self._moon_start_x = self._moon_anim_x
            self._moon_end_x   = 70
        else:
            self._moon_start_x = self._moon_anim_x
            self._moon_end_x   = self.W + 150
            self._sun_start_x  = self._sun_anim_x
            self._sun_end_x    = 70

    def _start_heartbeat(self):
        if not self._heartbeat_playing and self._snd_heartbeat:
            audio = self.app["audio"]
            self._snd_heartbeat.set_volume(audio.sfx_volume)
            self._snd_heartbeat.play(loops=-1)
            self._heartbeat_playing = True

    def _stop_heartbeat(self):
        if self._heartbeat_playing and self._snd_heartbeat:
            self._snd_heartbeat.stop()
            self._heartbeat_playing = False

    def _make_placeholder(self, label, path):
        s = pygame.Surface((800, 500))
        s.fill((240, 235, 250))
        for x in range(0, 800, 50): pygame.draw.line(s, (255,255,255), (x,0), (x,500))
        for y in range(0, 500, 50): pygame.draw.line(s, (255,255,255), (0,y), (800,y))
        f1 = pygame.font.SysFont("Segoe UI", 22, bold=True)
        f2 = pygame.font.SysFont("Segoe UI", 15)
        t1 = f1.render(label, True, P_DAY["purple"])
        t2 = f2.render(f"Add image: {path}", True, P_DAY["sub"])
        s.blit(t1, (400-t1.get_width()//2, 210))
        s.blit(t2, (400-t2.get_width()//2, 250))
        return s

    def _load_level(self, lvl_id):
        level           = Level(lvl_id)
        self.gs.start(level)
        self.loaded_id  = lvl_id
        self.particles  = []
        self.rings      = []
        self.hint_pulse = None
        self.shake_t    = 0.0
        self.shake_amp  = 0.0
        self.screen_t   = 0.0
        self.flashlight_active = False
        self.magnifier_active  = False
        self.torch_particles   = []
        pygame.mouse.set_visible(True)
        self._stop_heartbeat()

        def load_img(path, label):
            base     = os.path.dirname(os.path.dirname(__file__))
            filename = os.path.basename(path)
            abs_path = os.path.join(base, "assets", "levels", filename)
            try:
                if os.path.exists(abs_path): return pygame.image.load(abs_path).convert_alpha()
                elif os.path.exists(path):   return pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[GameScreen] Error loading image: {e}")
            return self._make_placeholder(label, path)

        self.img1 = load_img(level.img1_path, f"Image 1 — Level {lvl_id}")
        self.img2 = load_img(level.img2_path, f"Image 2 — Level {lvl_id}")
        self._compute_layout()

        upper_yr = (HUD + 8, max(HUD + 20, self.iy - 12))
        lower_yr = (min(self.H - 118, self.iy + self.dh + 12), self.H - 82)
        for b in self._birds_upper:
            b.y_range = upper_yr
            b._reset(initial=True)
        for b in self._birds_lower:
            b.y_range = lower_yr
            b._reset(initial=True)

    def _compute_layout(self):
        half_w   = self.W // 2 - 12
        avail_h  = self.H - HUD - 66
        sx       = half_w / self.img1.get_width()
        sy       = avail_h / self.img1.get_height()
        self.scale = min(sx, sy)
        self.dw  = int(self.img1.get_width()  * self.scale)
        self.dh  = int(self.img1.get_height() * self.scale)
        self.x1  = (self.W//2 - self.dw) // 2
        self.x2  = self.W//2 + (self.W//2 - self.dw)//2
        self.iy  = HUD + (avail_h - self.dh)//2
        self.img1s = pygame.transform.scale(self.img1, (self.dw, self.dh))
        self.img2s = pygame.transform.scale(self.img2, (self.dw, self.dh))

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONUP:
                self.dragging_slider = False

            if e.type == pygame.MOUSEMOTION and self.dragging_slider:
                self._update_volume_from_slider(e.pos[0])

            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.slider_rect.inflate(0, 24).collidepoint(e.pos):
                    if self._slider_alpha > 0:
                        self.dragging_slider = True
                        self._update_volume_from_slider(e.pos[0])
                self._on_click(e.pos)

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if   self.gs.phase == "playing":     self.gs.pause()
                    elif self.gs.phase == "paused":      self.gs.resume()
                    elif self.gs.phase == "how_to_play": self.gs.close_how_to_play()
                if e.key == pygame.K_h: self._do_hint()
                if e.key == pygame.K_p:
                    if   self.gs.phase == "playing": self.gs.pause()
                    elif self.gs.phase == "paused":  self.gs.resume()

    def _on_click(self, pos):
        if (math.hypot(pos[0] - self._sun_anim_x, pos[1] - self._sun_anim_y) < 60
                and self._sun_anim_x > -60 and self.theme_t < 0.85):
            self._start_theme_transition(1.0)
            return

        if (math.hypot(pos[0] - self._moon_anim_x, pos[1] - self._moon_anim_y) < 60
                and self._moon_anim_x < self.W + 60 and self.theme_t > 0.15):
            self._start_theme_transition(0.0)
            return

        if self.btn_pause.collidepoint(pos):
            if   self.gs.phase == "playing": self.gs.pause()
            elif self.gs.phase == "paused":  self.gs.resume()
            return

        if self.btn_howto.collidepoint(pos):
            if   self.gs.phase == "playing":     self.gs.open_how_to_play()
            elif self.gs.phase == "how_to_play": self.gs.close_how_to_play()
            return

        if self.gs.phase == "how_to_play":
            htp_btn = getattr(self, "_htp_close_btn", None)
            if htp_btn and htp_btn.collidepoint(pos):
                self.gs.close_how_to_play()
            return

        if self.btn_hint.collidepoint(pos):   self._do_hint();   return
        if self.btn_freeze.collidepoint(pos): self._do_freeze(); return

        if self.btn_flash.collidepoint(pos):
            self.flashlight_active = not self.flashlight_active
            if self.flashlight_active:
                self.magnifier_active = False
            return

        if self.btn_magnify.collidepoint(pos):
            self.magnifier_active = not self.magnifier_active
            if self.magnifier_active:
                self.flashlight_active = False
            return

        if self.btn_mute.collidepoint(pos) and not self.dragging_slider:
            audio = self.app["audio"]
            audio.toggle_mute()
            # Heartbeat keeps playing at sfx_volume — no change needed
            return

        if self.btn_quit.collidepoint(pos):
            self._stop_heartbeat()
            pygame.mouse.set_visible(True)
            self.app["current"] = "level_select"
            self.loaded_id = None
            return

        if self.gs.phase != "playing": return

        ix, iy_rel = self._to_img(pos)
        if ix is None: return

        if self.flashlight_active:
            original_radii = [r.radius for r in self.gs.regions]
            for r in self.gs.regions: r.radius = min(r.radius, 15)

        correct = self.gs.check_click(int(ix), int(iy_rel))

        if correct and self._snd_correct:
            audio = self.app["audio"]
            self._snd_correct.set_volume(audio.sfx_volume)
            self._snd_correct.play()

        if self.flashlight_active:
            for i, r in enumerate(self.gs.regions): r.radius = original_radii[i]

        for _ in range(22 if correct else 12):
            self.particles.append(Particle(pos[0], pos[1], correct))

        col = (93,211,158) if correct else (255,107,138)
        self.rings.append(Ring(pos[0], pos[1], col))

        if not correct:
            self.shake_t   = 0.75
            self.shake_amp = 10

        if self.gs.phase == "win":
            self.app["audio"].pause_music()
            self._stop_heartbeat()
            self._save_and_go("win")
        elif self.gs.phase == "lose":
            self.app["audio"].pause_music()
            self._stop_heartbeat()
            self._save_and_go("lose")

    def _update_volume_from_slider(self, mouse_x):
        rel_x = mouse_x - self.slider_rect.x
        pct   = max(0.0, min(1.0, rel_x / self.slider_rect.w))
        self.app["audio"].set_music_volume(pct)

    def _draw_audio_controls(self, surface):
        audio       = self.app["audio"]
        btn         = self.btn_mute
        sr          = self.slider_rect
        mx, my      = pygame.mouse.get_pos()
        hov_btn     = btn.collidepoint(mx, my)
        btn_cx, btn_cy = btn.centerx, btn.centery
        btn_r       = btn.height // 2 - 1
        purple      = self._get_c("purple")

        if audio.muted:
            ring_col = (210, 55, 85);  icon_col = (210, 55, 85)
            wave_col = (210, 55, 85);  bg_col   = (255, 236, 240)
        else:
            ring_col = purple;         icon_col = purple
            wave_col = purple;         bg_col   = _lerp_col((237,232,255), (40,38,80), self.theme_t)

        if hov_btn: bg_col = tuple(max(0, c - 18) for c in bg_col)

        pygame.draw.circle(surface, bg_col,   (btn_cx, btn_cy), btn_r)
        pygame.draw.circle(surface, ring_col, (btn_cx, btn_cy), btn_r, 2)

        big_size = 60
        big_s    = pygame.Surface((big_size, big_size), pygame.SRCALPHA)
        pygame.draw.rect(big_s, icon_col, (14, 22, 10, 16), border_radius=4)
        cone_pts = [(22, 22), (40, 10), (40, 50), (22, 38)]
        pygame.draw.polygon(big_s, icon_col, cone_pts)
        if not audio.muted:
            pygame.draw.arc(big_s, wave_col, (24, 15, 30, 30), -math.pi/3, math.pi/3, 5)
            pygame.draw.arc(big_s, wave_col, (16, 5, 50, 50),  -math.pi/4, math.pi/4, 5)
        else:
            pygame.draw.line(big_s, (210, 55, 85), (44, 20), (56, 40), 6)
            pygame.draw.line(big_s, (210, 55, 85), (56, 20), (44, 40), 6)
        icon_s = pygame.transform.smoothscale(big_s, (24, 24))
        surface.blit(icon_s, (btn_cx - 12, btn_cy - 12))

        if self._slider_alpha <= 0: return

        alpha    = int(255 * self._slider_alpha)
        sw       = sr.right - btn.right + 14
        sh       = btn.height + 16
        slider_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        lx       = 6
        ly       = (sh - sr.height) // 2
        pill_bg  = (240, 236, 252) if not audio.muted else (250, 236, 240)
        pygame.draw.rect(slider_s, (*pill_bg, alpha), (0, 0, sw, sh), border_radius=14)
        pygame.draw.rect(slider_s, (*ring_col, min(alpha, 100)), (0, 0, sw, sh), 1, border_radius=14)
        pygame.draw.rect(slider_s, (210, 202, 234, alpha), (lx, ly, sr.width, sr.height), border_radius=6)
        fill_w = max(0, int(sr.width * audio.music_volume))
        if fill_w > 0:
            fc = purple if not audio.muted else (195, 155, 170)
            pygame.draw.rect(slider_s, (*fc, alpha), (lx, ly, fill_w, sr.height), border_radius=6)
        kx     = max(lx, min(lx + sr.width, lx + fill_w))
        ky     = ly + sr.height // 2
        kfill  = (255, 255, 255) if not audio.muted else (245, 225, 230)
        pygame.draw.circle(slider_s, (*kfill, alpha),   (kx, ky), 8)
        pygame.draw.circle(slider_s, (*ring_col, alpha), (kx, ky), 8, 2)
        lf  = pygame.font.SysFont("Segoe UI", 9, bold=True)
        lbl = lf.render("BGM", True, self._get_c("sub"))
        lbl.set_alpha(alpha)
        slider_s.blit(lbl, (sw // 2 - lbl.get_width() // 2, sh - lbl.get_height() - 1))
        surface.blit(slider_s, (btn.right + 2, btn.y - 8))

    def _do_hint(self):
        cat       = self.gs.level.category if self.gs.level else "easy"
        max_hints = 3 if cat == "easy" else (2 if cat == "medium" else 1)
        if self.gs.hints_used >= max_hints:
            self.shake_t   = 0.3
            self.shake_amp = 5
            return
        r = self.gs.use_hint()
        if r: self.hint_pulse = HintPulse(r.cx, r.cy, r.radius)

    def _do_freeze(self): self.gs.freeze()

    def _calc_stars(self, wrong_clicks):
        if wrong_clicks == 0:   return 3
        elif wrong_clicks <= 3: return 2
        else:                   return 1

    def _save_and_go(self, dest):
        pygame.mouse.set_visible(True)
        gs  = self.gs
        cat = gs.level.category if gs.level else "easy"
        if cat == "easy":
            base_pts = 150; time_factor = 0.5; wrong_pen = 30; hint_pen = 50; lives_bonus = 25
        elif cat == "medium":
            base_pts = 200; time_factor = 0.8; wrong_pen = 50; hint_pen = 75; lives_bonus = 40
        else:
            base_pts = 300; time_factor = 1.5; wrong_pen = 75; hint_pen = 100; lives_bonus = 60

        stars = self._calc_stars(gs.wrong_clicks)
        try:
            sc, _ = self.app["backend"].calc_score(
                gs.found_count(), len(gs.regions),
                gs.time_left, gs.level.time_limit,
                gs.wrong_clicks, gs.level.max_wrong, gs.hints_used)
        except:
            base_score = gs.found_count() * base_pts
            time_bonus = int(min(gs.time_left, gs.level.time_limit * 0.5) * time_factor)
            lives_end  = gs.lives * lives_bonus if dest == "win" else 0
            penalties  = (gs.wrong_clicks * wrong_pen) + (gs.hints_used * hint_pen)
            sc         = base_score + time_bonus + lives_end - penalties

        sc = max(10, int(sc)) if dest == "win" else max(0, int(sc))
        try:
            self.app["backend"].save_score(
                self.app["player_id"], gs.level.id, sc, stars,
                int(gs.level.time_limit - gs.time_left),
                gs.wrong_clicks, gs.hints_used)
        except: pass

        self.app["last_score"]   = sc
        self.app["last_stars"]   = stars
        self.app["game_result"]  = {"score": sc, "stars": stars, "level_id": gs.level.id}
        # Cache best stars locally so level select always shows correct star count
        if "best_stars_cache" not in self.app:
            self.app["best_stars_cache"] = {}
        _lvl_id = gs.level.id
        _prev_best = self.app["best_stars_cache"].get(_lvl_id, 0)
        self.app["best_stars_cache"][_lvl_id] = max(_prev_best, stars)
        self.app["current"]      = dest
        self.loaded_id           = None

    def _to_img(self, pos):
        sx, sy = pos
        for ox in [self.x1, self.x2]:
            if ox <= sx < ox+self.dw and self.iy <= sy < self.iy+self.dh:
                return (sx-ox)/self.scale, (sy-self.iy)/self.scale
        return None, None

    def update(self, dt):
        sel = self.app.get("selected_level")
        if sel and sel != self.loaded_id:
            self._load_level(sel)

        mx, my = pygame.mouse.get_pos()
        hover_zone  = pygame.Rect(self.btn_mute.x, self.btn_mute.y - 10,
                                  self.slider_rect.right - self.btn_mute.x + 10,
                                  self.btn_mute.height + 20)
        is_hovering = hover_zone.collidepoint((mx, my)) or self.dragging_slider
        if is_hovering:
            self._hover_delay += dt
            if self._hover_delay > 0.15:
                self._slider_alpha = min(1.0, self._slider_alpha + dt * 5.0)
        else:
            self._hover_delay  = 0.0
            self._slider_alpha = max(0.0, self._slider_alpha - dt * 3.0)

        vol = 0.0 if self.app.get("muted") else self.app.get("bgm_volume", 0.35)
        # NOTE: heartbeat and correct SFX are NOT tied to BGM mute — they always
        # play at sfx_volume so the player hears feedback even when BGM is muted.
        audio = self.app["audio"]
        if self._snd_heartbeat:
            self._snd_heartbeat.set_volume(audio.sfx_volume)
        if self._snd_correct:
            self._snd_correct.set_volume(audio.sfx_volume)

        self.screen_t += dt
        self.gs.tick(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update(dt)
        self.rings = [r for r in self.rings if not r.done]
        for r in self.rings: r.update(dt)

        if self.hint_pulse:
            self.hint_pulse.update(dt)
            if self.hint_pulse.done: self.hint_pulse = None

        if self.shake_t > 0: self.shake_t -= dt

        if self.gs.phase == "playing" and not self.gs.frozen:
            if self.gs.time_left <= self.HEARTBEAT_THRESHOLD: self._start_heartbeat()
            else: self._stop_heartbeat()
        else: self._stop_heartbeat()

        if self.flashlight_active and self.gs.phase == "playing":
            is_ui = (my < HUD) or (my > self.H - 75)
            if is_ui: pygame.mouse.set_visible(True)
            else:
                pygame.mouse.set_visible(False)
                for _ in range(4):
                    self.torch_particles.append(TorchParticle(
                        mx + random.uniform(-3, 3), my + 100 + random.uniform(-1.5, 1.5)))
        elif self.magnifier_active and self.gs.phase == "playing":
            is_ui = (my < HUD) or (my > self.H - 75)
            pygame.mouse.set_visible(is_ui)
        else:
            pygame.mouse.set_visible(True)

        for p in self.torch_particles: p.update(dt)
        self.torch_particles = [p for p in self.torch_particles if p.life > 0 and p.radius > 0]

        if self.gs.phase == "lose" and self.app["current"] == "game":
            self.app["audio"].pause_music()
            self._stop_heartbeat()
            self._save_and_go("lose")

        if self._trans_active:
            self._trans_progress += dt * self._trans_speed
            if self._trans_progress >= 1.0:
                self._trans_progress = 1.0
                self._trans_active   = False
                
            p = self._trans_progress
            sp = p * p * p * (p * (p * 6.0 - 15.0) + 10.0) 
            
            self.theme_t = self._trans_start + sp * (self._trans_target - self._trans_start)
            
            self._sun_anim_x  = self._sun_start_x  + sp * (self._sun_end_x  - self._sun_start_x)
            self._moon_anim_x = self._moon_start_x + sp * (self._moon_end_x - self._moon_start_x)
            
            arc_height = 50 
            if self._trans_target > 0.5: 
                self._sun_anim_y = self._cel_y_base + math.sin(sp * math.pi) * arc_height
                self._moon_anim_y = self._cel_y_base - math.sin(sp * math.pi) * arc_height * 0.5
            else: 
                self._moon_anim_y = self._cel_y_base + math.sin(sp * math.pi) * arc_height
                self._sun_anim_y = self._cel_y_base - math.sin(sp * math.pi) * arc_height * 0.5

        self._ray_t += dt * 0.65

        bird_vis = 1.0 - self.theme_t
        if bird_vis > 0.02:
            for b in self._birds_upper + self._birds_lower: b.update(dt)

        for s in self._stars: s.update(dt)

    def _draw_sun(self, surface, cx, cy):
        cx, cy = int(cx), int(cy)
        vis    = max(0.0, min(1.0, 1.0 - self.theme_t))
        if vis < 0.02 or cx < -120 or cx > self.W + 120: return

        radius = 35   # was 45 — shrunk so it fits neatly in the HUD strip
        for layer in range(4):
            gr  = radius + 28 - layer * 7
            ga  = int((10 - layer * 2) * vis)
            if ga < 2: continue
            gs2 = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs2, (255, 180, 50, ga), (gr, gr), gr)
            surface.blit(gs2, (cx - gr, cy - gr))

        num_rays = 12
        ray_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for i in range(num_rays):
            ang     = self._ray_t + i * (math.pi * 2 / num_rays)
            inner_r = radius + 5
            outer_r = radius + (14 if i % 2 == 0 else 8)
            x1 = int(cx + math.cos(ang) * inner_r)
            y1 = int(cy + math.sin(ang) * inner_r)
            x2 = int(cx + math.cos(ang) * outer_r)
            y2 = int(cy + math.sin(ang) * outer_r)
            ray_a  = int(140 * vis)
            thick  = 3 if i % 2 == 0 else 2
            pygame.draw.line(ray_surf, (255, 200, 40, ray_a), (x1, y1), (x2, y2), thick)
        surface.blit(ray_surf, (0, 0))

        pygame.draw.circle(surface, _lerp_col((255, 170, 40), (255, 230, 80), 0.5), (cx, cy), radius)
        pygame.draw.circle(surface, (255, 245, 120), (cx, cy), radius - 5)

        hl = pygame.Surface((radius, radius), pygame.SRCALPHA)
        pygame.draw.circle(hl, (255, 255, 255, int(120 * vis)), (radius//2, radius//2), radius//2)
        surface.blit(hl, (cx - int(radius*0.7), cy - int(radius*0.7)))

    def _draw_moon(self, surface, cx, cy):
        cx, cy = int(cx), int(cy)
        vis    = max(0.0, min(1.0, self.theme_t))
        if vis < 0.02 or cx < -120 or cx > self.W + 120: return

        radius = 45 
        for layer in range(4):
            gr  = radius + 40 - layer * 10
            ga  = int((10 - layer * 2) * vis)
            if ga < 2: continue
            gs2 = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs2, (180, 190, 255, ga), (gr, gr), gr)
            surface.blit(gs2, (cx - gr, cy - gr))

        ms   = radius * 2 + 16
        moon = pygame.Surface((ms, ms), pygame.SRCALPHA)
        mcx  = ms // 2
        pygame.draw.circle(moon, (210, 218, 255, int(255 * vis)), (mcx, mcx), radius)
        pygame.draw.circle(moon, (0, 0, 0, 0), (mcx + 18, mcx - 8), radius - 8)
        surface.blit(moon, (cx - ms // 2, cy - ms // 2))

        for cr_x, cr_y, cr_r, cr_a in [(-12, 12, 8, 55), (-22, -6, 5, 40), (4, -14, 4, 35), (-8, -20, 3, 30)]:
            csurf = pygame.Surface((cr_r*2+2, cr_r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(csurf, (175, 185, 230, int(cr_a * vis)), (cr_r+1, cr_r+1), cr_r)
            surface.blit(csurf, (cx + cr_x - cr_r, cy + cr_y - cr_r))

    def _draw_background_elements(self, surface):
        day_vis   = 1.0 - self.theme_t
        night_vis = self.theme_t
        if night_vis > 0.02:
            for star in self._stars: star.draw(surface, night_vis)
        if day_vis > 0.02:
            bird_alpha = int(200 * day_vis)
            for b in self._birds_upper + self._birds_lower: b.draw(surface, bird_alpha)

    def draw(self, surface):
        target = self._shake_surf
        bg_col = _get_cinematic_bg(self.theme_t)
        target.fill(bg_col)

        self._draw_sun(target, self._sun_anim_x, self._sun_anim_y)
        self._draw_moon(target, self._moon_anim_x, self._moon_anim_y)
        self._draw_background_elements(target)

        if not self.img1s:
            surface.blit(target, (0, 0))
            return

        panel_col   = _lerp_col((255, 255, 255), (22, 25, 58), self.theme_t)
        border_col  = self._get_c("border")

        for ox in [self.x1, self.x2]:
            pygame.draw.rect(target, panel_col,  (ox-10, self.iy-10, self.dw+20, self.dh+20), border_radius=12)
            pygame.draw.rect(target, border_col, (ox-10, self.iy-10, self.dw+20, self.dh+20), width=2, border_radius=12)

        target.blit(self.img1s, (self.x1, self.iy))
        target.blit(self.img2s, (self.x2, self.iy))

        label_y = HUD + max(14, (self.iy - HUD) // 2)
        text_c  = self._get_c("text")
        txt(target, "ORIGINAL", self.x1 + self.dw//2, label_y, 20, text_c, center=True, bold=True)
        txt(target, "MODIFIED", self.x2 + self.dw//2, label_y, 20, text_c, center=True, bold=True)

        for r in self.gs.regions:
            if not r.found: continue
            for ox in [self.x1, self.x2]:
                cx = int(ox + r.cx*self.scale)
                cy = int(self.iy + r.cy*self.scale)
                rr = max(1, int(r.radius*self.scale))
                s  = pygame.Surface((rr*2+4, rr*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (93,211,158,50),  (rr+2,rr+2), rr)
                pygame.draw.circle(s, (93,211,158,220), (rr+2,rr+2), rr, 3)
                target.blit(s, (cx-rr-2, cy-rr-2))
                txt(target, "✓", cx, cy, max(12,rr), (255,255,255), bold=True, center=True)

        if self.hint_pulse:
            for ox in [self.x1, self.x2]: self.hint_pulse.draw(target, ox, self.iy, self.scale)

        for r in self.rings:     r.draw(target)
        for p in self.particles: p.draw(target)

        if self.flashlight_active:
            dark = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 255))
            mx, my = pygame.mouse.get_pos()
            rel_x = mx - self.x1 if mx < self.W // 2 else mx - self.x2
            center_left  = (self.x1 + rel_x, my)
            center_right = (self.x2 + rel_x, my)
            dark.blit(self.flash_hole, (center_left[0]  - self.total_radius, center_left[1]  - self.total_radius), special_flags=pygame.BLEND_RGBA_SUB)
            dark.blit(self.flash_hole, (center_right[0] - self.total_radius, center_right[1] - self.total_radius), special_flags=pygame.BLEND_RGBA_SUB)
            target.blit(dark, (0, 0))

        if self.magnifier_active and self.gs.phase == "playing":
            mx, my = pygame.mouse.get_pos()
            if not ((my < HUD) or (my > self.H - 75)):
                self._world_snap.blit(target, (0, 0))
                self._magnifier.draw(target, self._world_snap, mx, my)

        self._draw_hud(target)
        self._draw_buttons(target)

        if self.gs.phase == "paused":
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 20, 180) if self.theme_t > 0.5 else (255, 255, 255, 200))
            target.blit(ov, (0, 0))
            txt(target, "PAUSED", self.W//2, self.H//2-30, 42, self._get_c("text"), bold=True, center=True)
            txt(target, "Press ESC or P to resume", self.W//2, self.H//2+24, 17, self._get_c("sub"), center=True)

        draw_transition(target, self.screen_t, duration=1.4)

        if self._trans_active:
            angle   = math.sin(math.pi * self._trans_progress) * 4.0
            rotated = pygame.transform.rotate(target, angle)
            rw, rh  = rotated.get_size()
            rx, ry  = (self.W - rw) // 2, (self.H - rh) // 2
            surface.fill(bg_col)
            if self.shake_t > 0:
                amp = self.shake_amp * (self.shake_t / 0.75)
                ox, oy = int(math.sin(self.shake_t * 60) * amp), int(math.cos(self.shake_t * 55) * amp * 0.5)
                surface.blit(rotated, (rx + ox, ry + oy))
            else: surface.blit(rotated, (rx, ry))
        elif self.shake_t > 0:
            amp = self.shake_amp * (self.shake_t / 0.75)
            ox, oy = int(math.sin(self.shake_t * 60) * amp), int(math.cos(self.shake_t * 55) * amp * 0.5)
            surface.fill((0, 0, 0))
            surface.blit(target, (ox, oy))
        else:
            surface.blit(target, (0, 0))

        if self.gs.phase == "how_to_play":
            self._htp_close_btn = draw_help_overlay(surface)

        if self.flashlight_active and self.gs.phase == "playing":
            mx, my = pygame.mouse.get_pos()
            if not ((my < HUD) or (my > self.H - 75)):
                tx, ty = mx, my + 100
                pygame.draw.polygon(surface, (80, 70, 60), [(tx-4, ty), (tx+4, ty), (tx+2, ty+30), (tx-2, ty+30)])
                pygame.draw.ellipse(surface, (120, 110, 100), (tx-5, ty-2, 10, 4))
                pygame.draw.ellipse(surface, (200, 100, 0),   (tx-3, ty-1, 6, 2))
            fs = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            for p in self.torch_particles: p.draw(fs)
            surface.blit(fs, (0, 0))

    def _draw_hud(self, surface):
        gc     = self._get_c
        hud_bg = gc("hud_bg")
        border = gc("border")
        
        hud_margin = 150
        hud_w = self.W - hud_margin * 2
        
        hud_surf = pygame.Surface((hud_w, HUD), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (*hud_bg, 230), (0, 0, hud_w, HUD), border_bottom_left_radius=20, border_bottom_right_radius=20)
        surface.blit(hud_surf, (hud_margin, 0))
        pygame.draw.rect(surface, border, (hud_margin, -2, hud_w, HUD+2), 2, border_bottom_left_radius=20, border_bottom_right_radius=20)

        gs  = self.gs
        tl  = gs.time_left
        tot = gs.level.time_limit if gs.level else 120
        rat = max(0, tl / tot)

        lpad = hud_margin + 25
        txt(surface, "TIME", lpad, 16, 11, gc("sub"), bold=True)

        mins, secs = int(tl) // 60, int(tl) % 60
        time_s = f"{'❄  ' if gs.frozen else ''}{mins}:{secs:02d}"
        tcol   = (80, 180, 220) if gs.frozen else gc("text")
        txt(surface, time_s, lpad, 29, 26, tcol, bold=True)

        bx, by_, bw, bh = lpad, 69, 180, 10
        pygame.draw.rect(surface, gc("timer_bg"), (bx, by_, bw, bh), border_radius=5)

        if gs.frozen: bc = (168, 216, 234)
        elif rat > 0.5: bc = (93, 211, 158)
        elif rat > 0.25: bc = (255, 214, 180)
        else: bc = tuple(int(v * (0.7 + 0.3 * abs(math.sin(pygame.time.get_ticks() / 180)))) for v in (255, 107, 138))

        fw = max(0, int(bw * rat))
        if fw > 0: pygame.draw.rect(surface, bc, (bx, by_, fw, bh), border_radius=5)

        CX = self.W // 2
        if gs.level:
            txt(surface, gs.level.title.upper(), CX, 27, 20, gc("text"), bold=True, center=True)
            diff_cols = {"easy": (39, 209, 120), "medium": (255, 180, 0), "hard": (255, 60, 80)}
            dc     = diff_cols.get(gs.level.category, gc("sub"))
            dlabel = gs.level.diff_label.upper()
            lw     = font(11, bold=True).size(dlabel)[0] + 20
            badge  = pygame.Rect(CX - lw // 2, 56, lw, 18)
            bs2    = pygame.Surface((badge.w, badge.h), pygame.SRCALPHA)
            pygame.draw.rect(bs2, (*dc, 35), bs2.get_rect(), border_radius=9)
            surface.blit(bs2, badge.topleft)
            pygame.draw.rect(surface, dc, badge, width=1, border_radius=9)
            txt(surface, dlabel, CX, 65, 11, dc, bold=True, center=True)

        RIGHT_START = self.W - hud_margin - 310
        pygame.draw.line(surface, border, (RIGHT_START, 10), (RIGHT_START, HUD - 10), 1)

        BLOCK = 300 // 3
        stats = [
            ("FOUND", f"{gs.found_count()}/{len(gs.regions)}", gc("text")),
            ("LIVES", None, None),
            ("SCORE", str(gs.score), (255, 190, 80)),
        ]

        for i, (label, value, color) in enumerate(stats):
            cx = RIGHT_START + i * BLOCK + BLOCK // 2
            if i > 0: pygame.draw.line(surface, border, (RIGHT_START + i * BLOCK, 10), (RIGHT_START + i * BLOCK, HUD - 10), 1)
            txt(surface, label, cx, 16, 11, gc("sub"), bold=True, center=True)
            if label == "LIVES":
                max_l = gs.level.max_wrong if gs.level else 5
                sp    = min(24, (BLOCK - 10) // max(max_l, 1))
                total = max_l * sp - (sp - 18)
                hx    = cx - total // 2
                for j in range(max_l):
                    col = (255, 107, 138) if j < gs.lives else border
                    txt(surface, "♥", hx + j * sp, 39, 20, col, bold=True)
            else:
                txt(surface, value, cx, 39, 24, color, bold=True, center=True)

    def _draw_buttons(self, surface):
        t  = self.theme_t
        def nb(day_bg, day_tc, day_hov, night_bg=None, night_tc=None, night_hov=None):
            if night_bg  is None: night_bg  = tuple(max(0, c - 80) for c in day_bg)
            if night_tc  is None: night_tc  = tuple(min(255, c + 80) for c in day_tc)
            if night_hov is None: night_hov = tuple(max(0, c - 80) for c in day_hov)
            return (_lerp_col(day_bg, night_bg, t), _lerp_col(day_tc, night_tc, t), _lerp_col(day_hov, night_hov, t))

        ph = "Resume" if self.gs.phase == "paused" else "Pause"
        bg_, tc_, hv_ = nb((237,232,255),(124,92,191),(220,210,255), (40,35,72),(175,145,255),(55,48,95))
        button(surface, ph, self.btn_pause, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        cat = self.gs.level.category if self.gs.level else "easy"
        hints_left = (3 if cat == "easy" else (2 if cat == "medium" else 1)) - self.gs.hints_used
        if hints_left > 0:
            bg_, tc_, hv_ = nb((255,248,220),(200,150,40),(255,235,180), (60,50,28),(220,175,70),(75,62,35))
        else:
            bg_, tc_, hv_ = nb((240,240,240),(180,180,180),(240,240,240), (50,50,55),(140,140,150),(50,50,55))
        button(surface, f"Hint ({hints_left})", self.btn_hint, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        bg_, tc_, hv_ = nb((225,245,255),(80,160,200),(200,230,255), (22,44,65),(80,185,230),(30,58,85))
        button(surface, "Freeze", self.btn_freeze, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        if self.flashlight_active:
            bg_, tc_, hv_ = nb((230,255,230),(40,160,80),(210,245,210), (28,58,35),(70,200,110),(36,72,44))
        else:
            bg_, tc_, hv_ = nb((255,235,235),(200,80,80),(255,215,215), (60,28,30),(230,100,100),(72,36,36))
        button(surface, "Hunt Mode" if self.flashlight_active else "Torch", self.btn_flash, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        if self.magnifier_active:
            bg_, tc_, hv_ = nb((230,240,255),(50,100,200),(210,225,255), (28,45,75),(80,145,230),(36,56,92))
        else:
            bg_, tc_, hv_ = nb((240,240,255),(100,100,180),(225,225,255), (38,38,72),(130,130,200),(48,48,88))
        button(surface, "Magnify", self.btn_magnify, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        self._draw_audio_controls(surface)

        bg_, tc_, hv_ = nb((255,235,240),(220,80,100),(255,210,220), (65,22,30),(240,95,115),(80,28,38))
        button(surface, "Abort", self.btn_quit, bg_, tc_, radius=12, font_size=13, col_hover=hv_)

        # 'How to Play' button positioned on the right-side gap near the top
        if self.gs.phase == "how_to_play":
            bg_, tc_, hv_ = nb((200,185,255),(80,40,180),(185,168,248), (55,35,100),(160,120,255),(70,45,120))
        else:
            bg_, tc_, hv_ = nb((237,232,255),(100,70,200),(185,168,248), (40,35,72),(160,130,255),(55,48,95))
        button(surface, "How to Play", self.btn_howto, bg_, tc_, col_hover=hv_, radius=10, font_size=13, bold=True)