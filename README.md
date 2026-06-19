# AirBand

> **카메라 앞에서 손을 움직이는 것만으로 피아노, 테레민, 드럼을 연주하는 AI 공중 악기**

MediaPipe 손 인식과 Raspberry Pi GPIO를 결합하여, 실제 악기 없이도 허공에서 연주할 수 있는 인터랙티브 음악 시스템입니다.

---

## 프로젝트 개요

AirBand는 컴퓨터 비전과 임베디드 하드웨어를 결합한 실시간 공중 악기 프로젝트입니다. 웹캠 또는 Raspberry Pi 카메라로 촬영한 영상에서 MediaPipe Hands 모델이 손가락 끝 5개 좌표를 추출하고, 이를 음악 파라미터(음계, 볼륨, 움직임 속도)로 변환하여 pygame 오디오 엔진으로 즉시 재생합니다.

PyQt5 기반의 다크 테마 UI는 현재 모드, 인식된 손 위치, 재생 중인 음을 실시간으로 시각화하며, 카메라 화면 상에 직접 건반 구획과 드럼 패드 가이드라인을 매끄럽게 오버레이합니다. 피아노, 테레민, 드럼 모드는 GPIO 22에 연결된 단일 터치 스위치로 순환 전환하며, 로터리 엔코더로 옥타브와 감도를 조절할 수 있습니다. PIR 인체 감지 센서를 통해 일정 시간 사용이 없으면 자동으로 절전 모드로 전환되어 리소스를 아낍니다.

---

## 주요 기능

- **피아노 모드 (1옥타브 도~도)** — X축 8등분 건반 매핑으로 도(`C3`)부터 높은 도(`C4`)까지의 음계를 직관적인 타격(`strike`) 방식으로 연주
- **테레민 모드 (1옥타브 도~도)** — 2D 평면 상의 미세한 움직임을 감지하여 도(`C3`)부터 높은 도(`C4`)까지의 음계를 테레민 악기처럼 지속적이고 매끄러운 비브라토 톤으로 연주 (검지 Y 좌표로 볼륨 제어)
- **드럼 모드** — Y축 속도를 감지하여 hihat, clap, kick, snare 4개의 가상 드럼 패드 타격
- **비전 엔진 최적화 (30 FPS)** — `CameraThread`와 `InferenceThread`를 이중 스레드로 비동기화하고 `cv2.CAP_PROP_BUFFERSIZE = 1`을 적용하여 화면 렉(레이턴시)을 완벽히 해결
- **고해상도 픽셀 매칭** — 캡처 해상도를 `640x480`으로 격상하여 화질을 선명하게 개선하고, 스레드 단에서 RGB 변환 및 타겟 디스플레이 매칭(ROI 슬라이싱 연산)을 적용하여 GUI 스레드 부하 제로 달성
- **실시간 인터랙티브 가이드라인** — 화면에 수직 건반 구분선 및 십자 드럼 패드 경계를 오버레이하며, 손가락 위치에 따라 **호버(20% 불투명도)** 및 **타격 트리거(55% 불투명도로 Flash)** 시각적 피드백 효과 연출
- **하드웨어 연동** — PIR 인체 감지 센서(절전/자동 깨어남), 터치 스위치(GPIO 22 단일 핀 토글), 로터리 엔코더(옥타브/감도/볼륨 파라미터 순환 조절)
- **VNC 오디오 스트리밍 지원** — VNC 환경에서 소리를 듣기 위해 PipeWire의 RTP 송출 기능을 활성화하고 Windows VLC Player로 원격 청취 가능한 유니캐스트 스트리밍 기능 세팅 가이드 포함

---

## 프로젝트 구조

```
AirBand/
├── main.py                  # 진입점 — PyQt5 앱 실행
├── config.py                # 전체 상수 정의 (GPIO 핀, 카메라, 음계, 디스플레이 등)
├── requirements.txt         # Python 의존성
├── run.sh                   # libcamerify 자동 적용 실행 쉘 스크립트
├── core/
│   ├── hand_tracker.py      # MediaPipe Hands 래퍼 (왼손 끝 5점 추출 및 드로잉)
│   ├── piano_mode.py        # 피아노 1옥타브 음계 매핑 및 타격 처리기
│   ├── theremin_mode.py     # 테레민 1옥타브 음계 매핑 및 흔들기 처리기
│   ├── drum_mode.py         # 드럼 속도 기반 타격 감지기
│   └── camera_thread.py     # 카메라 캡처 및 비동기 추론 관리 스레드
├── hardware/
│   ├── gpio_handler.py      # pigpio GPIO 인터럽트 디버그 로그 및 pyqtSignal 발행
│   └── audio_engine.py      # pygame 오디오 엔진 (실시간 Sine/Noise 주파수 합성 재생)
├── ui/
│   └── main_window.py       # PyQt5 메인 윈도우 및 가이드라인 오버레이 그리기
├── assets/
│   └── NotoSansCJK-Regular.ttc # UI 한글 폰트
└── docs/                    # 추가 문서
```

