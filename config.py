# config.py — AirBand 전체 상수 정의

# ── GPIO 핀 번호 (BCM 모드) ──
PIR_PIN     = 17
TOUCH_PIANO = 27
TOUCH_DRUM  = 22
ENC_CLK     = 23
ENC_DT      = 24
ENC_SW      = 25

# ── 카메라 설정 ──
CAM_WIDTH   = 320
CAM_HEIGHT  = 240
CAM_FPS     = 30

# ── MediaPipe 설정 ──
MP_MODEL_COMPLEXITY   = 0        # Lite 모드 (속도 우선)
MP_MAX_NUM_HANDS      = 2
MP_MIN_DETECTION_CONF = 0.7
MP_MIN_TRACKING_CONF  = 0.5
FINGERTIP_IDS         = [4, 8, 12, 16, 20]  # 엄지~소지 끝 index

# ── 음계 설정 ──
SCALE_NOTES    = ['C', 'D', 'E', 'F', 'G', 'A', 'B']  # C장조 다이어토닉
BASE_OCTAVE    = 3
OCTAVE_RANGE   = (2, 6)
NOTE_DURATION  = 0.18
NOTE_REPEAT_MS = 160  # 피아노 모드 음 반복 간격 (ms)

# ── 드럼 설정 ──
DRUM_PADS = {
    'hihat': {'x': (0.0, 0.5), 'y': (0.0, 0.5)},
    'clap':  {'x': (0.5, 1.0), 'y': (0.0, 0.5)},
    'kick':  {'x': (0.0, 0.5), 'y': (0.5, 1.0)},
    'snare': {'x': (0.5, 1.0), 'y': (0.5, 1.0)},
}
VELOCITY_SCALE = 2.0
MIN_VELOCITY   = 0.1

# ── 대기모드 설정 ──
SLEEP_TIMEOUT_SEC = 30

# ── 오디오 설정 ──
AUDIO_FREQUENCY = 44100
AUDIO_CHANNELS  = 2
AUDIO_BUFFER    = 512

# ── UI 설정 ──
WINDOW_TITLE   = 'AirBand'
THEME_BG       = '#0d0d10'
THEME_TEXT     = '#e8e8f0'
THEME_PIANO_ACC = '#1abf8a'
THEME_DRUM_ACC  = '#e05070'
THEME_PRIMARY   = '#7c6af5'
