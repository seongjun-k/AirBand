#!/bin/bash
# 콘다 환경의 python3로 AirBand를 실행합니다.

# SSH 접속 시 오디오 세션(PipeWire/PulseAudio) 연결을 위한 환경 변수 자동 설정
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
fi
if [ -z "$PULSE_SERVER" ]; then
    if [ -S "/run/user/$(id -u)/pulse/native" ]; then
        export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native
    fi
fi

# 활성화된 HDMI 오디오 카드 자동 감지 및 ALSA 다이렉트 출력 설정
HDMI_CARD=""
for card_dir in /proc/asound/card[0-9]*; do
    if [ -f "$card_dir/eld#0" ]; then
        if grep -q "speakers.*FL/FR" "$card_dir/eld#0"; then
            card_num=$(basename "$card_dir" | sed 's/card//')
            HDMI_CARD=$card_num
            break
        fi
    fi
done

if [ -n "$HDMI_CARD" ]; then
    echo "[AirBand] Active HDMI audio card detected: card $HDMI_CARD"
    export SDL_AUDIODRIVER=alsa
    export AUDIODEV="plughw:$HDMI_CARD,0"
else
    echo "[AirBand] No active HDMI audio card detected. Using default system audio."
fi

DISPLAY=:0 /home/pi/miniforge3/envs/airband/bin/python3 /home/pi/AirBand/main.py