---

## 동작 원리

### 피아노 모드 (도~도)
```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  ├─ X (0.0 ~ 1.0) → C장조 1옥타브 도~높은도 (8개 건반 균등 분할)
  └─ 아래 방향 속도(strike: 타격 속도 > 0.15)에 따라 타격 피아노 사운드 재생
```

### 테레민 모드 (도~도)
```
카메라 프레임 → MediaPipe 손 인식 → 검지 끝 좌표 추출
  ├─ X (0.0 ~ 1.0) → C장조 1옥타브 도~높은도 (8개 건반 균등 분할)
  ├─ Y (0.0 ~ 1.0) → 볼륨 (1.0 - y, 위로 올릴수록 크게)
  └─ 흔들기 속도(theremin: 미세 움직임 감지 > 0.008)에 따라 지속 비브라토 사운드 재생
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

### 하드웨어 이벤트 흐름
```
PIR 센서      → pir_detected       → 30초 무감지 시 절전 모드 진입 (움직임 감지 시 자동 대기 해제 및 UI 복원)
터치 스위치    → mode_toggle        → 단일 터치 핀(GPIO 22) 입력 시 피아노 ↔ 테레민 ↔ 드럼 순환 토글
로터리 엔코더  → encoder_rotated    → 옥타브(피아노, 테레민) / 감도(드럼) / 볼륨 조절
               → encoder_pressed    → 조절할 파라미터 종류 순환 (화면에 표시)
```

---

## 설치 및 실행

### 요구 사항

- Raspberry Pi 4/5 Model B + 카메라 모듈 또는 USB 웹캠
- Raspberry Pi OS (Bookworm 권장, PipeWire 오디오 디바이스 탑재)
- pigpiod 데몬 실행 필요

### 의존성 설치

```bash
# 가상환경 활성화 (Conda 또는 Venv)
# 의존성 패키지 설치
pip install mediapipe opencv-python PyQt5 pygame pigpio numpy paramiko
```

### pigpiod 데몬 시작

```bash
sudo systemctl start pigpiod
# 부팅 시 자동 시작 등록:
sudo systemctl enable pigpiod
```

### 실행

```bash
# libcamerify 래퍼가 자동으로 입혀진 실행 스크립트 구동
./run.sh
```

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

## VNC 원격 오디오 스트리밍 설정 (VLC 수신 팁)

WayVNC는 화면 공유만 지원하므로, VNC 환경에서 소리를 듣기 위해서는 네트워크 RTP 송출 설정을 이용해야 합니다.

1. **라즈베리파이 PipeWire RTP 설정**:
   `/home/pi/.config/pipewire/pipewire.conf.d/rtp-sink.conf` 파일을 다음과 같이 작성합니다 (유니캐스트 설정 예시):
   ```text
   context.modules = [
       {
           name = libpipewire-module-rtp-sink
           args = {
               destination.ip = "<수신할 Windows PC IP>"
               destination.port = 46000
               net.mtu = 1280
               sess.name = "AirBand RTP Stream"
               sess.media = "opus"
               stream.props = {
                   media.class = "Audio/Sink"
                   node.name = "rtp-sink"
                   node.description = "AirBand RTP Output"
               }
           }
       }
   ]
   ```
2. **사운드 데몬 재시작 및 기본 장치 설정**:
   ```bash
   systemctl --user restart pipewire
   # wpctl status로 AirBand RTP Output 싱크의 ID를 확인한 뒤 기본 출력으로 지정 (예: ID 36)
   wpctl set-default 36
   ```
3. **윈도우 PC(수신 측)에서 재생**:
   * 메모장을 열어 아래의 SDP 기술서 텍스트를 작성하고, `airband.sdp` 파일명으로 저장합니다:
     ```text
     v=0
     o=- 0 0 IN IP4 <라즈베리파이 IP>
     s=AirBand RTP Stream
     c=IN IP4 <수신할 Windows PC IP>
     t=0 0
     m=audio 46000 RTP/AVP 96
     a=rtpmap:96 opus/48000/2
     ```
   * 이 `airband.sdp` 파일을 윈도우 PC의 VLC Player로 열면 렉 없이 실시간 전송 사운드를 들을 수 있습니다.

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
