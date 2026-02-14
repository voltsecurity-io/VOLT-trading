#!/bin/bash
# VOLT Trading - 24/7 System Optimization for ThinkPad X1 Nano
# Run with: sudo bash setup_24h.sh

set -e

echo "=============================================="
echo "VOLT Trading - 24/7 System Optimization"
echo "ThinkPad X1 Nano Intel Evo i7-1160G7"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup_24h.sh"
    exit 1
fi

# Check AC power
AC_STATUS=$(cat /sys/class/power_supply/AC*/online 2>/dev/null || echo "0")
if [ "$AC_STATUS" = "0" ]; then
    echo ""
    echo "WARNING: Laptop is NOT plugged in!"
    echo "For 24/7 operation, please connect the AC adapter."
    echo ""
fi

echo ""
echo "[1/4] Configuring power management..."

# Prevent sleep on lid close when on AC
mkdir -p /etc/systemd/logind.conf.d/
cat > /etc/systemd/logind.conf.d/volt-trading.conf << 'CONF'
# VOLT Trading - Prevent sleep during 24/7 operation
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
IdleAction=ignore
IdleActionSec=infinity
CONF

# Apply changes
systemctl restart systemd-logind 2>/dev/null || true
echo "  - Lid close: will NOT suspend"
echo "  - Idle action: disabled"

echo ""
echo "[2/4] Setting CPU governor for efficiency..."

# Use powersave governor (Intel's hardware P-states handle performance)
# This is actually optimal for i7-1160G7 with HWP
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo "powersave" > "$cpu" 2>/dev/null || true
done

# Enable turbo boost (important for burst workloads)
echo "0" > /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true

echo "  - CPU governor: powersave (HWP handles performance scaling)"
echo "  - Turbo boost: enabled"

echo ""
echo "[3/4] Configuring thermal management..."

# ThinkPad thermal control
if [ -d /proc/acpi/ibm ]; then
    echo "level auto" > /proc/acpi/ibm/fan 2>/dev/null || true
    echo "  - Fan control: automatic"
fi

echo ""
echo "[4/4] Network stability..."

# Disable WiFi power save (prevents disconnections)
iw dev $(iw dev | grep Interface | head -1 | awk '{print $2}') set power_save off 2>/dev/null && \
    echo "  - WiFi power save: disabled" || \
    echo "  - WiFi power save: could not disable (may need NetworkManager)"

echo ""
echo "=============================================="
echo "System optimized for 24/7 trading operation"
echo "=============================================="
echo ""
echo "CHECKLIST before starting 12h test:"
echo "  [ ] AC adapter connected"
echo "  [ ] WiFi/Ethernet stable"
echo "  [ ] Screen lock disabled (or use: hyprctl dispatch dpms off)"
echo "  [ ] Start test: cd ~/VOLT-trading && source .venv/bin/activate"
echo "       python run_dryrun_12h.py --hours 12 --capital 10000"
echo ""
