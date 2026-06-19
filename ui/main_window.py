# ui/main_window.py
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont

from core.camera_thread import CameraThread
from core.theremin_mode import ThereminProcessor
from core.drum_mode import DrumProcessor
from hardware.gpio_handler import GPIOHandler
from hardware.audio_engine import AudioEngine
from config import (
    THEME_BG, THEME_TEXT, THEME_THEREMIN_ACC,
    THEME_DRUM_ACC, THEME_PRIMARY, SLEEP_TIMEOUT_SEC,
    DISP_WIDTH, DISP_HEIGHT, SCALE_NOTES
)


class MainWindow(QMainWindow):
    """
    AirBand PyQt5 메인 윈도우.

    레이아웃:
      ┌─────────────────────────────────────┐
      │  HEADER: 로고 + 모드 전환 버튼 + 파라미터 표시  │
      ├──────────────────┬──────────────────┤
      │ 카메라 빰  (640px) │ 상태 패널          │
      └──────────────────┴──────────────────┘
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AirBand')
        self.setStyleSheet(f'background-color: {THEME_BG}; color: {THEME_TEXT};')

        self.mode           = 'theremin'
        self.current_param  = 'octave'
        self.base_octave    = 3
        self.sensitivity    = 2.0
        self.volume         = 70
        self._sleep_count   = 0
        self.is_sleeping    = False

        self._audio         = AudioEngine()
        self._theremin_proc = ThereminProcessor(self._audio)
        self._drum_proc     = DrumProcessor(self._audio)

        self._build_ui()
        self._start_camera()
        self._init_gpio()

        self._sleep_timer = QTimer()
        self._sleep_timer.timeout.connect(self._check_sleep)
        self._sleep_timer.start(1000)

    # ── UI 빌드 ──
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._build_header())
        layout.addLayout(self._build_body())

    def _build_header(self):
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(4, 4, 4, 4)

        title = QLabel('AirBand')
        title.setFont(QFont('sans-serif', 16, QFont.Bold))
        title.setStyleSheet(f'color: {THEME_PRIMARY};')
        row.addWidget(title)
        row.addStretch()

        self._theremin_btn = QPushButton('테레민')
        self._drum_btn     = QPushButton('드럼')
        inactive = 'background:#1a1a22;border:1px solid #2a2a38;border-radius:6px;padding:0 16px;color:#7878a0;'
        for btn in [self._theremin_btn, self._drum_btn]:
            btn.setFixedHeight(36)
            btn.setStyleSheet(inactive)
        self._theremin_btn.clicked.connect(lambda: self._on_mode_change('theremin'))
        self._drum_btn.clicked.connect(lambda: self._on_mode_change('drum'))
        row.addWidget(self._theremin_btn)
        row.addWidget(self._drum_btn)

        self._param_label = QLabel(f'[{self.current_param}]')
        self._param_label.setStyleSheet(f'color:{THEME_PRIMARY};font-size:12px;')
        row.addWidget(self._param_label)
        return header

    def _build_body(self):
        body = QHBoxLayout()
        body.setSpacing(8)

        self._cam_label = QLabel()
        self._cam_label.setFixedSize(DISP_WIDTH, DISP_HEIGHT)
        self._cam_label.setStyleSheet('border:1px solid #2a2a38;border-radius:8px;')
        body.addWidget(self._cam_label)

        panel = QWidget()
        playout = QVBoxLayout(panel)
        playout.setSpacing(8)

        self._note_label = QLabel('—')
        self._note_label.setAlignment(Qt.AlignCenter)
        self._note_label.setFont(QFont('sans-serif', 48, QFont.Bold))
        self._note_label.setStyleSheet(f'color:{THEME_THEREMIN_ACC};')
        playout.addWidget(self._note_label)

        self._detail_label = QLabel('손을 카메라 앞에서 움직여보세요')
        self._detail_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setStyleSheet('color:#7878a0;font-size:11px;')
        playout.addWidget(self._detail_label)
        playout.addStretch()

        body.addWidget(panel, 1)
        return body

    # ── 초기화 ──
    def _start_camera(self):
        self._cam_thread = CameraThread()
        self._cam_thread.frame_ready.connect(self._on_frame)
        self._cam_thread.start()

    def _init_gpio(self):
        try:
            self._gpio = GPIOHandler()
            self._gpio.pir_detected.connect(self._on_pir)
            self._gpio.mode_toggle.connect(self._on_mode_toggle)
            self._gpio.encoder_rotated.connect(self._on_encoder)
            self._gpio.encoder_pressed.connect(self._on_enc_btn)
        except Exception as e:
            print(f'[GPIO 경고] {e}')
            self._gpio = None

    # ── 슬롯 ──
    @pyqtSlot(object, object)
    def _on_frame(self, rgb_frame: np.ndarray, fingertips: list):
        if fingertips:
            self._sleep_count = 0

        if self.is_sleeping:
            return

        h, w, ch = rgb_frame.shape

        # ── 테레민 건반 구분선 및 타격 하이라이트 렌더링 ──
        if self.mode == 'theremin':
            total_keys = 8  # 1옥타브 도~도 (8칸)
            key_width = w / total_keys
            
            # 테레민 분석 처리 호출
            result = self._theremin_proc.process(fingertips)
            
            active_idx = None
            is_triggered = False
            if fingertips:
                hand = fingertips[0]
                x, y, z = hand['tips'][1]  # 검지 끝 좌표
                active_idx = int(max(0.0, min(0.999, x)) * total_keys)
                if result and result.get('triggered', False):
                    is_triggered = True
                
                # 해당 건반 영역 반투명 하이라이트 (ROI 슬라이싱 최적화로 메모리 재할당 차단)
                x_start = int(active_idx * key_width)
                x_end = int((active_idx + 1) * key_width)
                
                alpha = 0.55 if is_triggered else 0.2
                color = (245, 106, 124) if is_triggered else (138, 191, 26)  # RGB
                
                # 활성화된 슬롯 부위만 크롭하여 연산
                roi = rgb_frame[0:h, x_start:x_end]
                overlay = np.full_like(roi, color)
                cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
            
            # 세로 건반 경계선 및 음이름 텍스트 오버레이
            for i in range(total_keys):
                x_pos = int(i * key_width)
                if i > 0:
                    cv2.line(rgb_frame, (x_pos, 0), (x_pos, h), (80, 80, 90), 1)
                
                # 8번째 칸은 높은 도(C + 1옥타브)
                if i == 7:
                    note = 'C'
                    octave = self.base_octave + 1
                else:
                    note = SCALE_NOTES[i]
                    octave = self.base_octave
                    
                text = f"{note}{octave}"
                cx = int((i + 0.5) * key_width)
                cv2.putText(rgb_frame, text, (cx - 10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (220, 220, 220), 1, cv2.LINE_AA)
            
            if result:
                self._note_label.setText(f"{result['note']}{result['octave']}")
                self._detail_label.setText(
                    f"Vol {result['volume']*100:.0f}%  |  옥타브 {result['octave']}"
                )
        else:
            # 드럼 분석 처리 호출
            hits = self._drum_proc.process(fingertips)
            
            active_pad = None
            if fingertips:
                hand = fingertips[0]
                x, y, z = hand['tips'][1]
                
                is_hit = len(hits) > 0
                if is_hit:
                    active_pad = hits[0]['pad']
                else:
                    if x < 0.5 and y < 0.5: active_pad = 'hihat'
                    elif x >= 0.5 and y < 0.5: active_pad = 'clap'
                    elif x < 0.5 and y >= 0.5: active_pad = 'kick'
                    else: active_pad = 'snare'
                
                rects = {
                    'hihat': (0, 0, w//2, h//2),
                    'clap':  (w//2, 0, w, h//2),
                    'kick':  (0, h//2, w//2, h),
                    'snare': (w//2, h//2, w, h),
                }
                rect = rects.get(active_pad)
                if rect:
                    alpha = 0.55 if is_hit else 0.2
                    color = (224, 80, 112) if is_hit else (180, 60, 90)  # RGB
                    
                    # ROI 슬라이싱 최적화로 드럼 패드 부분만 연산
                    roi = rgb_frame[rect[1]:rect[3], rect[0]:rect[2]]
                    overlay = np.full_like(roi, color)
                    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
            
            # 십자 분할선 렌더링
            cv2.line(rgb_frame, (0, h//2), (w, h//2), (80, 80, 90), 1)
            cv2.line(rgb_frame, (w//2, 0), (w//2, h), (80, 80, 90), 1)
            
            # 패드 라벨 표시
            labels = [
                ("HI-HAT", (15, 25)),
                ("CLAP", (w//2 + 15, 25)),
                ("KICK", (15, h//2 + 25)),
                ("SNARE", (w//2 + 15, h//2 + 25))
            ]
            for text, pos in labels:
                cv2.putText(rgb_frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
            
            if hits:
                pads = ', '.join(h['pad'].upper() for h in hits)
                self._note_label.setText(pads)
                self._detail_label.setText(f"velocity {hits[0]['velocity']*100:.0f}%")

        # UI에 최종 영상 출력
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self._cam_label.setPixmap(QPixmap.fromImage(qimg))

    @pyqtSlot()
    def _on_mode_toggle(self):
        new_mode = 'drum' if self.mode == 'theremin' else 'theremin'
        self._on_mode_change(new_mode)

    @pyqtSlot(str)
    def _on_mode_change(self, mode: str):
        self.mode = mode
        acc = THEME_THEREMIN_ACC if mode == 'theremin' else THEME_DRUM_ACC
        self._note_label.setStyleSheet(f'color:{acc};')
        active   = f'background:{acc}22;border:1px solid {acc};border-radius:6px;padding:0 16px;color:{acc};'
        inactive = 'background:#1a1a22;border:1px solid #2a2a38;border-radius:6px;padding:0 16px;color:#7878a0;'
        if mode == 'theremin':
            self._theremin_btn.setStyleSheet(active)
            self._drum_btn.setStyleSheet(inactive)
        else:
            self._drum_btn.setStyleSheet(active)
            self._theremin_btn.setStyleSheet(inactive)

    @pyqtSlot()
    def _on_pir(self):
        print(f"[UI] PIR Event Received. Current sleep status: {self.is_sleeping}")
        self._sleep_count = 0
        if self.is_sleeping:
            self.is_sleeping = False
            self._note_label.setText('—')
            self._detail_label.setText('손을 카메라 앞에서 움직여보세요')
            self._cam_thread.running = True
            self._cam_thread.start()

    @pyqtSlot(int)
    def _on_encoder(self, direction: int):
        if self.current_param == 'octave':
            self.base_octave = max(2, min(6, self.base_octave + direction))
            self._theremin_proc.set_octave(self.base_octave)
            self._param_label.setText(f'[옥타브 {self.base_octave}]')
        elif self.current_param == 'sensitivity':
            self.sensitivity = round(max(0.5, min(5.0, self.sensitivity + direction * 0.2)), 1)
            self._drum_proc.set_sensitivity(self.sensitivity)
            self._param_label.setText(f'[감도 {self.sensitivity}]')
        elif self.current_param == 'volume':
            self.volume = max(0, min(100, self.volume + direction * 5))
            self._audio.set_volume(self.volume)
            self._param_label.setText(f'[볼륨 {self.volume}%]')

    @pyqtSlot()
    def _on_enc_btn(self):
        params = ['octave', 'sensitivity', 'volume']
        idx = params.index(self.current_param)
        self.current_param = params[(idx + 1) % len(params)]
        self._param_label.setText(f'[{self.current_param}]')

    def _check_sleep(self):
        self._sleep_count += 1
        if self._sleep_count >= SLEEP_TIMEOUT_SEC and not self.is_sleeping:
            self.is_sleeping = True
            self._cam_thread.running = False
            self._note_label.setText('절전 대기')
            self._detail_label.setText('손을 보여주거나 움직임이 감지되면 활성화됩니다')

    def closeEvent(self, event):
        self._cam_thread.stop()
        if self._gpio:
            self._gpio.cleanup()
        self._audio.close()
        event.accept()
