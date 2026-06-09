# sensors/sensor_manager.py
"""
전체 센서 통합 관리 클래스.

사용 예시:
    sm = SensorManager(
        on_mode_piano=lambda: print('피아노 모드'),
        on_mode_drum=lambda: print('드럼 모드'),
        on_sleep=lambda: print('대기 모드'),
        on_wake=lambda: print('깨어남'),
        on_volume_change=lambda delta: print(f'볼륨 {delta:+d}'),
        on_encoder_press=lambda: print('엔코더 클릭'),
    )
    sm.start()
    # ...
    sm.stop()
"""
from .pir_sensor import PIRSensor
from .touch_sensor import TouchSensor
from .rotary_encoder import RotaryEncoder


class SensorManager:
    """
    PIRSensor, TouchSensor, RotaryEncoder를 하나로 묶어
    초기화·시작·종료를 일괄 관리.

    Parameters
    ----------
    on_mode_piano : callable   — 피아노 모드 전환 요청
    on_mode_drum  : callable   — 드럼 모드 전환 요청
    on_sleep      : callable   — 대기모드 진입
    on_wake       : callable   — 대기모드 해제 (PIR 재감지)
    on_volume_change : callable(delta: int) — 엔코더 회전
    on_encoder_press : callable             — 엔코더 버튼 클릭
    """

    def __init__(
        self,
        on_mode_piano=None,
        on_mode_drum=None,
        on_sleep=None,
        on_wake=None,
        on_volume_change=None,
        on_encoder_press=None,
    ):
        self.pir = PIRSensor(
            on_motion=on_wake,
            on_sleep=on_sleep,
        )
        self.touch = TouchSensor(
            on_piano=on_mode_piano,
            on_drum=on_mode_drum,
        )
        self.encoder = RotaryEncoder(
            on_rotate=on_volume_change,
            on_press=on_encoder_press,
            initial_value=50,
        )

    def start(self):
        """PIR 타임아웃 감시 스레드 시작"""
        self.pir.start()

    def notify_hand_detected(self):
        """
        카메라에서 손이 감지됐을 때 PIR 타이머를 리셋.
        (카메라 기반 활동 = 실제 사용 중으로 간주)
        """
        self.pir.reset_timer()

    def get_volume(self) -> int:
        """현재 엔코더 볼륨 값 (0~100) 반환"""
        return self.encoder.value

    def stop(self):
        """모든 센서 종료 및 GPIO 정리"""
        self.pir.stop()
        self.touch.stop()
        self.encoder.stop()
