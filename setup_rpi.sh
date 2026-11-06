#!/bin/bash
# ==============================================================================
# Raspberry Pi 3B Setup Script for Standalone Supercar Exhaust Synthesizer
# ==============================================================================
set -e

echo "=================================================================="
echo "🏎️  Raspberry Pi 3B Virtual Exhaust Sound System Setup"
echo "=================================================================="

# 1. Update & Install Core Dependencies
echo "[1/4] Installing system dependencies (PortAudio, CAN utilities, NumPy)..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-numpy libportaudio2 can-utils

# 2. Install Python Libraries
echo "[2/4] Installing Python audio & CAN packages..."
pip3 install --break-system-packages sounddevice python-can

# 3. Configure SocketCAN persistent startup (500 kbps, Listen-Only)
echo "[3/4] Configuring SocketCAN (can0 @ 500k Listen-Only)..."
sudo tee /etc/network/interfaces.d/can0 > /dev/null << 'EOF'
allow-hotplug can0
iface can0 can static
    bitrate 500000
    up ip link set can0 type can bitrate 500000 listen-only on
    up ip link set can0 up
    down ip link set can0 down
EOF

# Optional: Add MCP2515 overlay to /boot/firmware/config.txt if using SPI HAT
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
fi

echo "Note: If using MCP2515 SPI CAN Hat instead of PCAN-USB Pro,"
echo "ensure 'dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25' is in $CONFIG_FILE"

# 4. Install & Enable Systemd Service for Auto-Start on Vehicle Boot
echo "[4/4] Installing systemd auto-start daemon..."
CURRENT_USER=$(whoami)
APP_DIR=$(pwd)

# Replace user and path in service file dynamically
sed -i "s|User=pi|User=$CURRENT_USER|g" tuning_sound.service
sed -i "s|/home/pi/tuning_sound|$APP_DIR|g" tuning_sound.service

sudo cp tuning_sound.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tuning_sound.service

echo "=================================================================="
echo "✅ Setup Complete!"
echo ""
echo "Commands to manage your exhaust sound system:"
echo "  • Start service now:   sudo systemctl start tuning_sound.service"
echo "  • Check status:        sudo systemctl status tuning_sound.service"
echo "  • View live logs:      journalctl -u tuning_sound.service -f"
echo "  • Manual bench test:   python3 headless_engine.py --test-sweep"
echo "=================================================================="
