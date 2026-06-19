# config.py — AirBand 전체 상수 정의

# ── GPIO 핀 번호 (BCM 모드) ──
PIR_PIN     = 17
TOUCH_PIN   = 22  # 피아노/드럼 모드 토글 터치 센서 (GPIO 22)
ENC_CLK     = 23
ENC_DT      = 24
ENC_SW      = 25

# ── 카메라 설정 ──
CAMERA_INDEX = 0  # PC/노트북 웹캠 또는 라즈베리파이 카메라 인덱스
CAM_WIDTH   = 640  # 카메라 물리 캡처 가로 해상도 (기존 320 -> 640 고화질 격상)
CAM_HEIGHT  = 480  # 카메라 물리 캡처 세로 해상도
CAM_FPS     = 30

DISP_WIDTH  = 640  # 화면에 표시될 가로 해상도
DISP_HEIGHT = 480  # 화면에 표시될 세로 해상도

# ── MediaPipe 설정 ──
MP_MODEL_COMPLEXITY   = 0        # Lite 모드 (속도 우선)
MP_MAX_NUM_HANDS      = 1
MP_MIN_DETECTION_CONF = 0.5
MP_MIN_TRACKING_CONF  = 0.5
MP_TRACK_SKIP_FRAMES  = 1            # 0: 스킵 없음, 1: 1프레임 스킵 (2프레임당 1회 추론)
FINGERTIP_IDS         = [4, 8, 12, 16, 20]  # 엄지~소지 끝 index

# ── 음계 설정 ──
SCALE_NOTES    = ['C', 'D', 'E', 'F', 'G', 'A', 'B']  # C장조 다이어토닉
BASE_OCTAVE    = 3
OCTAVE_RANGE   = (2, 6)
NOTE_DURATION  = 0.18
NOTE_REPEAT_MS = 160  # 피아노 모드 음 반복 간격 (ms)

# ── 피아노 트리거 설정 ──
# 'continuous': 손을 대고 있으면 반복해서 소리 남
# 'strike': 손가락을 아래로 내릴 때 한 번 소리 남 (타격 감지)
# 'pinch': 엄지와 검지를 맞닿을 때 한 번 소리 남 (핀치 감지)
# 'theremin': 손을 움직이는 동안 소리 남 (흔들기 감지)
PIANO_TRIGGER_MODE = 'theremin'

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

# ── UI 및 화면 설정 ──
WINDOW_TITLE   = 'AirBand'
THEME_BG       = '#0d0d10'
THEME_TEXT     = '#e8e8f0'
THEME_PIANO_ACC = '#1abf8a'
THEME_DRUM_ACC  = '#e05070'
THEME_PRIMARY   = '#7c6af5'

FULLSCREEN     = False     # True: 전체화면, False: 창모드
WINDOW_WIDTH   = 1024      # 창모드 가로 크기 (QHD 환경 대응을 위해 비율 조절)
WINDOW_HEIGHT  = 720       # 창모드 세로 크기

