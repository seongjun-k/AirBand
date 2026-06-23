# AirBand

> **카메라 앞에서 손을 움직이는 것만으로 피아노, 테레민, 드럼을 연주하는 AI 공중 악기**

MediaPipe 손 인식과 Raspberry Pi GPIO를 결합하여, 실제 악기 없이도 허공에서 연주할 수 있는 인터랙티브 음악 시스템입니다.

---

## 프로젝트 개요

AirBand는 컴퓨터 비전과 임베디드 하드웨어를 결합한 실시간 공중 악기 프로젝트입니다. 웹캠 또는 Raspberry Pi 카메라로 촬영한 영상에서 MediaPipe Hands 모델이 손가락 끝 5개 좌표를 추출하고, 이를 음악 파라미터(음계, 볼륨, 움직임 속도)로 변환하여 pygame 오디오 엔진으로 즉시 재생합니다.

PyQt5 기반의 다크 테마 UI는 현재 모드, 인식된 손 위치, 재생 중인 음을 실시간으로 시각화하며, 카메라 화면 상에 직접 건반 구획과 드럼 패드 가이드라인을 매끄럽게 오버레이합니다. 피아노, 테레민, 드럼 모드는 GPIO 22에 연결된 단일 터치 스위치로 순환 전환하며, 로터리 엔코더로 옥타브·감도·볼륨을 조절할 수 있습니다. PIR 인체 감지 센서를 통해 일정 시간 사용이 없으면 자동으로 절전 모드로 전환되어 리소스를 아낍니다.

---

## 주요 기능

- **피아노 모드 (1옥타브 도~도)** — X축 8등분 건반 매핑으로 도(`C3`)부터 높은 도(`C4`)까지의 음계를 직관적인 타격(`strike`) 방식으로 연주
- **테레민 모드 (1옥타브 도~도)** — 2D 평면 상의 미세한 움직임을 감지하여 도(`C3`)부터 높은 도(`C4`)까지의 음계를 테레민 악기처럼 지속적으로 연주 (검지 Y 좌표로 볼륨 제어)
- **드럼 모드** — Y축 속도를 감지하여 hihat, clap, kick, snare 4개의 가상 드럼 패드 타격
- **비전 엔진 최적화 (30 FPS)** — `CameraThread`와 `InferenceThread`를 이중 스레드로 비동기화하고 `cv2.CAP_PROP_BUFFERSIZE = 1`을 적용하여 화면 레이턴시를 최소화
- **고해상도 픽셀 매칭** — 캡처 해상도를 `640×480`으로 설정하고, 스레드 단에서 RGB 변환 및 ROI 슬라이싱 연산을 처리하여 GUI 스레드 부하 최소화
- **실시간 인터랙티브 가이드라인** — 화면에 수직 건반 구분선 및 십자 드럼 패드 경계를 오버레이하며, 손가락 위치에 따라 **호버(20% 불투명도)** 및 **타격 트리거(55% 불투명도 Flash)** 시각 피드백 연출
- **하드웨어 연동** — PIR 인체 감지 센서(절전/자동 깨어남), 터치 스위치(GPIO 22 단일 핀 토글), 로터리 엔코더(옥타브/감도/볼륨 파라미터 순환 조절)
- **절전 모드** — 30초 동안 움직임이 없으면 카메라 스레드를 정지하고 대기 화면으로 전환, PIR 감지 시 자동 복귀

---

## 프로젝트 구조

```
AirBand/
├── main.py                  # 진입점 — PyQt5 앱 실행, libcamerify 자동 적용
├── config.py                # 전체 상수 정의 (GPIO 핀, 카메라, 음계, 디스플레이, 트리거 모드 등)
├── requirements.txt         # Python 의존성
├── run.sh                   # libcamerify 자동 적용 실행 쉘 스크립트
├── install_pigpio.sh        # pigpio 라이브러리 설치 스크립트
├── test_cam_fps.py          # 카메라 FPS 측정 테스트 스크립트
├── core/
│   ├── hand_tracker.py      # MediaPipe Hands 래퍼 (왼손 끝 5점 추출 및 랜드마크 드로잉)
│   ├── piano_mode.py        # 피아노 1옥타브 음계 매핑 및 strike/pinch/continuous 트리거 처리기
│   ├── theremin_mode.py     # 테레민 1옥타브 음계 매핑 및 theremin/strike/pinch 트리거 처리기
│   ├── drum_mode.py         # Y축 속도 기반 드럼 타격 감지기 (4패드: hihat/clap/kick/snare)
│   ├── gesture_detector.py  # 핀치 판별, 손가락 펼침 카운트, 유틸리티 순수 함수 모음
│   └── camera_thread.py     # 카메라 캡처(CameraThread) + 비동기 추론(InferenceThread) 이중 스레드
├── hardware/
│   ├── gpio_handler.py      # pigpio GPIO 인터럽트 및 pyqtSignal 발행 (PIR/터치/엔코더)
│   └── audio_engine.py      # pygame 오디오 엔진 (Sine파 피아노 합성 + 드럼 WAV 재생)
├── ui/
│   └── main_window.py       # PyQt5 메인 윈도우, 모드 전환 UI, 가이드라인 오버레이 렌더링
├── assets/
│   ├── NotoSansCJK-Regular.ttc  # UI 한글 폰트 (한글 깨짐 방지)
│   └── sounds/
│       ├── hihat.wav        # 드럼 히햇 사운드
│       ├── clap.wav         # 드럼 클랩 사운드
│       ├── kick.wav         # 드럼 킥 사운드
│       └── snare.wav        # 드럼 스네어 사운드
└── docs/                    # 추가 문서
```

