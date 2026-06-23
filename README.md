# AirBand

> **카메라 앞에서 손을 움직이는 것만으로 피아노와 드럼을 연주하는 AI 공중 악기**

MediaPipe 손 인식과 Raspberry Pi GPIO를 결합하여, 실제 악기 없이도 허공에서 연주할 수 있는 인터랙티브 음악 시스템입니다.

---

## 프로젝트 개요

AirBand는 컴퓨터 비전과 임베디드 하드웨어를 결합한 실시간 공중 악기 프로젝트입니다. 웹캠 또는 Raspberry Pi 카메라로 촬영한 영상에서 MediaPipe Hands 모델이 손가락 끝 5개 좌표를 추출하고, 이를 음악 파라미터(음계, 볼륨, 타격 세기)로 변환하여 pygame 오디오 엔진으로 즉시 재생합니다.

PyQt5 기반 풀스크린 UI는 현재 모드, 인식된 손 위치, 재생 중인 음을 실시간으로 시각화합니다. 피아노 모드와 드럼 모드는 GPIO에 연결된 터치 스위치로 전환하며, 로터리 엔코더로 옥타브와 감도를 물리적으로 조절할 수 있습니다. PIR 인체 감지 센서를 통해 일정 시간 사용이 없으면 자동으로 절전 모드로 전환됩니다.

---

## 주요 기능

- **피아노 모드** — 검지 손가락의 X 위치로 C장조 1옥타브(도~도, 8키) 음계 연주, Y 위치로 볼륨 조절 및 다양한 트리거 모드(strike, pinch, continuous) 지원
- **테레민 모드** — 손의 미세한 위치 변화(X/Y축 움직임)를 감지하여 비브라토가 가미된 따뜻한 합성음 재생 (흔들기 연주)
- **드럼 모드** — 손의 Y축 속도를 감지하여 화면 4분할 패드(히햇·클랩·킥·스네어) 타격
- **손 인식** — MediaPipe Hands Lite 모델로 최대 2개 손, 비동기 추론 스레드를 통한 30 FPS 실시간 최적화 추적 및 거울 모드 지원
- **하드웨어 및 시뮬레이션 연동** — PIR 인체 감지 센서(자동 절전), 터치 센서(모드 전환), 로터리 엔코더(옥타브/감도/볼륨 제어) 연동 및 PC 개발 환경(DEVICE_MODE) 모의 구동 통합 지원
- **사용자 UI** — PyQt5 기반 다크 테마 GUI 인터페이스 (모드별 테마 컬러 및 실시간 오버레이 렌더링)

---

## 프로젝트 구조

```
AirBand/
├── main.py                  # 진입점 — PyQt5 앱 실행
├── config.py                # 전체 상수 정의 (GPIO 핀, 카메라, 음계 등)
├── requirements.txt         # Python 의존성
├── run.sh                   # 오디오 세션 환경변수 및 HDMI 카드 감지 지원 실행 스크립트
├── core/
│   ├── hand_tracker.py      # MediaPipe Hands 래퍼 (손가락 끝 5점 추출)
│   ├── piano_mode.py        # 피아노 음계 매핑 처리기
│   ├── theremin_mode.py     # 테레민 제스처 제어 처리기
│   ├── drum_mode.py         # 드럼 속도 기반 타격 감지기
│   └── camera_thread.py     # 비동기 추론(Inference) QThread를 내장한 카메라 캡처 스레드
├── hardware/
│   ├── gpio_handler.py      # GPIO 이벤트 통합 처리기 (통합 브릿지)
│   ├── pir_sensor.py        # PIR 인체 감지 센서 모듈
│   ├── touch_sensor.py      # 모드 전환 터치 센서 모듈
│   ├── rotary_encoder.py    # 파라미터 조절용 로터리 엔코더 모듈
│   └── audio_engine.py      # pygame 오디오 엔진 (실시간 음색 합성 및 샘플 재생)
├── ui/                      # PyQt5 UI 컴포넌트 (main_window.py 등)
├── assets/                  # 오디오 샘플, 아이콘 등 리소스
└── docs/                    # 추가 문서
```

---

## 동작 원리

### 피아노 모드

