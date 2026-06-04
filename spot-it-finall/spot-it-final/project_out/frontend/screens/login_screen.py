# ============================================================
#  frontend/screens/login_screen.py  — Premium Light & Alive
#  ── Left : animated cute shape mascot face + dynamic bokeh
#  ── Right: light glass form panel + moving background
#  All backend calls (_do_login / _do_signup) UNCHANGED.
# ============================================================
import pygame, math, random
from ui_config import C, txt, rounded_box, button, input_box, draw_transition

# ── Light premium palette ─────────────────────────────────────
D = {
    "bg_l":    (248, 250, 252),  # Soft white/blue left
    "bg_r":    (240, 243, 248),  # Slightly darker right for contrast
    "accent":  (108, 92, 231),
    "cyan":    (0,  210, 248),
    "panel":   (255, 255, 255),  # Pure white form
    "border":  (225, 230, 240),  # Light border
    "ink":     (20,  25,  35),   # Dark text
    "ink_l":   (130, 135, 150),  # Subtle gray text
    "tab_a":   (108, 92, 231),   # Active tab
    "tab_i":   (235, 240, 245),  # Inactive tab
    "inp_bg":  (250, 252, 255),  # Input background
    "inp_bd":  (215, 220, 230),  # Input border
    "inp_act": (108, 92, 231),   # Active input border
    "btn":     (108, 92, 231),
    "btn_hov": (80,  64, 196),
    "btn_txt": (255, 255, 255),
    "error":   (255,  60,  80),
    "err_bg":  (255, 235, 240),
    "white":   (15,  20,  30),   
    "head":    (255, 255, 255),
    "ring":    (200, 205, 220),
    "eye_bg":  (255, 255, 255),
    "iris":    (0,  210, 248),
    "pupil":   (20,  25,  30),
}

# ── Helpers ──────────────────────────────────────────────────
def _eye_target(eye_cx, eye_cy, mouse_pos, max_px=18.0):
    """Compute strong iris offset toward mouse_pos."""
    if mouse_pos is None:
        return 0.0, 0.0
    dx = mouse_pos[0] - eye_cx
    dy = mouse_pos[1] - eye_cy
    dist = math.hypot(dx, dy)
    if dist < 1:
        return 0.0, 0.0
    reach = min(max_px, dist * 0.25) 
    return (dx / dist) * reach, (dy / dist) * reach


# ── Background Movement Elements ─────────────────────────────
class _Orb:
    def __init__(self, lw, H):
        self.x   = random.randint(12, max(13, lw - 12))
        self.y0  = random.randint(30, max(31, H - 30))
        self.r   = random.randint(15, 45) 
        self.ph  = random.uniform(0, math.tau)
        self.fr  = random.uniform(0.1, 0.4) 
        self.ab  = random.randint(10, 40) 
        col = random.choice([
            (108, 92, 231), (0, 210, 248), (250, 100, 45), (240, 200, 30), (150, 100, 250)
        ])
        # Cache the surface for high performance
        self.surf = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (*col, 255), (self.r, self.r), self.r)

    def draw(self, main_surf, t):
        y = self.y0 + math.sin(t * self.fr + self.ph) * 25
        x = self.x + math.cos(t * self.fr * 0.8 + self.ph) * 15
        a = self.ab + int(math.sin(t * self.fr * 1.7 + self.ph) * 15)
        self.surf.set_alpha(max(0, min(255, a)))
        main_surf.blit(self.surf, (int(x) - self.r, int(y) - self.r))

class _AmbientBlob:
    def __init__(self, W, H):
        self.x   = random.randint(0, W)
        self.y0  = random.randint(0, H)
        self.r   = random.randint(250, 450)
        self.ph  = random.uniform(0, math.tau)
        self.fr  = random.uniform(0.05, 0.15)
        col = random.choice([
            (108, 92, 231), (0, 210, 248), (250, 100, 45)
        ])
        # Cache massive transparent surface
        self.surf = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surf, (*col, 7), (self.r, self.r), self.r) # Ultra faint

    def draw(self, main_surf, t):
        y = self.y0 + math.sin(t * self.fr + self.ph) * 120
        x = self.x + math.cos(t * self.fr * 0.8 + self.ph) * 120
        main_surf.blit(self.surf, (int(x) - self.r, int(y) - self.r))