---

## 동작 원리

### 피아노 모드 (도~도)
```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  ├─ X (0.0 ~ 1.0) → C장조 1옥타브 도~높은도 (8개 건반 균등 분할)
  ├─ Y (0.0 ~ 1.0) → 볼륨 (1.0 - y, 위로 올릴수록 크게)
  └─ 트리거 모드 (config.PIANO_TRIGGER_MODE):
       strike     : 아래 방향 속도 > 0.15 이상 시 한 번 재생 (기본값)
       pinch      : 엄지-검지 핀치 시 한 번 재생
       continuous : NOTE_REPEAT_MS(160ms) 간격으로 반복 재생
```

### 테레민 모드 (도~도)
```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  ├─ X (0.0 ~ 1.0) → C장조 1옥타브 도~높은도 (8개 건반 균등 분할)
  ├─ Y (0.0 ~ 1.0) → 볼륨 (1.0 - y, 위로 올릴수록 크게)
  └─ 트리거 모드 (config.THEREMIN_TRIGGER_MODE):
       theremin   : 미세 2D 움직임 거리 > 0.008 이상 시 반복 재생 (기본값)
       strike     : 아래 방향 속도 > 0.15 이상 시 한 번 재생
       pinch      : 엄지-검지 핀치 시 한 번 재생
       continuous : NOTE_REPEAT_MS(160ms) 간격으로 반복 재생
```

### 드럼 모드
```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 Y 속도 계산
  ├─ velocity = |y_curr - y_prev| / dt / VELOCITY_SCALE
  ├─ (x, y) 위치 → 화면 4분할 패드 결정
  │    좌상: 히햇 | 우상: 클랩
  │    좌하: 킥   | 우하: 스네어
  └─ velocity > 0.15 이상이면 타격, 120ms 쿨다운
```

### 오디오 엔진 구조
```
AudioEngine (hardware/audio_engine.py)
  ├─ play_piano(note, octave, volume)  → numpy Sine파 합성 후 pygame.mixer 즉시 재생
  └─ play_drum(pad, velocity)          → assets/sounds/{pad}.wav 파일 로드 후 재생
```

### 하드웨어 이벤트 흐름
```
PIR 센서      → pir_detected       → 30초 무감지 시 절전 모드 진입 / 움직임 감지 시 자동 복귀
터치 스위치    → mode_toggle        → GPIO 22 입력 시 피아노 → 테레민 → 드럼 순환 토글
로터리 엔코더  → encoder_rotated    → 옥타브(피아노·테레민) / 감도(드럼) / 볼륨 조절
               → encoder_pressed    → 조절 파라미터 순환 (옥타브 → 감도 → 볼륨, 화면에 표시)
```

---

## 설치 및 실행

### 요구 사항

- Raspberry Pi 4/5 Model B + 카메라 모듈 또는 USB 웹캠
- Raspberry Pi OS (Bookworm 권장)
- pigpiod 데몬 실행 필요

### 의존성 설치

```bash
# 가상환경 활성화 (Conda 또는 venv)
pip install mediapipe opencv-python PyQt5 pygame pigpio numpy
```

### pigpiod 데몬 시작

```bash
sudo systemctl start pigpiod
# 부팅 시 자동 시작 등록
sudo systemctl enable pigpiod
```

### 실행

```bash
# libcamerify 래퍼가 자동으로 적용된 실행 스크립트
./run.sh
```

---

## config.py 주요 설정

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `CAMERA_INDEX` | `0` | 카메라 디바이스 인덱스 |
| `CAM_WIDTH / CAM_HEIGHT` | `640 / 480` | 카메라 물리 캡처 해상도 |
| `CAM_FPS` | `30` | 목표 FPS |
| `MP_MAX_NUM_HANDS` | `1` | 인식할 최대 손 개수 |
| `MP_TRACK_SKIP_FRAMES` | `1` | 추론 스킵 프레임 수 (0: 스킵 없음) |
| `BASE_OCTAVE` | `3` | 피아노/테레민 기본 옥타브 |
| `PIANO_TRIGGER_MODE` | `'strike'` | 피아노 트리거 방식 (`strike` / `pinch` / `continuous`) |
| `THEREMIN_TRIGGER_MODE` | `'theremin'` | 테레민 트리거 방식 (`theremin` / `strike` / `pinch` / `continuous`) |
| `SLEEP_TIMEOUT_SEC` | `30` | 절전 모드 진입까지 대기 시간 (초) |
| `FULLSCREEN` | `False` | 전체화면 여부 (`True`: 전체화면, `False`: 창 모드) |
| `WINDOW_WIDTH / WINDOW_HEIGHT` | `1024 / 720` | 창 모드 해상도 |

---

## GPIO 핀 배선 (BCM 모드)

| 컴포넌트 | BCM 핀 | 역할 |
|----------|--------|------|
| PIR 센서 | GPIO 17 | 인체 움직임 감지 (절전 모드 해제) |
| 터치 센서 | GPIO 22 | 피아노 🎹 ↔ 테레민 ↔ 드럼 🥁 모드 순환 토글 |
| 로터리 엔코더 CLK | GPIO 23 | 회전 감지 (CLK) |
| 로터리 엔코더 DT | GPIO 24 | 방향 판별 (DT) |
| 로터리 엔코더 SW | GPIO 25 | 버튼 클릭 (조절 파라미터 변경: 옥타브 ↔ 감도 ↔ 볼륨) |

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
