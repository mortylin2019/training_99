"""
video_capture.py — Record the 99.exe game window to an MP4 video file.

Uses mss (fast DXGI screen capture) + ffmpeg subprocess pipe for H.264 encoding.
Runs capture on a background thread to avoid blocking the main game loop.

Usage:
    recorder = VideoRecorder(game.hwnd, fps=80)
    recorder.start()
    # ... in game loop ...
    recorder.capture_frame()  # call each frame during gameplay
    recorder.stop()           # finalizes video
"""

import subprocess
import threading
import time
import os
from pathlib import Path
from loguru import logger

try:
    import mss
except ImportError:
    mss = None


class VideoRecorder:
    """Captures the game window (and optionally a second window) to MP4."""

    def __init__(self, hwnd, output_path=None, fps=80, crf=23, second_hwnd=None):
        """
        Args:
            hwnd: Win32 window handle of the primary (game) window.
            output_path: Path for the output .mp4 file.
            fps: Frame rate for the output video.
            crf: H.264 quality (0-51, lower=better).
            second_hwnd: Optional second window to include in the capture
                         (e.g. AI Monitor). Captures bounding box of both.
        """
        self.hwnd = hwnd
        self.second_hwnd = second_hwnd
        self.fps = fps
        self.crf = crf
        self._ffmpeg_proc = None
        self._lock = threading.Lock()
        self._running = False
        self._frame_count = 0
        self._start_time = None
        self._width = 0
        self._height = 0

        if output_path:
            self.output_path = output_path
        else:
            ts = time.strftime("%Y%m%d_%H%M%S")
            os.makedirs("logs/videos", exist_ok=True)
            self.output_path = os.path.join("logs/videos", f"gameplay_{ts}.mp4")

    # ── Window geometry ────────────────────────────────────────────

    @staticmethod
    def _ensure_dpi_aware():
        """Make the process DPI-aware so window coordinates match physical pixels."""
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _get_window_rect(self):
        """Get the game window's CLIENT AREA screen coordinates and size.

        Computes the client area (game content, no title bar/borders)
        screen position using ClientToScreen, with DPI awareness.
        Falls back to full window rect if client area looks wrong.
        """
        import ctypes
        from ctypes import wintypes

        self._ensure_dpi_aware()

        hwnd = ctypes.wintypes.HWND(self.hwnd)

        # Get client area size
        cr = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(cr))
        cw = cr.right - cr.left
        ch = cr.bottom - cr.top

        # Convert client (0,0) to screen coordinates
        pt = wintypes.POINT()
        pt.x, pt.y = 0, 0
        ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))

        # Validate: client area should be ~304x224 for 99.exe
        if 200 <= cw <= 400 and 150 <= ch <= 300:
            logger.debug(f"Capture (client): left={pt.x}, top={pt.y}, {cw}x{ch}")
            return {"left": pt.x, "top": pt.y, "width": cw, "height": ch}

        # Fallback: use full window rect
        wr = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(wr))
        w = wr.right - wr.left
        h = wr.bottom - wr.top
        logger.debug(f"Capture (window): left={wr.left}, top={wr.top}, {w}x{h}")
        return {"left": wr.left, "top": wr.top, "width": w, "height": h}

    def _get_combined_rect(self):
        """Get the bounding box covering both windows.
        Validates against screen bounds; falls back to single-window if invalid."""
        import ctypes
        from ctypes import wintypes

        self._ensure_dpi_aware()

        rects = []
        for hwnd in (self.hwnd, self.second_hwnd):
            if not hwnd:
                continue
            try:
                wr = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(
                    ctypes.wintypes.HWND(hwnd), ctypes.byref(wr),
                )
                if wr.right > wr.left and wr.bottom > wr.top:
                    rects.append({
                        "left": wr.left, "top": wr.top,
                        "right": wr.right, "bottom": wr.bottom,
                    })
            except Exception:
                pass

        if not rects:
            return self._get_window_rect()

        # Compute bounding box
        left = min(r["left"] for r in rects)
        top = min(r["top"] for r in rects)
        right = max(r["right"] for r in rects)
        bottom = max(r["bottom"] for r in rects)
        w, h = right - left, bottom - top

        # Validate against screen bounds
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN

        if left < 0 or top < 0 or right > screen_w or bottom > screen_h:
            logger.warning(f"Combined rect {w}x{h} exceeds screen {screen_w}x{screen_h} — using game-only")
            return self._get_window_rect()
        if w > screen_w or h > screen_h:
            logger.warning(f"Combined rect {w}x{h} larger than screen — using game-only")
            return self._get_window_rect()

        logger.info(f"🎬 Combined capture: {w}x{h} covering {len(rects)} windows")
        return {"left": left, "top": top, "width": w, "height": h}

    # ── Public API ──────────────────────────────────────────────────

    def start(self):
        """Launch ffmpeg and begin recording."""
        if mss is None:
            logger.error("mss not installed. Run: pip install mss")
            return False

        # Get capture region — combined if second window specified
        if self.second_hwnd:
            rect = self._get_combined_rect()
        else:
            rect = self._get_window_rect()
        self._width = rect["width"]
        self._height = rect["height"]

        if self._width <= 0 or self._height <= 0:
            logger.error(f"Invalid window dimensions: {self._width}x{self._height}")
            return False

        # Ensure output directory exists
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        # ffmpeg command: read raw RGB24 frames from stdin, encode to H.264 MP4
        cmd = [
            "ffmpeg",
            "-y",  # overwrite output
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self._width}x{self._height}",
            "-pix_fmt", "bgra",  # mss captures BGRA
            "-r", str(self.fps),
            "-i", "-",  # stdin
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", str(self.crf),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            self.output_path,
        ]

        logger.info(f"🎬 Recording → {self.output_path} ({self._width}x{self._height} @ {self.fps}fps)")

        try:
            self._ffmpeg_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.error("ffmpeg not found on PATH. Install ffmpeg to use video recording.")
            return False

        self._running = True
        self._frame_count = 0
        self._start_time = time.time()

        # Create mss capture context targeting the game client area
        self._sct = mss.mss()
        self._monitor = {
            "left": rect["left"],
            "top": rect["top"],
            "width": self._width,
            "height": self._height,
        }

        return True

    def capture_frame(self):
        """Capture one frame and pipe to ffmpeg."""
        if not self._running or self._ffmpeg_proc is None:
            return

        try:
            with self._lock:
                img = self._sct.grab(self._monitor)
                self._ffmpeg_proc.stdin.write(img.bgra)
                self._frame_count += 1
        except BrokenPipeError:
            logger.warning("ffmpeg pipe broken — recording stopped early")
            self._running = False
        except OSError as e:
            self._consecutive_errors = getattr(self, '_consecutive_errors', 0) + 1
            if self._consecutive_errors == 1:
                # Log the first error with details for diagnosis
                logger.warning(
                    f"Capture error: {e} | region=({self._monitor['left']},{self._monitor['top']}) "
                    f"{self._monitor['width']}x{self._monitor['height']}"
                )
            elif self._consecutive_errors <= 3:
                logger.debug(f"Capture error ({self._consecutive_errors}/3): {e}")
            if self._consecutive_errors > 30:
                logger.warning("Too many capture errors — stopping recording")
                self._running = False
        except AttributeError:
            self._running = False
        else:
            self._consecutive_errors = 0

    def stop(self):
        """Finalize the video file. Call when recording is done."""
        if not self._running:
            return

        self._running = False
        elapsed = time.time() - self._start_time if self._start_time else 0

        if self._ffmpeg_proc:
            try:
                self._ffmpeg_proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                self._ffmpeg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._ffmpeg_proc.kill()
                self._ffmpeg_proc.wait()

        actual_fps = self._frame_count / elapsed if elapsed > 0 else 0
        logger.info(
            f"🎬 Recording saved: {self.output_path} "
            f"({self._frame_count} frames, {elapsed:.1f}s, {actual_fps:.1f} fps)"
        )

    @property
    def is_recording(self):
        return self._running

    @property
    def frame_count(self):
        return self._frame_count
