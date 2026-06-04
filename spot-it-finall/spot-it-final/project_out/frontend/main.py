# ============================================================
#  frontend/main.py  — Entry point
# ============================================================

import pygame, sys, os

# Make sure imports work when run from frontend/ folder
sys.path.insert(0, os.path.dirname(__file__))

from backend_client import BackendClient
from screens.login_screen    import LoginScreen
from screens.level_select    import LevelSelectScreen
from screens.game_screen     import GameScreen
from screens.win_screen      import WinScreen
from screens.lose_screen     import LoseScreen, LeaderboardScreen

W, H   = 1280, 720
FPS    = 60
TITLE  = "Spot the Difference"

# ============================================================
# CENTRALIZED AUDIO MANAGER
# ============================================================

class AudioManager:
    """
    Single source of truth for all audio in the game.
    - music_volume : stored BGM volume (0.0–1.0), used even while muted
    - sfx_volume   : volume applied to all SFX played via play_sfx()
    - muted        : silences everything (music + SFX) without losing settings
    - _music_paused: True when BGM has been deliberately paused (win/lose)
    """

    def __init__(self):
        self.music_volume  = 0.35
        self.sfx_volume    = 0.75
        self.muted         = False
        self._music_paused = False

        self.music_path = os.path.join(
            os.path.dirname(__file__),
            "assets", "sounds", "bg_music.mp3"
        )

    # ----------------------------------------------------------
    # BGM helpers
    # ----------------------------------------------------------

    def start_music(self):
        """Load and start background music (looping)."""
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.set_volume(0.0 if self.muted else self.music_volume)
            pygame.mixer.music.play(-1)
            self._music_paused = False
        except Exception as e:
            print(f"[AudioManager] Failed to load music: {e}")

    def stop_music(self):
        """Fully stop BGM (used on quit)."""
        pygame.mixer.music.stop()
        self._music_paused = False

    def pause_music(self):
        """Pause BGM when entering win/lose screens."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        self._music_paused = True

    def resume_music(self):
        """Resume BGM when returning to gameplay / level select.
        Always unpauses the mixer track so the music is physically running;
        mute is handled by volume only, not by keeping the track paused.
        """
        if self._music_paused:
            pygame.mixer.music.unpause()          # always unpause the track
            if self.muted:
                pygame.mixer.music.set_volume(0.0)  # keep it silent if muted
            self._music_paused = False
        elif not pygame.mixer.music.get_busy():
            # Music stopped entirely (e.g. first boot edge case) — restart it
            self.start_music()
            if self.muted:
                pygame.mixer.music.set_volume(0.0)

    # ----------------------------------------------------------
    # Volume / mute
    # ----------------------------------------------------------

    def set_music_volume(self, volume: float):
        """Set BGM volume level (0.0–1.0). Respects mute."""
        self.music_volume = max(0.0, min(1.0, volume))
        if not self.muted and not self._music_paused:
            pygame.mixer.music.set_volume(self.music_volume)

    def toggle_mute(self):
        """Toggle BGM-only mute on/off. SFX (win/lose/correct/heartbeat) are NOT affected."""
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.set_volume(0.0)
        else:
            if not self._music_paused:
                pygame.mixer.music.set_volume(self.music_volume)

    # ----------------------------------------------------------
    # SFX helpers
    # ----------------------------------------------------------

    def play_sfx(self, sound: pygame.mixer.Sound):
        """
        Play a Sound object respecting mute + sfx_volume.
        Stops any previous play of the same sound first (prevents overlap).
        """
        if sound is None:
            return
        vol = 0.0 if self.muted else self.sfx_volume
        sound.set_volume(vol)
        sound.stop()          # prevent stacking / overlap
        sound.play()

    def play_sfx_loop(self, sound: pygame.mixer.Sound):
        """Play a Sound looped (e.g. heartbeat). Respects mute."""
        if sound is None:
            return
        vol = 0.0 if self.muted else self.sfx_volume
        sound.set_volume(vol)
        sound.play(loops=-1)

    def stop_all_sfx(self):
        """Stop all SFX channels (leaves music channel untouched)."""
        pygame.mixer.stop()

    def update_sfx_mute(self, sound: pygame.mixer.Sound):
        """Update volume of an already-playing looped sound to match mute state."""
        if sound is None:
            return
        vol = 0.0 if self.muted else self.sfx_volume
        sound.set_volume(vol)


# ============================================================
# MAIN
# ============================================================

def main():
    pygame.init()
    pygame.mixer.init(44100, -16, 2, 512)

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)

    clock = pygame.time.Clock()

    # ========================================================
    # AUDIO
    # ========================================================

    audio = AudioManager()
    audio.start_music()

    # ========================================================
    # BACKEND
    # ========================================================

    backend = BackendClient()
    connected = backend.connect()

    if not connected:
        print("⚠️  C++ server not running — scores won't be saved.")
        print("   Start it with: cd backend && server.exe")

    # ========================================================
    # SHARED APP STATE
    # ========================================================

    app = {
        "screen":         screen,
        "backend":        backend,
        "audio":          audio,

        "player_id":      None,
        "player_name":    "",

        "current":        "login",
        "selected_level": None,
        "game_result":    {},

        "W": W,
        "H": H,
    }

    # ========================================================
    # SCREENS
    # ========================================================

    screens = {
        "login":        LoginScreen(app),
        "level_select": LevelSelectScreen(app),
        "game":         GameScreen(app),
        "win":          WinScreen(app),
        "lose":         LoseScreen(app),
        "leaderboard":  LeaderboardScreen(app),
    }

    _has_enter_hook = {"win", "lose", "leaderboard"}

    prev_screen = app["current"]

    # ========================================================
    # GAME LOOP
    # ========================================================

    while True:
        dt = clock.tick(FPS) / 1000.0

        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                audio.stop_music()
                backend.close()
                pygame.quit()
                sys.exit()

        current = app["current"]

        # ====================================================
        # SCREEN TRANSITION HOOKS
        # ====================================================

        if current != prev_screen:

            if current in _has_enter_hook:
                screens[current]._on_enter()

            # Resume BGM when returning to level select or game from win/lose
            if prev_screen in {"win", "lose"} and current in {"level_select", "game"}:
                audio.resume_music()

            prev_screen = current 

        active = screens[current]

        active.handle_events(events)
        active.update(dt)
        active.draw(screen)

        pygame.display.flip()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()