"""
ai_visualizer.py — Real-time AI decision overlay for Training 99.

Provides a tkinter window that shows:
  - 2x scaled playfield with bullet type colors + AI direction arrow
  - Live stats (run #, survival time, bullet count, pattern)
  - Mini playfield overview
  - Auto-positions the game window beside it for a clean layout

Usage:
    viz = AIVisualizer(game_hwnd=game.hwnd)
    viz.start()
    viz.update(px=152, py=44, bullets=..., stats=..., ai_move='LEFT')
    viz.stop()
"""

import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
from loguru import logger

# ── DPI awareness (must happen before any tkinter window creation) ──
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ── Color scheme ──────────────────────────────────────────────────
BG_DARK = "#0f0f23"
BG_PANEL = "#1a1a3e"
ACCENT = "#e94560"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0a0c0"
BULLET_COLORS = {
    0: "#ff4444",  # Normal — red
    1: "#ffaa00",  # Homing — orange/yellow
    2: "#44aaff",  # Bounce — blue
    3: "#cc44ff",  # Accelerating — purple
}
PLAYER_COLOR = "#00ff88"
HITBOX_COLOR = "#00ff8866"
DANGER_COLORS = ["#00000000", "#00ff0044", "#88ff0044", "#ffff0066",
                 "#ff880088", "#ff0000aa"]  # transparent → red


