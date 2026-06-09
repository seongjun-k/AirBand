# sensors/pir_sensor.py
"""
PIR(수동 적외선) 인체 감지 센서 모듈.

담당 기능:
  - GPIO PIR 핀 초기화
  - 움직임 감지 시 콜백 호출
  - 대기모드 타임아웃 카운터 관리

연결 핀: BCM 17 (config.PIR_PIN)
"""
import time
import threading
from config import PIR_PIN, SLEEP_TIMEOUT_SEC

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False


class PIRSensor:
    """
    PIR 센서 래퍼.

    Parameters
    ----------
    on_motion : callable
        움직임 감지 시 호출되는 콜백 (인수 없음)
    on_sleep : callable
        SLEEP_TIMEOUT_SEC 동안 감지 없을 때 호출되는 콜백
    """

    def __init__(self, on_motion=None, on_sleep=None):
        self._on_motion = on_motion
        self._on_sleep = on_sleep
        self._last_motion_time = time.time()
        self._is_sleeping = False
        self._running = False
        self._thread = None

        if _GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIR_PIN, GPIO.IN)
            GPIO.add_event_detect(
                PIR_PIN, GPIO.RISING,
                callback=self._gpio_callback,
                bouncetime=300
            )

    def _gpio_callback(self, channel):
        """GPIO 인터럽트 → 움직임 감지 처리"""
        self._last_motion_time = time.time()
        if self._is_sleeping:
            self._is_sleeping = False
        if self._on_motion:
            self._on_motion()

    def start(self):
        """타임아웃 감시 스레드 시작"""
        self._running = True
        self._thread = threading.Thread(target=self._timeout_loop, daemon=True)
        self._thread.start()

    def _timeout_loop(self):
        """주기적으로 마지막 감지 시간 확인 → 대기모드 진입"""
        while self._running:
            elapsed = time.time() - self._last_motion_time
            if elapsed >= SLEEP_TIMEOUT_SEC and not self._is_sleeping:
                self._is_sleeping = True
                if self._on_sleep:
                    self._on_sleep()
            time.sleep(1.0)

    def is_active(self) -> bool:
        """현재 대기모드가 아닌 활성 상태인지 반환"""
        return not self._is_sleeping

    def reset_timer(self):
        """외부에서 마지막 동작 시간 갱신 (카메라로 손 감지 시 호출)"""
        self._last_motion_time = time.time()
        self._is_sleeping = False

    def stop(self):
        """스레드 종료 및 GPIO 정리"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if _GPIO_AVAILABLE:
            GPIO.remove_event_detect(PIR_PIN)
