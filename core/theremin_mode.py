# core/theremin_mode.py
import time
import math
import config
from config import SCALE_NOTES, BASE_OCTAVE, OCTAVE_RANGE, NOTE_REPEAT_MS
from core.gesture_detector import is_pinching


class ThereminProcessor:
    """
    손가락 끝 좌표 -> 음계/옥타브/볼륨 변환 처리기.

    매핑 규칙:
      - 검지 끝(tips[1]) X (0.0~1.0) -> C장조 2옥타브 범위 음계
      - 검지 끝(tips[1]) Y (0.0~1.0) -> 볼륨 (1.0 - y, 위가 크게)
      - 트리거 모드(continuous, strike, pinch, theremin)에 따라 테레민 재생
    """

    def __init__(self, audio_engine, base_octave=BASE_OCTAVE):
        self._audio = audio_engine
        self.base_octave = base_octave
        self._last_trigger_ms = {}  # hand_label -> last_trigger_ms
        self._prev_x = {}           # hand_label -> x
        self._prev_y = {}           # hand_label -> y
        self._prev_time = {}        # hand_label -> time
        self._was_pinching = {}     # hand_label -> bool
        self._cooldown_ms = 160  # 타격 간 최소 간격 (config.NOTE_REPEAT_MS와 동기화)

    def process(self, fingertips: list) -> list:
        """
        fingertips: [{'hand': str, 'tips': [(x,y,z)×5]}, ...]
        Returns: [{'note': str, 'octave': int, 'volume': float, 'triggered': bool, 'hand': str}, ...]
        """
        if not fingertips:
            self._prev_x.clear()
            self._prev_y.clear()
            self._prev_time.clear()
            self._was_pinching.clear()
            return []

        results = []
        now = time.time()
        now_ms = now * 1000
        trigger_mode = getattr(config, 'THEREMIN_TRIGGER_MODE', 'theremin')

        for hand in fingertips:
            label = hand['hand']
            x, y, _ = hand['tips'][1]  # 검지 끝 (landmark 8)

            note, octave = self._x_to_note(x)
            volume = max(0.0, min(1.0, 1.0 - y))

            should_trigger = False

            if trigger_mode == 'continuous':
                last_t = self._last_trigger_ms.get(label, 0)
                if now_ms - last_t >= NOTE_REPEAT_MS:
                    should_trigger = True

            elif trigger_mode == 'pinch':
                tx, ty, _ = hand['tips'][0]
                ix, iy, _ = hand['tips'][1]
                dist = math.hypot(tx - ix, ty - iy)
                
                currently_pinched = self._was_pinching.get(label, False)
                if currently_pinched:
                    if dist > 0.09:
                        self._was_pinching[label] = False
                else:
                    last_t = self._last_trigger_ms.get(label, 0)
                    if dist < 0.06 and (now_ms - last_t) >= self._cooldown_ms:
                        should_trigger = True
                        self._was_pinching[label] = True

            elif trigger_mode == 'strike':
                prev_y = self._prev_y.get(label)
                prev_time = self._prev_time.get(label)
                if prev_y is not None and prev_time is not None:
                    dt = now - prev_time
                    if dt > 0:
                        dy = y - prev_y
                        velocity = dy / dt
                        last_t = self._last_trigger_ms.get(label, 0)
                        if velocity > 0.15 and (now_ms - last_t) >= self._cooldown_ms:
                            should_trigger = True
                self._prev_y[label] = y
                self._prev_time[label] = now

            elif trigger_mode == 'theremin':
                prev_x = self._prev_x.get(label)
                prev_y = self._prev_y.get(label)
                if prev_x is not None and prev_y is not None:
                    dx = x - prev_x
                    dy = y - prev_y
                    dist = math.hypot(dx, dy)
                    last_t = self._last_trigger_ms.get(label, 0)
                    if dist > 0.008 and (now_ms - last_t) >= self._cooldown_ms:
                        should_trigger = True
                self._prev_x[label] = x
                self._prev_y[label] = y

            if should_trigger:
                self._audio.play_theremin(note, octave, volume)
                self._last_trigger_ms[label] = now_ms

            results.append({
                'note': note,
                'octave': octave,
                'volume': volume,
                'triggered': should_trigger,
                'pressed': self._was_pinching.get(label, False) if trigger_mode == 'pinch' else should_trigger,
                'hand': label
            })

        return results

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
