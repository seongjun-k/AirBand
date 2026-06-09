# core/piano_mode.py
import time
from config import SCALE_NOTES, BASE_OCTAVE, OCTAVE_RANGE, NOTE_REPEAT_MS


class PianoProcessor:
    """
    손가락 끝 좌표 → 음계/옷타브/볼륨 변환 처리기.

    매핑 규칙:
      - 검지 끝(tips[1]) X (0.0~1.0) → C장조 2옷타브 범위 음계
      - 검지 끝(tips[1]) Y (0.0~1.0) → 볼륨 (1.0 - y, 위가 크게)
      - 손이 인식되는 동안 160ms 간격으로 해당 음 반복 재생
    """

    def __init__(self, audio_engine, base_octave=BASE_OCTAVE):
        self._audio = audio_engine
        self.base_octave = base_octave
        self._last_trigger_ms = 0

    def process(self, fingertips: list) -> dict | None:
        """
        fingertips: [{'hand': str, 'tips': [(x,y,z)×5]}, ...]
        Returns: {'note': str, 'octave': int, 'volume': float} or None
        """
        if not fingertips:
            return None

        # 가정: 왼손 우선, 없으면 첫 번째 감지된 손 사용
        hand = next(
            (h for h in fingertips if h['hand'] == 'Left'),
            fingertips[0]
        )
        x, y, _ = hand['tips'][1]  # 검지 끝 (landmark 8)

        note, octave = self._x_to_note(x)
        volume = max(0.0, min(1.0, 1.0 - y))

        now_ms = time.time() * 1000
        if now_ms - self._last_trigger_ms >= NOTE_REPEAT_MS:
            self._audio.play_piano(note, octave, volume)
            self._last_trigger_ms = now_ms

        return {'note': note, 'octave': octave, 'volume': volume}

    def _x_to_note(self, x: float) -> tuple:
        """
        X 위치 (0.0~1.0) → (음계 이름, 옷타브)
        2옷타브(SCALE_NOTES ×2) 범위로 균등 분할
        """
        total = len(SCALE_NOTES) * 2
        idx = int(x * total)
        idx = max(0, min(idx, total - 1))
        note = SCALE_NOTES[idx % len(SCALE_NOTES)]
        octave = self.base_octave + (idx // len(SCALE_NOTES))
        return note, octave

    def set_octave(self, octave: int):
        self.base_octave = max(OCTAVE_RANGE[0], min(OCTAVE_RANGE[1], octave))