```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  └─ X (0.0 ~ 1.0) → C장조 1옥타브 8음계(도~도) 매핑
  └─ Y (0.0 ~ 1.0) → 볼륨 (1.0 - y, 위로 올릴수록 크게)
  └─ 트리거 설정에 따라 160ms 간격 반복 재생(continuous), 타격(strike) 또는 꼬집기(pinch) 연주
```

### 테레민 모드

```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 위치의 변화량 감지
  └─ 손의 움직임(x, y 변량)이 일정 기준 이상일 때 소리 활성화
  └─ 6Hz 비브라토 및 부드러운 감쇠 엔벨롭이 결합된 따뜻한 합성 사운드 실시간 합성 및 재생
```

### 드럼 모드

```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 Y 속도 계산
  └─ velocity = |y_curr - y_prev| / dt / VELOCITY_SCALE
  └─ (x, y) 위치 → 화면 4분할 패드 결정
       좌상: 히햇 | 우상: 클랩
       좌하: 킥   | 우하: 스네어
  └─ velocity > 0.15 이상이면 타격, 120ms 쿨다운
```

### 하드웨어 이벤트 흐름

```
PIR 센서      → pir_detected()       → 30초 무감지 시 절전 모드 (카메라 스레드 중지)
                                     → 감지 시 절전 해제 (카메라 스레드 안전 재구동)
터치 센서     → mode_toggle          → 피아노 → 테레민 → 드럼 순환 전환
로터리 엔코더  → encoder_rotated(int) → 파라미터(옥타브 / 감도 / 볼륨) 조절
               → encoder_pressed()    → 조절 대상 파라미터 순환 전환 (octave -> sensitivity -> volume)
```

---

## 설치 및 실행

### 요구 사항

- Raspberry Pi 4 Model B 또는 PC 환경
- Python 3.10
- (Raspberry Pi 구동 시) pigpiod 데몬 및 ALSA/PipeWire 오디오 드라이버 구성

### 의존성 설치

```bash
pip install -r requirements.txt
```

```
mediapipe>=0.10
opencv-python>=4.8
PyQt5>=5.15
pygame>=2.5
pigpio>=1.78
numpy>=1.24
```

### pigpiod 데몬 시작

```bash
sudo systemctl start pigpiod
# 부팅 시 자동 시작하려면:
sudo systemctl enable pigpiod
```

### 실행

```bash
python main.py
```

앱은 전체화면으로 실행됩니다. 종료하려면 `Alt+F4` 또는 UI의 종료 버튼을 사용하세요.

---

## GPIO 핀 배선 (BCM 모드)

| 컴포넌트 | BCM 핀 | 역할 |
|----------|--------|------|
| PIR 센서 | GPIO 17 | 인체 감지 (절전 해제) |
| 터치 센서 — 모드 전환 | GPIO 22 | 피아노 테레민 드럼 모드 전환 |
| 로터리 엔코더 CLK | GPIO 23 | 회전 감지 |
| 로터리 엔코더 DT | GPIO 24 | 방향 판별 |
| 로터리 엔코더 SW | GPIO 25 | 버튼 (파라미터 순환) |

---

## 설정 파라미터 (config.py)

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `SCALE_NOTES` | C D E F G A B | C장조 다이어토닉 7음 |
| `BASE_OCTAVE` | 3 | 기본 시작 옥타브 |
| `OCTAVE_RANGE` | (2, 6) | 조절 가능 범위 |
| `NOTE_DURATION` | 0.18초 | 음 지속 시간 |
| `NOTE_REPEAT_MS` | 160ms | 연속 재생 간격 |
| `PIANO_TRIGGER_MODE` | 'pinch' | 피아노 모드 연주 트리거 방식 ('pinch', 'strike', 'continuous') |
| `THEREMIN_TRIGGER_MODE` | 'theremin' | 테레민 모드 연주 트리거 방식 ('theremin', 'continuous') |
| `DEVICE_MODE` | 'pi' | 하드웨어 장치 모드 설정 ('pi' 또는 'pc') |

---

## UI 테마

| 색상 역할 | 코드 |
|-----------|------|
| 배경 | `#0d0d10` |
| 텍스트 | `#e8e8f0` |
| 피아노 강조 | `#1abf8a` |
| 테레민 강조 | `#00bcd4` |
| 드럼 강조 | `#e05070` |
| 프라이머리 | `#7c6af5` |

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
