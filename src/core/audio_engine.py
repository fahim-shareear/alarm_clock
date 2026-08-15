from PySide6.QtCore import QObject, QTimer

try:
    import pygame
except ImportError:  # pygame-ce installs as "pygame" too, this covers a missing install
    pygame = None


class AudioEngine(QObject):
    """Wraps pygame's music channel with a fade-in ramp."""

    def __init__(self, fade_ms: int = 4000, parent=None):
        super().__init__(parent)
        self.fade_ms = fade_ms
        self._ready = False

        if pygame is not None:
            try:
                pygame.mixer.init()
                self._ready = True
            except Exception as e:
                print(f"[warn] audio init failed: {e}")

        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_step)
        self._current_volume = 0.0
        self._step = 0.0

    def play(self, tone_path: str, loop: bool = True) -> None:
        if not self._ready:
            print("[warn] audio engine not initialized, skipping playback")
            return
        if not tone_path:
            print("[warn] alarm has no tone assigned, skipping playback")
            return

        try:
            pygame.mixer.music.load(tone_path)
        except Exception as e:
            print(f"[warn] could not load tone '{tone_path}': {e}")
            return

        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.play(loops=-1 if loop else 0)

        self._current_volume = 0.0
        steps = max(1, self.fade_ms // 200)
        self._step = 1.0 / steps
        self._fade_timer.start(200)

    def _fade_step(self) -> None:
        self._current_volume = min(1.0, self._current_volume + self._step)
        pygame.mixer.music.set_volume(self._current_volume)
        if self._current_volume >= 1.0:
            self._fade_timer.stop()

    def stop(self) -> None:
        self._fade_timer.stop()
        if self._ready:
            pygame.mixer.music.stop()