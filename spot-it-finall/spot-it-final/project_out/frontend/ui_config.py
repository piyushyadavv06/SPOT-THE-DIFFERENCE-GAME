# ============================================================
#  frontend/ui_config.py — Colors, fonts, shared draw helpers
# ============================================================
import pygame, math, os

# ---- Color palette ------------------------------------------
C = {
    "bg":         (10,  12,  30),
    "bg2":        (16,  20,  45),
    "panel":      (20,  28,  60),
    "panel2":     (26,  36,  72),
    "accent":     (108, 92, 231),
    "accent2":    (168, 85, 247),
    "accent_glow":(80,  60, 200),
    "green":      (39, 209, 120),
    "green2":     (0,  255, 136),
    "red":        (255,  60,  80),
    "red2":       (255, 100, 110),
    "yellow":     (255, 214,   0),
    "orange":     (255, 150,  40),
    "blue":       (40,  160, 255),
    "cyan":       (0,   220, 255),
    "white":      (240, 240, 250),
    "gray":       (130, 130, 150),
    "dark":       (5,    5,   15),
    "gold":       (255, 215,   0),
    "silver":     (192, 192, 192),
    "bronze":     (205, 127,  50),
    "easy":       (39,  209, 120),
    "medium":     (255, 214,   0),
    "hard":       (255,  60,  80)
}

# ---- Font Caching -------------------------------------------
_fonts = {}
_FONT_PRIORITY = [
    "Nunito", "Varela Round", "Poppins", "Segoe UI",
    "Trebuchet MS", "Calibri", "Arial Rounded MT Bold", "Arial"
]

