# core/piano_mode.py
import time
import config
from config import SCALE_NOTES, BASE_OCTAVE, OCTAVE_RANGE, NOTE_REPEAT_MS
from core.gesture_detector import is_pinching


class PianoProcessor:
    """
    손가락 끝 좌표 -> 음계/옥타브/볼륨 변환 처리기.

    매핑 규칙:
      - 검지 끝(tips[1]) X (0.0~1.0) -> C장조 2옥타브 범위 음계
      - 검지 끝(tips[1]) Y (0.0~1.0) -> 볼륨 (1.0 - y, 위가 크게)
      - 트리거 모드(continuous, strike, pinch)에 따라 피아노 재생
    """

    def __init__(self, audio_engine, base_octave=BASE_OCTAVE):
        self._audio = audio_engine
        self.base_octave = base_octave
        self._last_trigger_ms = 0

        # 동작 감지용 상태 변수
        self._prev_y = None
        self._prev_time = None
        self._was_pinching = False
        self._cooldown_ms = 200  # 타격 간 최소 간격

    def process(self, fingertips: list) -> dict | None:
        """
        fingertips: [{'hand': str, 'tips': [(x,y,z)×5]}, ...]
        Returns: {'note': str, 'octave': int, 'volume': float, 'triggered': bool} or None
        """
        if not fingertips:
            self._prev_y = None
            self._prev_time = None
            self._was_pinching = False
            return None

        # 가정: 왼손 우선, 없으면 첫 번째 감지된 손 사용
        hand = next(
            (h for h in fingertips if h['hand'] == 'Left'),
            fingertips[0]
        )
        x, y, _ = hand['tips'][1]  # 검지 끝 (landmark 8)

        note, octave = self._x_to_note(x)
        volume = max(0.0, min(1.0, 1.0 - y))

        now = time.time()
        now_ms = now * 1000
        should_trigger = False

        trigger_mode = getattr(config, 'PIANO_TRIGGER_MODE', 'strike')

        if trigger_mode == 'continuous':
            if now_ms - self._last_trigger_ms >= NOTE_REPEAT_MS:
                should_trigger = True

        elif trigger_mode == 'pinch':
            pinching = is_pinching(hand)
            # 핀치 상태가 False에서 True로 전환될 때 한 번만 트리거
            if pinching and not self._was_pinching:
                should_trigger = True
            self._was_pinching = pinching

        elif trigger_mode == 'strike':
            if self._prev_y is not None and self._prev_time is not None:
                dt = now - self._prev_time
                if dt > 0:
                    # Y축 좌표는 위가 0, 아래가 1이므로 아래 방향 이동 시 dy > 0
                    dy = y - self._prev_y
                    velocity = dy / dt
                    # 아래 방향 속도가 0.3 이상이며 쿨다운을 만족할 때 트리거
                    if velocity > 0.3 and (now_ms - self._last_trigger_ms) >= self._cooldown_ms:
                        should_trigger = True
            self._prev_y = y
            self._prev_time = now

        if should_trigger:
            self._audio.play_piano(note, octave, volume)
            self._last_trigger_ms = now_ms

        return {'note': note, 'octave': octave, 'volume': volume, 'triggered': should_trigger}

    def _x_to_note(self, x: float) -> tuple:
        """
        X 위치 (0.0~1.0) -> (음계 이름, 옥타브)
        2옥타브(SCALE_NOTES x2) 범위로 균등 분할
        """
        total = len(SCALE_NOTES) * 2
        idx = int(x * total)
        idx = max(0, min(idx, total - 1))
        note = SCALE_NOTES[idx % len(SCALE_NOTES)]
        octave = self.base_octave + (idx // len(SCALE_NOTES))
        return note, octave

    def set_octave(self, octave: int):
        self.base_octave = max(OCTAVE_RANGE[0], min(OCTAVE_RANGE[1], octave))
