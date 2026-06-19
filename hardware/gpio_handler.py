# hardware/gpio_handler.py
try:
    import pigpio
except ImportError:
    pigpio = None
from PyQt5.QtCore import QObject, pyqtSignal
from config import PIR_PIN, TOUCH_PIN, ENC_CLK, ENC_DT, ENC_SW


class GPIOHandler(QObject):
    """
    pigpio 기반 GPIO 인터럽트 처리.
    이벤트를 pyqtSignal로 발행 → 메인 스레드(Qt)에서 안전하게 처리.

    Signals:
        pir_detected()       : PIR 인체 감지
        mode_changed(str)    : 모드 전환 ('piano' | 'drum')
        encoder_rotated(int) : 엔코더 회전 (+1 시계, -1 반시계)
        encoder_pressed()    : 엔코더 버튼 (파라미터 순환)
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
                "pigpio 데실 연결 실패. 'sudo systemctl start pigpiod' 확인"
            )
        self._setup_pins()
        self._register_callbacks()
        self._enc_last_clk = self._pi.read(ENC_CLK)

    def _setup_pins(self):
        for pin in [PIR_PIN, TOUCH_PIN, ENC_CLK, ENC_DT]:
            self._pi.set_mode(pin, pigpio.INPUT)
            self._pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        self._pi.set_mode(ENC_SW, pigpio.INPUT)
        self._pi.set_pull_up_down(ENC_SW, pigpio.PUD_UP)  # 버튼은 풀업

    def _register_callbacks(self):
        self._pi.callback(PIR_PIN,   pigpio.RISING_EDGE,  self._on_pir)
        self._pi.callback(TOUCH_PIN, pigpio.RISING_EDGE,  self._on_touch)
        self._pi.callback(ENC_CLK,   pigpio.EITHER_EDGE,  self._on_encoder)
        self._pi.callback(ENC_SW,    pigpio.FALLING_EDGE, self._on_enc_btn)

    def _on_pir(self, gpio, level, tick):
        print(f"[GPIO] PIR Motion Detected! Pin: {gpio}, Level: {level}")
        self.pir_detected.emit()

    def _on_touch(self, gpio, level, tick):
        self.mode_toggle.emit()

    def _on_encoder(self, gpio, level, tick):
        """CLK/DT 위상 차로 회전 방향 감지"""
        clk = self._pi.read(ENC_CLK)
        dt  = self._pi.read(ENC_DT)
        if clk != self._enc_last_clk:
            direction = -1 if clk != dt else 1
            self.encoder_rotated.emit(direction)
        self._enc_last_clk = clk

    def _on_enc_btn(self, gpio, level, tick):
        self.encoder_pressed.emit()

    def cleanup(self):
        self._pi.stop()
