# sensors/touch_sensor.py
"""
정전식 터치 버튼 센서 모듈.

담당 기능:
  - 피아노 모드 전환 버튼 (BCM 27)
  - 드럼 모드 전환 버튼  (BCM 22)
  - 디바운스(200ms) 처리

연결 핀: config.TOUCH_PIANO, config.TOUCH_DRUM
"""
import time
from config import TOUCH_PIANO, TOUCH_DRUM

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False

_DEBOUNCE_MS = 200


class TouchSensor:
    """
    2-버튼 터치 센서 래퍼.

    Parameters
    ----------
    on_piano : callable
        피아노 버튼 터치 시 호출되는 콜백
    on_drum : callable
        드럼 버튼 터치 시 호출되는 콜백
    """

    def __init__(self, on_piano=None, on_drum=None):
        self._on_piano = on_piano
        self._on_drum = on_drum
        self._last_trigger = {TOUCH_PIANO: 0, TOUCH_DRUM: 0}

        if _GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            for pin in (TOUCH_PIANO, TOUCH_DRUM):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(
                    pin, GPIO.RISING,
                    callback=self._gpio_callback,
                    bouncetime=_DEBOUNCE_MS
                )

    def _gpio_callback(self, channel):
        """GPIO 인터럽트 → 디바운스 후 콜백 호출"""
        now_ms = time.time() * 1000
        if now_ms - self._last_trigger[channel] < _DEBOUNCE_MS:
            return
        self._last_trigger[channel] = now_ms

        if channel == TOUCH_PIANO and self._on_piano:
            self._on_piano()
        elif channel == TOUCH_DRUM and self._on_drum:
            self._on_drum()

    def is_piano_pressed(self) -> bool:
        """현재 피아노 버튼 물리 입력 상태 확인 (폴링용)"""
        if _GPIO_AVAILABLE:
            return GPIO.input(TOUCH_PIANO) == GPIO.HIGH
        return False

    def is_drum_pressed(self) -> bool:
        """현재 드럼 버튼 물리 입력 상태 확인 (폴링용)"""
        if _GPIO_AVAILABLE:
            return GPIO.input(TOUCH_DRUM) == GPIO.HIGH
        return False

    def stop(self):
        """GPIO 이벤트 감지 해제"""
        if _GPIO_AVAILABLE:
            GPIO.remove_event_detect(TOUCH_PIANO)
            GPIO.remove_event_detect(TOUCH_DRUM)
