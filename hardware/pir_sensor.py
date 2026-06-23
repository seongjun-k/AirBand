# hardware/pir_sensor.py
try:
    import pigpio
except ImportError:
    pigpio = None
from PyQt5.QtCore import QObject, pyqtSignal
from config import PIR_PIN


class PIRSensor(QObject):
    """
    PIR 인체 감지 센서 하드웨어 모듈.
    인체 움직임 감지 시 motion_detected 시그널을 발행합니다.
    """
    motion_detected = pyqtSignal()

    def __init__(self, pi, parent=None):
        super().__init__(parent)
        self._pi = pi
        self._setup()

    def _setup(self):
        if self._pi and pigpio:
            self._pi.set_mode(PIR_PIN, pigpio.INPUT)
            self._pi.set_pull_up_down(PIR_PIN, pigpio.PUD_DOWN)
            self._pi.callback(PIR_PIN, pigpio.RISING_EDGE, self._on_trigger)

    def _on_trigger(self, gpio, level, tick):
        print(f"[GPIO-PIR] Motion Detected! Pin: {gpio}, Level: {level}")
        self.motion_detected.emit()
