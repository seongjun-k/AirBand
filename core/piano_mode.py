# core/piano_mode.py
import time
import math
import config
from config import SCALE_NOTES, BASE_OCTAVE, OCTAVE_RANGE, NOTE_REPEAT_MS
from core.gesture_detector import is_pinching


class PianoProcessor:
    """
    손가락 끝 좌표 -> 음계/옥타브/볼륨 변환 처리기.

    매핑 규칙:
      - 검지 끝(tips[1]) X (0.0~1.0) -> C장조 2옥타브 범위 음계
      - 검지 끝(tips[1]) Y (0.0~1.0) -> 볼륨 (1.0 - y, 위가 크게)
      - 트리거 모드(continuous, strike, pinch, theremin)에 따라 피아노 재생
    """

    def __init__(self, audio_engine, base_octave=BASE_OCTAVE):
        self._audio = audio_engine
        self.base_octave = base_octave
        self._last_trigger_ms = 0

        # 동작 감지용 상태 변수
        self._prev_x = None
        self._prev_y = None
        self._prev_time = None
        self._was_pinching = False
        self._cooldown_ms = 160  # 타격 간 최소 간격 (config.NOTE_REPEAT_MS와 동기화)

    def process(self, fingertips: list) -> dict | None:
        """
        fingertips: [{'hand': str, 'tips': [(x,y,z)×5]}, ...]
        Returns: {'note': str, 'octave': int, 'volume': float, 'triggered': bool} or None
        """
        if not fingertips:
            self._prev_x = None
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
                    # 아래 방향 속도가 0.15 이상이며 쿨다운을 만족할 때 트리거 (감도 상향 조정)
                    if velocity > 0.15 and (now_ms - self._last_trigger_ms) >= self._cooldown_ms:
                        should_trigger = True
            self._prev_y = y
            self._prev_time = now

        elif trigger_mode == 'theremin':
            if self._prev_x is not None and self._prev_y is not None:
                # 2D 평면 상의 미세 거리 변화 감지
                dx = x - self._prev_x
                dy = y - self._prev_y
                dist = math.hypot(dx, dy)
                
                # 미세 움직임 임계치(0.008)를 충족하고 쿨다운이 끝났을 때만 소리 트리거
                if dist > 0.008 and (now_ms - self._last_trigger_ms) >= self._cooldown_ms:
                    should_trigger = True
            
            # 움직임이 있든 없든 상태 갱신
            self._prev_x = x
            self._prev_y = y

        if should_trigger:
            self._audio.play_piano(note, octave, volume)
            self._last_trigger_ms = now_ms

        return {'note': note, 'octave': octave, 'volume': volume, 'triggered': should_trigger}

    def _x_to_note(self, x: float) -> tuple:
        """
        X 위치 (0.0~1.0) -> (음계 이름, 옥타브)
        1옥타브 다이어토닉 '도~도' (총 8개 건반) 균등 분할
        """
        total_keys = 8
        idx = int(x * total_keys)
        idx = max(0, min(idx, total_keys - 1))
        
        # 8번째 건반(index 7)은 다음 옥타브의 C (높은 도)
        if idx == 7:
            note = 'C'
            octave = self.base_octave + 1
        else:
            note = SCALE_NOTES[idx]
            octave = self.base_octave
            
        return note, octave

    def set_octave(self, octave: int):
        self.base_octave = max(OCTAVE_RANGE[0], min(OCTAVE_RANGE[1], octave))
