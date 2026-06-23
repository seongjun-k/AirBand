# hardware/rotary_encoder.py
try:
    import pigpio
except ImportError:
    pigpio = None
from PyQt5.QtCore import QObject, pyqtSignal
from config import ENC_CLK, ENC_DT, ENC_SW


class RotaryEncoder(QObject):
    """
    로터리 엔코더 하드웨어 모듈.
    엔코더 회전(rotated) 및 스위치 누름(pressed) 이벤트를 감지하여 시그널을 발행합니다.
    """
    rotated = pyqtSignal(int)
    pressed = pyqtSignal()

    def __init__(self, pi, parent=None):
        super().__init__(parent)
        self._pi = pi
        self._setup()

    def _setup(self):
        if self._pi and pigpio:
            # CLK 및 DT 핀을 입력 및 풀다운 설정
            for pin in [ENC_CLK, ENC_DT]:
                self._pi.set_mode(pin, pigpio.INPUT)
                self._pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
            
            # SW 핀은 풀업 설정 (누를 때 Low 레벨 감지)
            self._pi.set_mode(ENC_SW, pigpio.INPUT)
            self._pi.set_pull_up_down(ENC_SW, pigpio.PUD_UP)

            # pigpio 콜백 함수 바인딩
            self._pi.callback(ENC_CLK, pigpio.RISING_EDGE, self._on_rotate)
            self._pi.callback(ENC_SW, pigpio.FALLING_EDGE, self._on_press)

    def _on_rotate(self, gpio, level, tick):
        """CLK RISING_EDGE 트리거 발생 시 DT 단자 상태로 방향 판별"""
        dt = self._pi.read(ENC_DT)
        direction = -1 if dt == 0 else 1
        self.rotated.emit(direction)

    def _on_press(self, gpio, level, tick):
        self.pressed.emit()
