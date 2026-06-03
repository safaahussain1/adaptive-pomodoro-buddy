import threading
import numpy as np

try:
    import sounddevice as sd
    _SD_AVAILABLE = True
except Exception:
    _SD_AVAILABLE = False

_QUIET_DB = 35.0       # library-quiet environment
_MODERATE_DB = 55.0    # coffee-shop level
_LOUD_DB = 70.0        # open-plan office / street noise


class AmbientNoiseDetector:
    """Continuously measures microphone RMS in a background thread."""

    def __init__(self, sample_rate: int = 16000, block_duration_ms: int = 200):
        self.sample_rate = sample_rate
        self.block_size = int(sample_rate * block_duration_ms / 1000)
        self._current_db = 40.0
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    # ------------------------------------------------------------------
    def start(self):
        if not _SD_AVAILABLE:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    def get_db(self) -> float:
        with self._lock:
            return self._current_db

    def get_noise_label(self) -> str:
        db = self.get_db()
        if db < _QUIET_DB:
            return "Quiet"
        elif db < _MODERATE_DB:
            return "Moderate"
        elif db < _LOUD_DB:
            return "Loud"
        else:
            return "Very Loud"

    # ------------------------------------------------------------------
    def _run(self):
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.block_size,
                dtype="float32",
            ) as stream:
                while self._running:
                    data, _ = stream.read(self.block_size)
                    rms = float(np.sqrt(np.mean(data ** 2)) + 1e-10)
                    db = 20 * np.log10(rms) + 94  # calibrated to approx dB SPL
                    db = max(0.0, db)
                    with self._lock:
                        self._current_db = db
        except Exception:
            pass  # microphone unavailable — silently degrade