class AIVisualizer:
    """Tkinter overlay showing live AI gameplay state.
    The game window is positioned to the left; this monitor sits to its right."""

    def __init__(self, game_hwnd=None, embed=False):
        self.game_hwnd = game_hwnd
        self.embed = embed  # if True, reposition game window next to us
        self.running = False
        self.thread = None
        self.root = None
        self.playfield = None  # main canvas
        self._ui_ready = threading.Event()
        self._ui_error = None

        # Shared state (written by game loop, read by UI thread)
        self._lock = threading.Lock()
        self._state = {
            "px": 152, "py": 44,
            "bullets": [],
            "stats": {},
            "ai_move": "—",
            "danger": None,
            "is_playing": False,
        }
        self._frame_time = time.time()

    # ── Public API ──────────────────────────────────────────────────

    def start(self):
        """Launch the UI in a background thread."""
        if self.running:
            return
        self.running = True
        self._ui_ready.clear()
        self.thread = threading.Thread(target=self._run_ui, daemon=True)
        self.thread.start()
        # Wait up to 3s for the window to appear
        if not self._ui_ready.wait(timeout=3.0):
            if self._ui_error:
                logger.error(f"🖥️  AI Visualizer FAILED: {self._ui_error}")
            else:
                logger.error("🖥️  AI Visualizer timed out — window did not appear")
            self.running = False
            return
        logger.info("🖥️  AI Visualizer started")

    def update(self, px=None, py=None, bullets=None, stats=None,
               ai_move=None, danger=None, is_playing=None):
        """Push the latest game state. Call from game loop (any thread)."""
        with self._lock:
            if px is not None:
                self._state["px"] = px
            if py is not None:
                self._state["py"] = py
            if bullets is not None:
                # Store a shallow copy of the bullet list to avoid mutation races
                self._state["bullets"] = list(bullets)
            if stats is not None:
                self._state["stats"] = dict(stats)
                # One-time debug: confirm stats are flowing
                if not hasattr(self, '_stats_logged'):
                    self._stats_logged = True
                    logger.debug(f"📊 First stats received: {stats}")
            if ai_move is not None:
                self._state["ai_move"] = ai_move
            if danger is not None:
                self._state["danger"] = danger
            if is_playing is not None:
                self._state["is_playing"] = is_playing

    def stop(self):
        """Close the UI window."""
        self.running = False
        self._ui_ready.clear()
        if self.root:
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass

    @property
    def monitor_hwnd(self):
        """Win32 HWND of the AI Monitor window (for video capture)."""
        if self.root is None:
            return None
        try:
            # On Windows, frame().winfo_id() gives the HWND
            return self.root.winfo_id()
        except Exception:
            return None

    # ── UI Construction ─────────────────────────────────────────────

    def _run_ui(self):
        """Build and run the tkinter UI. Runs in background thread."""
        try:
            self.root = tk.Tk()
            self.root.title("特訓９９ — AI Monitor")
            self.root.configure(bg=BG_DARK)
            self.root.resizable(False, False)
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)

            # ── Main layout ──
            main_frame = tk.Frame(self.root, bg=BG_DARK)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            # Left panel — playfield canvas
            left_frame = tk.Frame(main_frame, bg=BG_DARK)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

            self._build_canvas_panel(left_frame)

            # Right panel — stats (compact, no forced width)
            right_frame = tk.Frame(main_frame, bg=BG_PANEL)
            right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))

            self._build_stats_panel(right_frame)

            # Signal that UI is ready
            self._ui_ready.set()

            # Start periodic UI refresh
            self.root.after(50, self._refresh)
            self.root.mainloop()

        except Exception as e:
            self._ui_error = f"{e}\n{traceback.format_exc()}"
            logger.error(f"🖥️  AI Visualizer crashed: {self._ui_error}")
            self._ui_ready.set()  # unblock start() so it can report the error
            self.running = False

    def position_at(self, x, y, height=None):
        """Move this monitor window to (x, y), optionally matching a height."""
        try:
            mw = self.root.winfo_reqwidth()
            mh = height if height else self.root.winfo_reqheight()
            self.root.geometry(f"{mw}x{mh}+{x}+{y}")
        except Exception:
            pass

    def _build_canvas_panel(self, parent):
        """Create a canvas showing the playfield, scaled to fit game height."""
        # Scale canvas so monitor height ≈ game window height (~400px)
        # Game is 304×224. Scale 1.5 → 456×336 canvas, ~370px window.
        self._scale = 1.5
        cw = int(304 * self._scale)
        ch = int(224 * self._scale)
        self.playfield = tk.Canvas(
            parent, width=cw, height=ch,
            bg="#0a0a1a", highlightthickness=1,
            highlightbackground="#333366",
        )
        self.playfield.pack(padx=2, pady=2)

    def _build_stats_panel(self, parent):
        """Create the stats display on the right side."""
        # Title
        tk.Label(
            parent, text="AI MONITOR", bg=BG_PANEL,
            fg=ACCENT, font=("Consolas", 12, "bold"),
        ).pack(pady=(8, 4))

        # Separator
        tk.Frame(parent, bg=ACCENT, height=2).pack(fill=tk.X, padx=8)

        # Stat labels
        self.stat_labels = {}
        stat_fields = [
            ("Run", "—"),
            ("Survival", "—"),
            ("Frames", "—"),
            ("Bullets", "—"),
            ("Nearest", "—"),
            ("Pattern", "—"),
            ("AI Move", "—"),
            ("Algo", "—"),
            ("FPS", "—"),
        ]
        stat_container = tk.Frame(parent, bg=BG_PANEL)
        stat_container.pack(fill=tk.X, padx=6, pady=2)

        for name, default in stat_fields:
            row = tk.Frame(stat_container, bg=BG_PANEL)
            row.pack(fill=tk.X, pady=1)
            tk.Label(
                row, text=f"{name}:", bg=BG_PANEL,
                fg=TEXT_SECONDARY, font=("Consolas", 9),
                anchor=tk.W, width=12,
            ).pack(side=tk.LEFT)
            val = tk.Label(
                row, text=default, bg=BG_PANEL,
                fg=TEXT_PRIMARY, font=("Consolas", 9, "bold"),
                anchor=tk.E,
            )
            val.pack(side=tk.RIGHT)
            self.stat_labels[name] = val

        # Separator
        tk.Frame(parent, bg=ACCENT, height=2).pack(fill=tk.X, padx=8, pady=(4, 0))

    # ── Periodic UI refresh ─────────────────────────────────────────

    def _refresh(self):
        """Called every ~33ms (30fps) to redraw the UI."""
        if not self.running or self.root is None:
            return

        try:
            now = time.time()
            dt = now - self._frame_time
            self._frame_time = now
            fps = 1.0 / dt if dt > 0 else 0

            with self._lock:
                state = dict(self._state)

            try:
                self._draw_playfield(state)
            except Exception as e:
                logger.debug(f"draw_playfield error: {e}")

            try:
                self._update_stats(state, fps)
            except Exception as e:
                logger.debug(f"update_stats error: {e}")

        except Exception as e:
            logger.debug(f"_refresh outer error: {e}")

        if self.running and self.root is not None:
            try:
                self.root.after(33, self._refresh)
            except Exception:
                pass

    def _draw_playfield(self, state):
        """Draw the playfield with player and bullets. Y-axis flipped."""
        if self.playfield is None:
            return

        c = self.playfield
        c.delete("all")

        SCALE = getattr(self, '_scale', 2)
        H = 224

        px = state.get("px", 152)
        py = H - 1 - state.get("py", 44)
        bullets = state.get("bullets", [])
        danger = state.get("danger")

        # ── Draw danger heatmap if available ──
        if danger is not None and hasattr(danger, 'shape'):
            try:
                import numpy as np
                dmax = np.max(danger)
                if dmax > 0:
                    dnorm = danger / dmax
                    for y in range(0, min(danger.shape[0], H), 4):
                        for x in range(0, min(danger.shape[1], 304), 4):
                            val = dnorm[y, x]
                            if val > 0.01:
                                color_idx = min(int(val * 5), 4)
                                color = DANGER_COLORS[color_idx + 1]
                                fy = (H - 1 - y) * SCALE  # flip Y
                                c.create_rectangle(
                                    x * SCALE, fy,
                                    (x + 4) * SCALE, fy + 4 * SCALE,
                                    fill=color, outline="",
                                )
            except Exception:
                pass

        # ── Draw bullets ──
        max_bullets = min(len(bullets), 200)
        for b in bullets[:max_bullets]:
            bx = b.x * SCALE
            by = (H - 1 - b.y) * SCALE  # flip Y
            color = BULLET_COLORS.get(b.type, "#ffffff")
            r = 2
            c.create_oval(bx - r, by - r, bx + r, by + r, fill=color, outline="")

        # ── Draw player ──
        pr = 4
        c.create_oval(
            px * SCALE - pr, py * SCALE - pr,
            px * SCALE + pr, py * SCALE + pr,
            fill=PLAYER_COLOR, outline="#00cc66", width=2,
        )
        # Hitbox (Y flipped: game uses Y+ for above-player)
        c.create_rectangle(
            (px + 2) * SCALE, (py - 0) * SCALE,
            (px + 12) * SCALE, (py - 9) * SCALE,
            outline=HITBOX_COLOR, width=1,
        )

        # ── AI move direction arrow (Y flipped: UP means +Y in game = -Y on canvas) ──
        move = state.get("ai_move", "—")
        move_dirs = {
            "LEFT": (-1, 0), "RIGHT": (1, 0),
            "UP": (0, 1), "DOWN": (0, -1),         # flipped Y
            "UP-LEFT": (-1, 1), "UP-RIGHT": (1, 1),
            "DOWN-LEFT": (-1, -1), "DOWN-RIGHT": (1, -1),
            "STOP": (0, 0),
        }
        dx, dy = move_dirs.get(move, (0, 0))
        if dx != 0 or dy != 0:
            arrow_len = 20
            ex = px * SCALE + dx * arrow_len
            ey = py * SCALE + dy * arrow_len
            c.create_line(
                px * SCALE, py * SCALE, ex, ey,
                fill="#00ff88", width=2, arrow=tk.LAST,
            )

        # Bullet count indicator
        c.create_text(
            8, 8, anchor=tk.NW,
            text=f"B:{len(bullets)}",
            fill=TEXT_SECONDARY, font=("Consolas", 9),
        )

    def _update_stats(self, state, fps):
        """Update the stat labels."""
        stats = state.get("stats", {})
        move = state.get("ai_move", "—")

        mapping = {
            "Run": str(stats.get("run", "—")),
            "Survival": str(stats.get("survival", "—")),
            "Frames": str(stats.get("frames", "—")),
            "Bullets": str(stats.get("bullets", "—")),
            "Nearest": str(stats.get("nearest", "—")),
            "Pattern": str(stats.get("pattern", "—")),
            "AI Move": move,
            "Algo": str(stats.get("algo", "—")),
            "FPS": f"{fps:.0f}",
        }

        # One-time debug: confirm rendering
        if stats and not hasattr(self, '_render_logged'):
            self._render_logged = True
            logger.debug(f"📊 Rendering stats: {mapping}")

        for name, label in self.stat_labels.items():
            if name in mapping:
                label.config(text=mapping[name])

    def _on_close(self):
        """Handle window close button."""
        self.running = False
        self.root.destroy()
