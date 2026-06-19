#!/bin/bash
# Debian 13 (Trixie) 환경에서 pigpio 데몬을 소스 빌드하여 설치하고 실행하는 스크립트입니다.
set -e

echo "=== 1. pigpio 소스 코드 다운로드 및 압축 해제 ==="
wget https://github.com/joan2937/pigpio/archive/refs/tags/v79.tar.gz -O /tmp/v79.tar.gz
tar zxf /tmp/v79.tar.gz -C /tmp
cd /tmp/pigpio-79

echo "=== 2. pigpio 빌드 ==="
make -j$(nproc)

echo "=== 3. pigpio 설치 (sudo 권한 필요) ==="
sudo make install
sudo ldconfig

echo "=== 4. pigpiod systemd 서비스 파일 생성 ==="
sudo tee /etc/systemd/system/pigpiod.service > /dev/null <<EOF
[Unit]
Description=Daemon required to control GPIO pins via pigpio
[Service]
Type=forking
ExecStart=/usr/local/bin/pigpiod -t 0 -l
Restart=always
ExecStop=/bin/systemctl kill pigpiod
[Install]
WantedBy=multi-user.target
EOF

echo "=== 5. pigpiod 서비스 활성화 및 시작 ==="
sudo systemctl daemon-reload
sudo systemctl enable pigpiod
sudo systemctl restart pigpiod

echo "=== 6. 임시 파일 정리 ==="
rm -rf /tmp/v79.tar.gz /tmp/pigpio-79

echo "=================================================="
echo "✅ pigpiod 설치 및 데몬 시작이 완료되었습니다!"
echo "=================================================="
