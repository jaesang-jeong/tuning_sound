#!/bin/bash
# ==============================================================================
# Raspberry Pi 3B Boot Speed Optimization Script for Vehicle Sound System
# Reduces boot-to-sound latency from ~18-25s down to ~4-6s!
# ==============================================================================
set -e

echo "=================================================================="
echo "⚡  Raspberry Pi 3B Boot Speed Optimizer (Vehicle Engine Sound)"
echo "=================================================================="

# Detect config & cmdline paths (Debian Bookworm uses /boot/firmware/)
if [ -f /boot/firmware/config.txt ]; then
    BOOT_DIR="/boot/firmware"
else
    BOOT_DIR="/boot"
fi

CONFIG_TXT="$BOOT_DIR/config.txt"
CMDLINE_TXT="$BOOT_DIR/cmdline.txt"

# 1. Disable Network Wait-Online Services (Saves ~5 to 10 seconds!)
echo "[1/5] Disabling network-wait-online blockers (sound works 100% offline)..."
sudo systemctl mask systemd-networkd-wait-online.service 2>/dev/null || true
sudo systemctl mask NetworkManager-wait-online.service 2>/dev/null || true
echo "  • Network wait-online masked."

# 2. Disable Non-Essential Background Services & Timers
echo "[2/5] Disabling non-essential services & apt background timers..."
SERVICES_TO_DISABLE=(
    "apt-daily.timer"
    "apt-daily-upgrade.timer"
    "man-db.timer"
    "ModemManager.service"
    "triggerhappy.service"
    "keyboard-setup.service"
    "console-setup.service"
)

for s in "${SERVICES_TO_DISABLE[@]}"; do
    sudo systemctl disable "$s" 2>/dev/null || true
    echo "  • Disabled $s"
done

# 3. Optimize Firmware Config (boot_delay=0, initial_turbo=30)
echo "[3/5] Optimizing $CONFIG_TXT for instant boot..."
if [ -f "$CONFIG_TXT" ]; then
    sudo grep -q "boot_delay=0" "$CONFIG_TXT" || echo "boot_delay=0" | sudo tee -a "$CONFIG_TXT" > /dev/null
    sudo grep -q "disable_splash=1" "$CONFIG_TXT" || echo "disable_splash=1" | sudo tee -a "$CONFIG_TXT" > /dev/null
    sudo grep -q "initial_turbo=30" "$CONFIG_TXT" || echo "initial_turbo=30" | sudo tee -a "$CONFIG_TXT" > /dev/null
    echo "  • Configured boot_delay=0, disable_splash=1, initial_turbo=30."
fi

# 4. Optimize Kernel Command Line (quiet, fastboot, fsck.mode=skip)
echo "[4/5] Optimizing $CMDLINE_TXT (silent console & fastboot)..."
if [ -f "$CMDLINE_TXT" ]; then
    CURRENT_CMDLINE=$(cat "$CMDLINE_TXT")
    NEW_CMDLINE="$CURRENT_CMDLINE"
    
    for param in "quiet" "loglevel=3" "fastboot" "fsck.mode=skip"; do
        if ! echo "$NEW_CMDLINE" | grep -qw "$param"; then
            NEW_CMDLINE="$NEW_CMDLINE $param"
        fi
    done
    
    echo "$NEW_CMDLINE" | sudo tee "$CMDLINE_TXT" > /dev/null
    echo "  • Injected quiet fastboot parameters."
fi

# 5. Precompile Python Bytecode & Install Real-Time Service
echo "[5/5] Pre-compiling Python bytecode (.pyc) and updating service priority..."
python3 -m compileall -q . 2>/dev/null || true

# Apply updated real-time service unit
CURRENT_USER=$(whoami)
APP_DIR=$(pwd)
sed -i "s|User=pi|User=$CURRENT_USER|g" tuning_sound.service
sed -i "s|/home/pi/tuning_sound|$APP_DIR|g" tuning_sound.service

sudo cp tuning_sound.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tuning_sound.service

echo "=================================================================="
echo "⚡ Optimization Complete!"
echo "• Reboot now to apply: sudo reboot"
echo "• After reboot, measure your ultra-fast boot time with:"
echo "    systemd-analyze"
echo "    systemd-analyze blame"
echo "=================================================================="
