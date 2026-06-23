# hardware/gpio_handler.py
try:
    import pigpio
except ImportError:
    pigpio = None
from PyQt5.QtCore import QObject, pyqtSignal
from hardware.pir_sensor import PIRSensor
from hardware.touch_sensor import TouchSensor
from hardware.rotary_encoder import RotaryEncoder


class GPIOHandler(QObject):
    """
    각 개별 센서 모듈들을 생성하고 통합 관리하는 GPIO 핸들러.
    상위 UI(Qt)와의 완벽한 호환성을 위해 기존과 동일한 인터페이스(pyqtSignal)를 제공합니다.
    """
    pir_detected    = pyqtSignal()
    mode_toggle     = pyqtSignal()
    encoder_rotated = pyqtSignal(int)
    encoder_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        if pigpio is None:
            raise RuntimeError(
                "pigpio 라이브러리를 임포트할 수 없습니다. 'pip install pigpio' 확인"
            )
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError(
                "pigpio 데몬 연결 실패. 'sudo systemctl start pigpiod' 확인"
            )

        # 센서별 모듈 객체 초기화 (동일한 pigpio 커넥션 참조 전달)
        self.pir = PIRSensor(self._pi, parent=self)
        self.touch = TouchSensor(self._pi, parent=self)
        self.encoder = RotaryEncoder(self._pi, parent=self)

        # 개별 센서 모듈의 이벤트를 공통 API 시그널로 릴레이 포워딩
        self.pir.motion_detected.connect(self.pir_detected.emit)
        self.touch.touched.connect(self.mode_toggle.emit)
        self.encoder.rotated.connect(self.encoder_rotated.emit)
        self.encoder.pressed.connect(self.encoder_pressed.emit)

    def cleanup(self):
        """pigpio 커넥션 정리 및 해제"""
        if self._pi:
            self._pi.stop()