def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        found = None
        for name in _FONT_PRIORITY:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                found = name
                break
        if found:
            _fonts[key] = pygame.font.SysFont(found, size, bold=bold)
        else:
            try:
                _fonts[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
            except Exception:
                _fonts[key] = pygame.font.SysFont("Arial", size, bold=bold)
    return _fonts[key]

def txt(surface, text, x, y, size, color, bold=False, center=False, right=False):
    f   = font(size, bold)
    sur = f.render(str(text), True, color)
    r   = sur.get_rect()
    if center: r.center = (x, y)
    elif right: r.midright = (x, y)
    else:       r.topleft  = (x, y)
    surface.blit(sur, r)
    return r

# ---- UI Elements --------------------------------------------
def rounded_box(surface, color, rect, radius=2, alpha=255, border_col=None, border_w=0):
    if alpha < 255:
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
        surface.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_col and border_w:
        pygame.draw.rect(surface, border_col, rect, width=border_w, border_radius=radius)

def drop_shadow(surface, rect, radius=16, blur_steps=6, color=(0, 0, 0), alpha_max=55, offset_y=6):
    for i in range(blur_steps, 0, -1):
        spread = i * 2
        a = int(alpha_max * (1 - (i / blur_steps) * 0.72))
        a = max(0, min(255, a))
        sr = pygame.Rect(
            rect.x - spread // 2,
            rect.y + offset_y - spread // 4,
            rect.w + spread,
            rect.h + spread // 2
        )
        s = pygame.Surface((sr.w, sr.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, a), s.get_rect(),
                         border_radius=min(radius + spread, 40))
        surface.blit(s, sr.topleft)

def button(surface, text, rect, col_bg, col_text, col_hover=None, radius=8, font_size=16, bold=True, icon=""):
    mouse = pygame.mouse.get_pos()
    hov   = rect.collidepoint(mouse)
    bg    = col_hover if (hov and col_hover) else col_bg

    rounded_box(surface, bg, rect, radius=radius)

    hl = pygame.Surface((rect.w - 4, 2), pygame.SRCALPHA)
    hl.fill((255, 255, 255, 28 if hov else 16))
    surface.blit(hl, (rect.x + 2, rect.y + 1))

    y_offset = -2 if hov else 0
    label = (icon + " " + text).strip()
    txt(surface, label, rect.centerx, rect.centery + y_offset, font_size, col_text, bold=bold, center=True)
    return hov

def input_box(surface, rect, value, active, placeholder="", show_stars=False):
    border = C["accent"] if active else C["panel2"]
    if active:
        gl = pygame.Surface((rect.w + 8, rect.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(gl, (*C["accent"], 28), gl.get_rect(), border_radius=14)
        surface.blit(gl, (rect.x - 4, rect.y - 4))
    rounded_box(surface, C["panel"], rect, radius=10, border_col=border, border_w=2)
    display = ("●" * len(value)) if show_stars else value
    col     = C["white"] if value else C["gray"]

    if not value:
        display = placeholder

    f = font(18)
    sur = f.render(display, True, col)
    surface.blit(sur, (rect.x+14, rect.centery - sur.get_height()//2))

    if active and (pygame.time.get_ticks() // 500) % 2 == 0:
        cx = rect.x + 14 + (sur.get_width() if value else 0) + 2
        pygame.draw.line(surface, C["white"], (cx, rect.y+8), (cx, rect.bottom-8), 2)

def draw_stars(surface, count, cx, cy, size=28):
    total = 3
    spacing = size + 8
    sx = cx - (total * spacing) // 2 + (spacing // 2)
    
    for i in range(total):
        col = C["gold"] if i < count else (50, 50, 70)
        star_cx = sx + i * spacing
        
        points = []
        outer_r = size / 2
        inner_r = size / 4
        
        for p in range(10):
            angle = math.pi/2 - p * (math.pi / 5)
            r = outer_r if p % 2 == 0 else inner_r
            x = star_cx + math.cos(angle) * r
            y = cy - math.sin(angle) * r
            points.append((x, y))
            
        pygame.draw.polygon(surface, col, points)

def glow_circle(surface, color, center, radius):
    s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    for i in range(radius, 0, -2):
        alpha = int(255 * (1 - i/radius))
        pygame.draw.circle(s, (*color, alpha), (radius, radius), i)
    surface.blit(s, (center[0]-radius, center[1]-radius))

# ---- Image Management ---------------------------------------
_img_cache = {}
def get_image(filepath, size):
    key = (filepath, size)
    if key not in _img_cache:
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Missing: {filepath}")
            img = pygame.image.load(filepath).convert_alpha()
            img = pygame.transform.smoothscale(img, size)
            _img_cache[key] = img
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            s = pygame.Surface(size)
            s.fill((40, 40, 40))
            pygame.draw.line(s, (255, 0, 0), (0, 0), size, 2)
            pygame.draw.line(s, (255, 0, 0), (0, size[1]), (size[0], 0), 2)
            _img_cache[key] = s
    return _img_cache[key]

# ---- Universal Screen Transition ----------------------------
def draw_transition(surface, t, duration=1.4):
    if t < duration:
        alpha = int(255 * (1 - (t / duration)))
        s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        surface.blit(s, (0, 0))

# ---- How To Play Overlay ------------------------------------
def draw_help_overlay(surface):
    sw, sh = surface.get_size()
    backdrop = pygame.Surface((sw, sh), pygame.SRCALPHA)
    backdrop.fill((10, 10, 30, 210))
    surface.blit(backdrop, (0, 0))

    pw, ph = 720, 440
    px = (sw - pw) // 2
    py = (sh - ph) // 2

    drop_shadow(surface, pygame.Rect(px, py, pw, ph), radius=20, blur_steps=8, alpha_max=80, offset_y=10)
    rounded_box(surface, (248, 250, 252), pygame.Rect(px, py, pw, ph), radius=18)
    rounded_box(surface, (230, 225, 245), pygame.Rect(px, py, pw, ph), radius=18,
                alpha=255, border_col=(200, 190, 230), border_w=2)

    title_rect = pygame.Rect(px, py, pw, 54)
    title_surf = pygame.Surface((pw, 54), pygame.SRCALPHA)
    pygame.draw.rect(title_surf, (124, 92, 191, 220), title_surf.get_rect(), border_radius=18)
    pygame.draw.rect(title_surf, (124, 92, 191, 220), pygame.Rect(0, 27, pw, 27))
    surface.blit(title_surf, (px, py))
    txt(surface, "HOW TO PLAY", px + pw // 2, py + 27, 20, (255, 255, 255), bold=True, center=True)

    items = [
        ("🔍", "Magnify",  "Activates a zoom lens under your cursor — hover over any area to see it up close."),
        ("🔦", "Torch",    "Hunt Mode: dims the screen and lights up the area around your cursor like a flashlight."),
        ("💡", "Hint",     "Highlights one hidden difference with a pulsing ring. Limited uses per difficulty."),
        ("❄️",  "Freeze",  "Stops the countdown timer for 5 seconds — costs points, use it wisely!"),
        ("⏸",  "Pause",   "Freezes the game; press again, ESC, or P to resume without losing time."),
        ("🚪", "Abort",    "Exits the level immediately and returns to the level select screen."),
    ]

    col_w   = pw // 2 - 20
    row_h   = 62
    start_y = py + 70
    pad_x   = 24

    for idx, (emoji, title, desc) in enumerate(items):
        col   = idx % 2
        row   = idx // 2
        ix    = px + pad_x + col * (col_w + 20)
        iy    = start_y + row * row_h

        icon_cx = ix + 20
        icon_cy = iy + 22
        ic_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(ic_surf, (124, 92, 191, 40), (20, 20), 20)
        surface.blit(ic_surf, (icon_cx - 20, icon_cy - 20))
        txt(surface, emoji, icon_cx, icon_cy, 18, (80, 60, 140), center=True)

        txt(surface, title, ix + 48, iy + 8,  14, (45, 45, 72),   bold=True)
        f_desc = font(12)
        words  = desc.split()
        line, lines = "", []
        for w in words:
            test = (line + " " + w).strip()
            if f_desc.size(test)[0] > col_w - 58:
                lines.append(line); line = w
            else:
                line = test
        if line: lines.append(line)
        for li, ln in enumerate(lines):
            txt(surface, ln, ix + 48, iy + 26 + li * 15, 12, (100, 100, 130))

    div_y = start_y + 3 * row_h + 4
    pygame.draw.line(surface, (220, 215, 235), (px + 20, div_y), (px + pw - 20, div_y), 1)

    btn_w, btn_h = 180, 40
    btn_rect = pygame.Rect(px + pw // 2 - btn_w // 2, py + ph - 56, btn_w, btn_h)
    button(surface, "Back  (ESC)", btn_rect, (124, 92, 191), (255, 255, 255),
           col_hover=(100, 70, 170), radius=10, font_size=14, bold=True)
    return btn_rect

# ---- Universal Audio Controls UI ----------------------------
class AudioUI:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 160, 36)
        self.mute_rect = pygame.Rect(x, y, 36, 36)
        self.slider_rect = pygame.Rect(x + 46, y + 13, 100, 10)
        self.dragging = False

    def handle_events(self, events, app):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.mute_rect.collidepoint(e.pos):
                    app["muted"] = not app.get("muted", False)
                    if "update_audio" in app: app["update_audio"]()
                elif self.slider_rect.inflate(10, 20).collidepoint(e.pos):
                    self.dragging = True
                    self._update_vol(e.pos[0], app)
            elif e.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
            elif e.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self._update_vol(e.pos[0], app)

    def _update_vol(self, mx, app):
        rel = mx - self.slider_rect.x
        vol = max(0.0, min(1.0, rel / self.slider_rect.w))
        app["bgm_volume"] = vol
        if vol > 0:
            app["muted"] = False
        else:
            app["muted"] = True
        if "update_audio" in app: app["update_audio"]()

    def draw(self, surface, app):
        rounded_box(surface, (255, 255, 255), self.rect, radius=18, alpha=200)
        pygame.draw.rect(surface, (225, 230, 240), self.rect, 2, border_radius=18)
        
        is_muted = app.get("muted", False) or app.get("bgm_volume", 0.35) == 0
        
        # --- Custom Vector Speaker Icon ---
        cx, cy = self.mute_rect.centerx, self.mute_rect.centery
        icon_col = C["text"]
        
        # Speaker base
        pygame.draw.polygon(surface, icon_col, [
            (cx - 7, cy - 4), (cx - 3, cy - 4), (cx + 3, cy - 8),
            (cx + 3, cy + 8), (cx - 3, cy + 4), (cx - 7, cy + 4)
        ])
        
        if is_muted:
            # Red X
            pygame.draw.line(surface, C["red"], (cx + 5, cy - 4), (cx + 11, cy + 4), 2)
            pygame.draw.line(surface, C["red"], (cx + 11, cy - 4), (cx + 5, cy + 4), 2)
        else:
            # Sound Waves
            pygame.draw.arc(surface, icon_col, (cx - 1, cy - 5, 10, 10), -math.pi/3, math.pi/3, 2)
            pygame.draw.arc(surface, icon_col, (cx - 3, cy - 8, 16, 16), -math.pi/4, math.pi/4, 2)
        # ----------------------------------
        
        pygame.draw.rect(surface, (225, 230, 240), self.slider_rect, border_radius=5)
        
        if not is_muted:
            vol = app.get("bgm_volume", 0.35)
            fw = int(self.slider_rect.w * vol)
            pygame.draw.rect(surface, (108, 92, 231), (self.slider_rect.x, self.slider_rect.y, fw, self.slider_rect.h), border_radius=5)
            pygame.draw.circle(surface, (168, 85, 247), (self.slider_rect.x + fw, self.slider_rect.centery), 8)
        else:
            pygame.draw.circle(surface, (130, 130, 150), (self.slider_rect.x, self.slider_rect.centery), 8)