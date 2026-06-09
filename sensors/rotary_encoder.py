# sensors/rotary_encoder.py
"""
로터리 엔코더 센서 모듈.

담당 기능:
  - CW/CCW 회전 감지 → 볼륨/감도 값 ±1 조절
  - 스위치(클릭) 감지 → 기능 토글
  - 현재 값 0~100 범위 클램프

연결 핀: BCM 23(CLK), 24(DT), 25(SW)
"""
import time
from config import ENC_CLK, ENC_DT, ENC_SW

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False


class RotaryEncoder:
    """
    로터리 엔코더 래퍼.

    Parameters
    ----------
    on_rotate : callable(delta: int)
        CW → delta=+1, CCW → delta=-1
    on_press : callable
        스위치 클릭 시 호출
    initial_value : int
        초기 값 (0~100)
    """

    def __init__(self, on_rotate=None, on_press=None, initial_value=50):
        self._on_rotate = on_rotate
        self._on_press = on_press
        self._value = max(0, min(100, initial_value))
        self._last_clk = None
        self._last_press_time = 0

        if _GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            for pin in (ENC_CLK, ENC_DT):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(ENC_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self._last_clk = GPIO.input(ENC_CLK)

            GPIO.add_event_detect(
                ENC_CLK, GPIO.BOTH,
                callback=self._clk_callback
            )
            GPIO.add_event_detect(
                ENC_SW, GPIO.FALLING,
                callback=self._sw_callback,
                bouncetime=300
            )

    def _clk_callback(self, channel):
        """CLK 에지 감지 → CW/CCW 판별"""
        clk_state = GPIO.input(ENC_CLK)
        dt_state  = GPIO.input(ENC_DT)

        if clk_state != self._last_clk:
            delta = 1 if clk_state != dt_state else -1
            self._value = max(0, min(100, self._value + delta))
            if self._on_rotate:
                self._on_rotate(delta)
        self._last_clk = clk_state

    def _sw_callback(self, channel):
        """버튼 클릭 디바운스 처리"""
        now = time.time()
        if now - self._last_press_time < 0.3:
            return
        self._last_press_time = now
        if self._on_press:
            self._on_press()

    @property
    def value(self) -> int:
        """현재 엔코더 값 (0~100)"""
        return self._value

    def set_value(self, v: int):
        """외부에서 값 강제 설정"""
        self._value = max(0, min(100, v))

    def stop(self):
        """GPIO 이벤트 감지 해제"""
        if _GPIO_AVAILABLE:
            for pin in (ENC_CLK, ENC_SW):
                GPIO.remove_event_detect(pin)
