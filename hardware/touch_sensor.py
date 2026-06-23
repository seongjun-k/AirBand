# hardware/touch_sensor.py
try:
    import pigpio
except ImportError:
    pigpio = None
from PyQt5.QtCore import QObject, pyqtSignal
from config import TOUCH_PIN


class TouchSensor(QObject):
    """
    모드 전환용 터치 센서 하드웨어 모듈.
    스위치가 터치(RISING_EDGE)될 때 touched 시그널을 발행합니다.
    """
    touched = pyqtSignal()

    def __init__(self, pi, parent=None):
        super().__init__(parent)
        self._pi = pi
        self._setup()

    def _setup(self):
        if self._pi and pigpio:
            self._pi.set_mode(TOUCH_PIN, pigpio.INPUT)
            self._pi.set_pull_up_down(TOUCH_PIN, pigpio.PUD_DOWN)
            self._pi.callback(TOUCH_PIN, pigpio.RISING_EDGE, self._on_trigger)

    def _on_trigger(self, gpio, level, tick):
        self.touched.emit()
