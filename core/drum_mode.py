# core/drum_mode.py
import time
from config import DRUM_PADS, VELOCITY_SCALE, MIN_VELOCITY


class DrumProcessor:
    """
    손가락 끝 Y 속도 기반 드럼 타격 감지기.

    velocity = |y_current - y_prev| / dt / VELOCITY_SCALE (0.0~1.0 클램프)

    패드 위치 (화면 4분할):
      히햇(좌상) | 클랩(우상)
      ──────────┼──────────
      킵(좌하)   | 스네어(우하)
    """

    def __init__(self, audio_engine, sensitivity=VELOCITY_SCALE):
        self._audio = audio_engine
        self.sensitivity = sensitivity
        self._prev = {}      # hand_label → {'y': float, 'time': float}
        self._cooldown = {}  # hand_label → last_trigger_time
        self._COOLDOWN_MS = 120

    def process(self, fingertips: list) -> list:
        """
        fingertips: [{'hand': str, 'tips': [(x,y,z)×5]}, ...]
        Returns: [{'pad': str, 'velocity': float, 'hand': str}, ...]  트리거된 패드 목록
        """
        triggered = []
        now = time.time()

        for hand in fingertips:
            label = hand['hand']
            x, y, _ = hand['tips'][1]  # 검지 끝

            if label in self._prev:
                prev = self._prev[label]
                dt = now - prev['time']
                if dt > 0:
                    velocity = abs(y - prev['y']) / dt / self.sensitivity
                    velocity = max(MIN_VELOCITY, min(1.0, velocity))

                    last_t = self._cooldown.get(label, 0)
                    if (now - last_t) * 1000 >= self._COOLDOWN_MS and velocity > 0.15:
                        pad = self._get_pad(x, y)
                        self._audio.play_drum(pad, velocity)
                        self._cooldown[label] = now
                        triggered.append({'pad': pad, 'velocity': velocity, 'hand': label})

            self._prev[label] = {'y': y, 'time': now}

        return triggered

    def _get_pad(self, x: float, y: float) -> str:
        """정규화된 (x, y) → 드럼 패드 이름"""
        for name, bounds in DRUM_PADS.items():
            if (bounds['x'][0] <= x < bounds['x'][1] and
                    bounds['y'][0] <= y < bounds['y'][1]):
                return name
        return 'snare'

    def set_sensitivity(self, value: float):
        self.sensitivity = max(0.5, min(5.0, value))
