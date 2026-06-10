# AirBand

> **카메라 앞에서 손을 움직이는 것만으로 피아노와 드럼을 연주하는 AI 공중 악기**

MediaPipe 손 인식과 Raspberry Pi GPIO를 결합하여, 실제 악기 없이도 허공에서 연주할 수 있는 인터랙티브 음악 시스템입니다.

---

## 프로젝트 개요

AirBand는 컴퓨터 비전과 임베디드 하드웨어를 결합한 실시간 공중 악기 프로젝트입니다. 웹캠 또는 Raspberry Pi 카메라로 촬영한 영상에서 MediaPipe Hands 모델이 손가락 끝 5개 좌표를 추출하고, 이를 음악 파라미터(음계, 볼륨, 타격 세기)로 변환하여 pygame 오디오 엔진으로 즉시 재생합니다.

PyQt5 기반 풀스크린 UI는 현재 모드, 인식된 손 위치, 재생 중인 음을 실시간으로 시각화합니다. 피아노 모드와 드럼 모드는 GPIO에 연결된 터치 스위치로 전환하며, 로터리 엔코더로 옥타브와 감도를 물리적으로 조절할 수 있습니다. PIR 인체 감지 센서를 통해 일정 시간 사용이 없으면 자동으로 절전 모드로 전환됩니다.

---

## 주요 기능

- **피아노 모드** — 검지 손가락의 X 위치로 C장조 2옥타브 음계 연주, Y 위치로 볼륨 조절
- **드럼 모드** — 손의 Y축 속도를 감지하여 히햇·클랩·킥·스네어 4패드 타격
- **손 인식** — MediaPipe Hands Lite 모델로 최대 2개 손, 30 FPS 실시간 추적
- **하드웨어 연동** — PIR 인체 감지 센서(자동 절전), 터치 스위치(모드 전환), 로터리 엔코더(옥타브/감도 조절)
- **풀스크린 UI** — PyQt5 기반 다크 테마 인터페이스

---

## 프로젝트 구조

```
AirBand/
├── main.py                  # 진입점 — PyQt5 앱 실행
├── config.py                # 전체 상수 정의 (GPIO 핀, 카메라, 음계 등)
├── requirements.txt         # Python 의존성
├── core/
│   ├── hand_tracker.py      # MediaPipe Hands 래퍼 (손가락 끝 5점 추출)
│   ├── piano_mode.py        # 피아노 음계 매핑 처리기
│   ├── drum_mode.py         # 드럼 속도 기반 타격 감지기
│   └── camera_thread.py     # 카메라 캡처 QThread
├── hardware/
│   ├── gpio_handler.py      # pigpio GPIO 인터럽트 → pyqtSignal 발행
│   └── audio_engine.py      # pygame 오디오 엔진 (피아노/드럼 재생)
├── ui/                      # PyQt5 UI 컴포넌트
├── assets/                  # 오디오 샘플, 아이콘 등 리소스
└── docs/                    # 추가 문서
```

---

## 동작 원리

### 피아노 모드

```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  └─ X (0.0 ~ 1.0) → C장조 2옥타브 14음계 매핑
  └─ Y (0.0 ~ 1.0) → 볼륨 (1.0 - y, 위로 올릴수록 크게)
  └─ 160ms 간격으로 해당 음 반복 재생
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
PIR 센서      → pir_detected()       → 30초 무감지 시 절전 모드
터치 스위치    → mode_changed(str)    → piano / drum 전환
로터리 엔코더  → encoder_rotated(int) → 옥타브(피아노) / 감도(드럼) 조절
               → encoder_pressed()    → 조절 파라미터 순환
```

---

## 설치 및 실행

### 요구 사항

- Raspberry Pi 4 Model B 4GB + 카메라 모듈 또는 USB 웹캠
- Python 3.10
- pigpiod 데몬 실행 필요

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
| 터치 센서 — 모드 전환 | GPIO 27 | 피아노 드럼 모드 전환 |
| 로터리 엔코더 CLK | GPIO 23 | 회전 감지 |
| 로터리 엔코더 DT | GPIO 24 | 방향 판별 |
| 로터리 엔코더 SW | GPIO 25 | 버튼 (파라미터 순환) |

---

## 음계 설정

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `SCALE_NOTES` | C D E F G A B | C장조 다이어토닉 7음 |
| `BASE_OCTAVE` | 3 | 기본 시작 옥타브 |
| `OCTAVE_RANGE` | (2, 6) | 조절 가능 범위 |
| `NOTE_DURATION` | 0.18초 | 음 지속 시간 |
| `NOTE_REPEAT_MS` | 160ms | 연속 재생 간격 |

---

## UI 테마

| 색상 역할 | 코드 |
|-----------|------|
| 배경 | `#0d0d10` |
| 텍스트 | `#e8e8f0` |
| 피아노 강조 | `#1abf8a` |
| 드럼 강조 | `#e05070` |
| 프라이머리 | `#7c6af5` |

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