# ── Mascot draw (Cute Asymmetrical Shapes) ───────────────────
def _draw_mascot(surf, cx, cy, t, eye_ox, eye_oy, eye_close, body_ox=0.0, sc=1.0):
    s = sc
    cx += int(body_ox) # Apply body movement
    
    # Base floating animation for the whole group
    fy = math.sin(t * 1.35) * (6 * s)
    gy = int(cy + fy + 60 * s) 

    def draw_face(ex, ey, radius, has_white, spacing=None):
        ox = eye_ox * 0.5
        oy = eye_oy * 0.5
        lid = max(0.0, min(1.0, eye_close))
        h = int(radius * 2 * (1.0 - lid))

        if h < 2:
            pygame.draw.line(surf, (20, 20, 25), (ex - radius, ey), (ex + radius, ey), max(2, int(3 * s)))
            if spacing:
                pygame.draw.line(surf, (20, 20, 25), (ex + spacing - radius, ey), (ex + spacing + radius, ey), max(2, int(3 * s)))
            return

        xs = [ex] if spacing is None else [ex, ex + spacing]

        for x in xs:
            rect = pygame.Rect(int(x - radius), int(ey - h // 2), int(radius * 2), h)
            if has_white:
                pygame.draw.ellipse(surf, (255, 255, 255), rect)
                pr = max(2, int(radius * 0.55))
                ph = max(2, int(pr * 2 * (1.0 - lid)))
                px = x + ox
                py = ey + oy
                prect = pygame.Rect(int(px - pr), int(py - ph // 2), int(pr * 2), ph)
                pygame.draw.ellipse(surf, (20, 20, 25), prect)
            else:
                px = x + ox * 0.7 
                py = ey + oy * 0.7
                prect = pygame.Rect(int(px - radius), int(py - h // 2), int(radius * 2), h)
                pygame.draw.ellipse(surf, (20, 20, 25), prect)

    # 1. Purple Rectangle 
    pw, ph = int(90 * s), int(170 * s)
    px, py = cx - int(60 * s), gy - ph
    pygame.draw.rect(surf, (95, 45, 240), (px, py, pw, ph))
    draw_face(px + int(25 * s), py + int(25 * s), int(12 * s), has_white=True, spacing=int(28 * s))
    pygame.draw.line(surf, (20, 20, 25), 
                     (px + int(32 * s), py + int(50 * s)), 
                     (px + int(42 * s), py + int(50 * s)), max(1, int(2.5 * s)))

    # 2. Black Rectangle 
    bw, bh = int(60 * s), int(115 * s)
    bx, by = cx + int(10 * s), gy - bh
    pygame.draw.rect(surf, (35, 35, 40), (bx, by, bw, bh))
    draw_face(bx + int(15 * s), by + int(20 * s), int(11 * s), has_white=True, spacing=int(20 * s))

    # 3. Orange Semi-Circle Blob 
    ow, oh = int(150 * s), int(75 * s)
    ox, oy = cx - int(110 * s), gy - oh
    pygame.draw.rect(surf, (250, 100, 45), (ox, oy, ow, oh), 
                     border_top_left_radius=int(75 * s), 
                     border_top_right_radius=int(75 * s))
    draw_face(ox + int(50 * s), oy + int(35 * s), int(9 * s), has_white=False, spacing=int(35 * s))
    
    m_rect = pygame.Rect(ox + int(56 * s), oy + int(48 * s), int(22 * s), int(15 * s))
    if eye_close < 0.5:
        pygame.draw.ellipse(surf, (20, 20, 25), m_rect)
        pygame.draw.rect(surf, (250, 100, 45), (ox + int(56 * s), oy + int(48 * s), int(22 * s), int(7 * s)))
    else:
        pygame.draw.line(surf, (20, 20, 25), 
                         (ox + int(60 * s), oy + int(54 * s)), 
                         (ox + int(74 * s), oy + int(54 * s)), max(1, int(2 * s)))

    # 4. Yellow Rounded Rectangle 
    yw, yh = int(65 * s), int(85 * s)
    yx, yy = cx + int(55 * s), gy - yh
    pygame.draw.rect(surf, (240, 200, 30), (yx, yy, yw, yh), 
                     border_top_left_radius=int(35 * s), 
                     border_top_right_radius=int(35 * s))
    draw_face(yx + int(45 * s), yy + int(25 * s), int(8 * s), has_white=False)
    pygame.draw.line(surf, (20, 20, 25), 
                     (yx + int(10 * s), yy + int(40 * s)), 
                     (yx + int(40 * s), yy + int(40 * s)), max(1, int(3 * s)))


# ============================================================
#  LoginScreen
# ============================================================
class LoginScreen:
    def __init__(self, app):
        self.app       = app
        self.W, self.H = app["W"], app["H"]

        # ── Form state ──────────────────────────────────────
        self.username  = ""
        self.password  = ""
        self.active    = "user"
        self.error     = ""
        self.success   = ""
        self.tab       = "login"
        self.t         = 0.0

        # ── Layout ──────────────────────────────────────────
        self.split  = self.W // 2
        card_w      = min(380, self.W - self.split - 40)
        card_x      = self.split + (self.W - self.split - card_w) // 2
        card_y      = (self.H - 340) // 2
        self.card_rect = pygame.Rect(card_x, card_y, card_w, 340)

        ix = card_x + 24
        iw = card_w - 48
        self.user_rect   = pygame.Rect(ix, card_y + 120, iw, 44)
        self.pass_rect   = pygame.Rect(ix, card_y + 178, iw, 44)

        tw = (card_w - 48) // 2 - 3
        self.login_tab_rect  = pygame.Rect(ix,       card_y + 60, tw, 36)
        self.signup_tab_rect = pygame.Rect(ix+tw+6,  card_y + 60, tw, 36)

        self.action_rect = pygame.Rect(ix, card_y + 240, iw, 46)

        # ── Mascot state ────────────────────────────────────
        self._msc_cx  = self.split // 2
        self._msc_cy  = self.H // 2
        self._msc_sc  = max(0.9, min(1.6, self.H / 500))
        self._body_ox = 0.0 
        self._eye_ox  = 0.0
        self._eye_oy  = 0.0
        self._eye_close = 0.0
        self._btn_hover = False

        # ── Background motion layers ────────────────────────
        lw = self.split
        self._orbs = [_Orb(lw, self.H) for _ in range(35)]
        self._blobs = [_AmbientBlob(self.W, self.H) for _ in range(6)]

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(e.pos)
            if e.type == pygame.KEYDOWN:
                self._handle_key(e)

    def _handle_click(self, pos):
        if self.user_rect.collidepoint(pos):   self.active = "user"; return
        if self.pass_rect.collidepoint(pos):   self.active = "pass"; return
        if self.login_tab_rect.collidepoint(pos):
            self.tab = "login";  self.error = ""; return
        if self.signup_tab_rect.collidepoint(pos):
            self.tab = "signup"; self.error = ""; return
        if self.action_rect.collidepoint(pos):
            if self.tab == "login": self._do_login()
            else:                   self._do_signup()

    def _handle_key(self, e):
        if self.active == "user":
            if e.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            elif e.key in (pygame.K_TAB, pygame.K_RETURN):
                self.active = "pass"
            elif e.unicode.isprintable() and e.unicode and len(self.username) < 24:
                self.username += e.unicode
        elif self.active == "pass":
            if e.key == pygame.K_BACKSPACE:
                self.password = self.password[:-1]
            elif e.key == pygame.K_RETURN:
                if self.tab == "login": self._do_login()
                else:                   self._do_signup()
            elif e.unicode.isprintable() and e.unicode and len(self.password) < 32:
                self.password += e.unicode

    def _do_login(self):
        u, p = self.username.strip(), self.password
        if not u or not p: self.error = "Missing credentials!"; return
        ok, pid_or_err, name = self.app["backend"].login(u, p)
        if ok:
            self.app["player_id"], self.app["player_name"] = pid_or_err, name
            self.app["current"] = "level_select"
            self.error = ""
        else:
            self.error = str(pid_or_err)

    def _do_signup(self):
        u, p = self.username.strip(), self.password
        if len(u) < 3: self.error = "Username needs 3+ chars!"; return
        if len(p) < 4: self.error = "Password needs 4+ chars!"; return
        ok, pid_or_err, name = self.app["backend"].signup(u, p)
        if ok:
            self.app["player_id"], self.app["player_name"] = pid_or_err, name
            self.app["current"] = "level_select"
            self.error = ""
        else:
            self.error = str(pid_or_err)

    def update(self, dt):
        self.t += dt

        mouse = pygame.mouse.get_pos()
        self._btn_hover = self.action_rect.collidepoint(mouse)
        sc = self._msc_sc

        if self.active == "user":
            tgt_body_ox = 60.0 * sc   
        elif self.active == "pass":
            tgt_body_ox = -80.0 * sc  
        else:
            tgt_body_ox = 0.0
            
        self._body_ox += (tgt_body_ox - self._body_ox) * min(1.0, dt * 5.0)

        tgt_ox, tgt_oy = _eye_target(
            self._msc_cx + self._body_ox, self._msc_cy - int(14 * sc),
            mouse, max_px=18.0 * sc
        )
        speed = min(1.0, dt * 14.0)
        self._eye_ox += (tgt_ox - self._eye_ox) * speed
        self._eye_oy += (tgt_oy - self._eye_oy) * speed

        tgt_close = 1.0 if self.active == "pass" else 0.0
        self._eye_close += (tgt_close - self._eye_close) * min(1.0, dt * 7.0)

    def draw(self, surface):
        # ── Left Background (Scrolling Grid) ──
        left_surf = pygame.Surface((self.split, self.H))
        left_surf.fill(D["bg_l"])
        
        offset = int(self.t * 15) % 44
        gc = (235, 240, 250)
        for gx in range(-44, self.split + 44, 44):
            pygame.draw.line(left_surf, gc, (gx + offset, 0), (gx + offset, self.H))
        for gy in range(-44, self.H + 44, 44):
            pygame.draw.line(left_surf, gc, (0, gy + offset), (self.split, gy + offset))
            
        self._draw_left_elements(left_surf)
        surface.blit(left_surf, (0, 0))

        # ── Right Background (Moving Diagonals) ──
        right_surf = pygame.Surface((self.W - self.split, self.H))
        right_surf.fill(D["bg_r"])
        
        r_offset = int(self.t * 15) % 60
        rgc = (234, 238, 245)
        for i in range(0, self.W + self.H, 60):
            pygame.draw.line(right_surf, rgc, (i + r_offset, 0), (i + r_offset - self.H, self.H), 2)
            
        surface.blit(right_surf, (self.split, 0))

        # ── Ambient Studio Blobs over entire screen ──
        for blob in self._blobs:
            blob.draw(surface, self.t)

        # ── Divider Glow ──
        div = pygame.Surface((12, self.H), pygame.SRCALPHA)
        for i in range(12):
            a = int(25 * (1 - i / 12))
            pygame.draw.line(div, (*D["accent"], a), (i, 0), (i, self.H))
        surface.blit(div, (self.split, 0))

        # ── Form Card ──
        self._draw_card(surface)

        draw_transition(surface, self.t)

    def _draw_left_elements(self, surf):
        lw = self.split

        # Floating bokeh orbs
        for orb in self._orbs:
            orb.draw(surf, self.t)

        # Mascot
        _draw_mascot(surf,
                     self._msc_cx, self._msc_cy,
                     self.t,
                     self._eye_ox, self._eye_oy,
                     self._eye_close,
                     body_ox=self._body_ox,
                     sc=self._msc_sc)

        # Title
        self._lbl(surf, "SpotQuest", lw // 2, self.H // 2 + int(108 * self._msc_sc),
                  28, D["white"], bold=True)
        self._lbl(surf, "Can You Find 'Em ALL?", lw // 2,
                  self.H // 2 + int(108 * self._msc_sc) + 30,
                  13, D["accent"], bold=True)

    def _lbl(self, surf, text, x, y, size, color, bold=False):
        try:
            f = pygame.font.SysFont("Segoe UI", size, bold=bold)
        except Exception:
            f = pygame.font.SysFont("Arial", size, bold=bold)
        s = f.render(text, True, color)
        r = s.get_rect(center=(x, y))
        surf.blit(s, r)

    def _draw_card(self, surface):
        cr = self.card_rect

        # Drop shadow
        sh = pygame.Surface((cr.w + 40, cr.h + 40), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 15),
                         (0, 0, cr.w + 40, cr.h + 40), border_radius=28)
        surface.blit(sh, (cr.x - 20, cr.y + 15))

        # Card body
        pygame.draw.rect(surface, D["panel"], cr, border_radius=22)
        pygame.draw.rect(surface, D["border"], cr, width=2, border_radius=22)

        # Top inner highlight
        hl = pygame.Surface((cr.w - 8, 2), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 100))
        surface.blit(hl, (cr.x + 4, cr.y + 2))

        # Greeting
        txt(surface, "Welcome back", cr.centerx, cr.y + 24,
            20, D["white"], bold=True, center=True)
        txt(surface, "Sign in to continue", cr.centerx, cr.y + 47,
            12, D["ink_l"], center=True)

        # Tabs
        for tab_name, rect, label in [
            ("login",  self.login_tab_rect,  "Login"),
            ("signup", self.signup_tab_rect, "Sign Up"),
        ]:
            active = (self.tab == tab_name)
            bg  = D["tab_a"] if active else D["tab_i"]
            fc  = D["btn_txt"] if active else D["ink_l"]
            pygame.draw.rect(surface, bg, rect, border_radius=10)
            if active:
                gr = pygame.Surface((rect.w + 6, rect.h + 6), pygame.SRCALPHA)
                pygame.draw.rect(gr, (*D["accent"], 35),
                                 gr.get_rect(), border_radius=13)
                surface.blit(gr, (rect.x - 3, rect.y - 3))
                pygame.draw.rect(surface, bg, rect, border_radius=10)
            txt(surface, label, rect.centerx, rect.centery,
                13, fc, bold=True, center=True)

        # Inputs
        self._draw_input(surface, self.user_rect,
                         self.username, self.active == "user",
                         "Username", show_stars=False)
        self._draw_input(surface, self.pass_rect,
                         self.password, self.active == "pass",
                         "Password", show_stars=True)

        # Submit button
        yo  = -3 if self._btn_hover else 0
        bcl = D["btn_hov"] if self._btn_hover else D["btn"]
        ar  = self.action_rect.move(0, yo)

        if self._btn_hover:
            bsh = pygame.Surface((ar.w + 14, ar.h + 14), pygame.SRCALPHA)
            pygame.draw.rect(bsh, (*D["accent"], 45),
                             (0, 0, ar.w + 14, ar.h + 14), border_radius=20)
            surface.blit(bsh, (ar.x - 7, ar.y + 5))

        pygame.draw.rect(surface, bcl, ar, border_radius=14)
        
        bhl = pygame.Surface((ar.w - 6, 2), pygame.SRCALPHA)
        bhl.fill((255, 255, 255, 50))
        surface.blit(bhl, (ar.x + 3, ar.y + 1))

        label = "Secure Login" if self.tab == "login" else "Create Account"
        txt(surface, label, ar.centerx, ar.centery,
            15, D["btn_txt"], bold=True, center=True)

        # Error
        if self.error:
            ey = self.card_rect.y + 302
            er = pygame.Rect(self.card_rect.x + 24, ey,
                             self.card_rect.w - 48, 28)
            pygame.draw.rect(surface, D["err_bg"], er, border_radius=9)
            pygame.draw.rect(surface, D["error"], er, width=1, border_radius=9)
            txt(surface, self.error, er.centerx, er.centery,
                11, D["error"], bold=True, center=True)

    def _draw_input(self, surface, rect, value, active, placeholder,
                    show_stars=False):
        bd = D["inp_act"] if active else D["inp_bd"]

        if active:
            gl = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
            pygame.draw.rect(gl, (*D["inp_act"], 20),
                             gl.get_rect(), border_radius=15)
            surface.blit(gl, (rect.x - 5, rect.y - 5))

        pygame.draw.rect(surface, D["inp_bg"], rect, border_radius=11)
        pygame.draw.rect(surface, bd, rect, width=2, border_radius=11)

        display = ("●" * len(value)) if (show_stars and value) else value
        col     = D["ink"]  if value else D["ink_l"]
        text    = display   if value else placeholder

        try:
            f = pygame.font.SysFont("Segoe UI", 15)
        except Exception:
            f = pygame.font.SysFont("Arial", 15)

        s = f.render(text, True, col)
        surface.blit(s, (rect.x + 14, rect.centery - s.get_height() // 2))

        if active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx2 = rect.x + 14 + (s.get_width() if value else 0) + 3
            pygame.draw.line(surface, D["cyan"],
                             (cx2, rect.y + 8), (cx2, rect.bottom - 8), 2)