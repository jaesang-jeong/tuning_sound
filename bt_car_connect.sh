#!/bin/bash
# ==============================================================================
# Raspberry Pi 3B Vehicle Bluetooth Audio (A2DP) Auto-Pairing & Reconnect Tool
# ==============================================================================
set -e

echo "=================================================================="
echo "🚗  Raspberry Pi 3B -> Vehicle Bluetooth Audio Pairing Helper"
echo "=================================================================="

# Ensure Bluetooth service is up
sudo systemctl start bluetooth 2>/dev/null || true
sudo rfkill unblock bluetooth 2>/dev/null || true

echo "[1/4] Scanning for nearby Bluetooth devices for 10 seconds..."
echo "👉 차량 내비게이션/오디오의 [기기 등록 / 신규 연결] 화면을 띄워주세요!"

# Start discovery
bluetoothctl --timeout 10 scan on > /tmp/bt_scan.log 2>&1 || true

echo ""
echo "[2/4] Discovered Bluetooth Audio Devices:"
echo "------------------------------------------------------------------"
bluetoothctl devices | while read -r line; do
    echo "  $line"
done
echo "------------------------------------------------------------------"

echo ""
read -p "차량의 블루투스 MAC 주소를 입력하세요 (예: AA:BB:CC:DD:EE:FF): " CAR_MAC

if [ -z "$CAR_MAC" ]; then
    echo "❌ MAC 주소가 입력되지 않았습니다. 취소되었습니다."
    exit 1
fi

echo ""
echo "[3/4] Pairing and Trusting $CAR_MAC..."
echo "• 차량 모니터에 페어링 확인(PIN 번호) 창이 뜨면 '확인'을 눌러주세요."

bluetoothctl pair "$CAR_MAC" || true
bluetoothctl trust "$CAR_MAC"
bluetoothctl connect "$CAR_MAC" || true

echo ""
echo "[4/4] Configuring persistent auto-reconnect on vehicle boot..."

# Create a systemd service to automatically reconnect to this car on every boot
SERVICE_PATH="/etc/systemd/system/bt_car_reconnect.service"
sudo tee "$SERVICE_PATH" > /dev/null << EOF
[Unit]
Description=Auto Reconnect to Vehicle Bluetooth Audio
After=bluetooth.target sound.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bluetoothctl connect $CAR_MAC
RemainAfterExit=yes
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bt_car_reconnect.service

echo "=================================================================="
echo "✅ 블루투스 연결 및 자동 재연결 설정 완료!"
echo "• 등록된 차량 MAC: $CAR_MAC"
echo "• 이제 차량 시동을 켜면 라즈베리파이가 자동으로 차량 오디오로 연결됩니다."
echo "• 연결 테스트: python3 -c \"import sounddevice as sd; print(sd.query_devices())\""
echo "=================================================================="
