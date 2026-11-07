#!/bin/bash
# ==============================================================================
# Raspberry Pi 3B Revert / Cleanup Script
# Restores system settings, services, and packages back to original state.
# ==============================================================================
set -e

echo "=================================================================="
echo "🧹  Raspberry Pi 3B Exhaust System Cleanup & Revert"
echo "=================================================================="

# 1. Stop and Disable Systemd Service
echo "[1/4] Stopping and removing systemd service..."
if systemctl is-active --quiet tuning_sound.service 2>/dev/null; then
    sudo systemctl stop tuning_sound.service
    echo "  • Stopped active tuning_sound.service"
fi

if systemctl is-enabled --quiet tuning_sound.service 2>/dev/null; then
    sudo systemctl disable tuning_sound.service
    echo "  • Disabled tuning_sound.service"
fi

if [ -f /etc/systemd/system/tuning_sound.service ]; then
    sudo rm -f /etc/systemd/system/tuning_sound.service
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    echo "  • Removed /etc/systemd/system/tuning_sound.service"
fi

if [ -f /etc/systemd/system/bt_car_reconnect.service ]; then
    sudo systemctl stop bt_car_reconnect.service 2>/dev/null || true
    sudo systemctl disable bt_car_reconnect.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/bt_car_reconnect.service
    sudo systemctl daemon-reload
    echo "  • Removed /etc/systemd/system/bt_car_reconnect.service"
fi

# 2. Revert SocketCAN Configuration
echo "[2/4] Removing SocketCAN persistent configuration..."
if ip link show can0 2>/dev/null | grep -q "UP"; then
    sudo ip link set can0 down 2>/dev/null || true
    echo "  • Brought down can0 network interface"
fi

if [ -f /etc/network/interfaces.d/can0 ]; then
    sudo rm -f /etc/network/interfaces.d/can0
    echo "  • Removed /etc/network/interfaces.d/can0"
fi

# 3. Uninstall Python Audio & CAN Packages
echo "[3/4] Uninstalling installed Python packages (sounddevice, python-can)..."
pip3 uninstall -y sounddevice python-can 2>/dev/null || pip3 uninstall -y --break-system-packages sounddevice python-can 2>/dev/null || true
echo "  • Python packages removed"

# 4. Optional: Remove can-utils
echo "[4/4] Removing can-utils and cleaning apt cache..."
sudo apt-get remove -y can-utils 2>/dev/null || true
sudo apt-get autoremove -y 2>/dev/null || true

# Restore tuning_sound.service template placeholders
if [ -f tuning_sound.service ]; then
    git checkout tuning_sound.service 2>/dev/null || true
fi

echo "=================================================================="
echo "✅ Revert Complete! System restored to original clean state."
echo "=================================================================="
