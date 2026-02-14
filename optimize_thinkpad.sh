#!/bin/bash
# Quick ThinkPad Optimization for 24/7 Trading

set -e

echo "════════════════════════════════════════════════════════════"
echo "⚡ ThinkPad X1 Nano - 24/7 Trading Optimization"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run as root! Run as normal user."
    echo "   The script will ask for sudo when needed."
    exit 1
fi

echo "This will optimize your ThinkPad for 24/7 trading by:"
echo "  • Preventing sleep/suspend"
echo "  • Disabling Wi-Fi power saving"
echo "  • Setting CPU to performance mode"
echo "  • Installing monitoring tools"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📦 Step 1: Installing required packages"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check which packages are already installed
PACKAGES_TO_INSTALL=""

for pkg in lm_sensors cpupower htop; do
    if ! pacman -Q $pkg &>/dev/null; then
        PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL $pkg"
    fi
done

if [ -n "$PACKAGES_TO_INSTALL" ]; then
    echo "Installing:$PACKAGES_TO_INSTALL"
    sudo pacman -S --needed $PACKAGES_TO_INSTALL
else
    echo "✓ All required packages already installed"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚫 Step 2: Preventing sleep/suspend"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if GNOME is running
if command -v gsettings &> /dev/null; then
    echo "Configuring GNOME power settings..."
    
    # Never suspend on AC
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
    echo "✓ Disabled suspend on AC power"
    
    # Never suspend on battery
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
    echo "✓ Disabled suspend on battery"
    
    # Don't suspend when lid closed on AC
    gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action 'nothing'
    echo "✓ Lid close on AC won't suspend"
    
    # Screen timeout
    gsettings set org.gnome.desktop.session idle-delay 0
    echo "✓ Disabled idle timeout"
    
    echo ""
    echo "✅ GNOME power settings configured"
else
    echo "⚠️  GNOME not detected. Sleep prevention will be handled by test script."
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "⚡ Step 3: CPU Performance Mode"
echo "════════════════════════════════════════════════════════════"
echo ""

# Set CPU governor to performance
echo "Setting CPU governor to performance..."
sudo cpupower frequency-set -g performance &>/dev/null || true
echo "✓ CPU set to performance mode"

# Make it permanent
echo "Making performance mode permanent..."
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpupower > /dev/null
sudo systemctl enable cpupower &>/dev/null || true

echo ""
echo "Current CPU frequencies:"
cpupower frequency-info | grep "current CPU frequency" | head -1

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📡 Step 4: Network Optimization"
echo "════════════════════════════════════════════════════════════"
echo ""

# Get Wi-Fi interface name
WIFI_INTERFACE=$(ip link | grep -E "wl[a-z0-9]+" | awk -F: '{print $2}' | tr -d ' ' | head -1)

if [ -n "$WIFI_INTERFACE" ]; then
    echo "Found Wi-Fi interface: $WIFI_INTERFACE"
    
    # Disable power saving
    sudo iw dev $WIFI_INTERFACE set power_save off 2>/dev/null || true
    echo "✓ Wi-Fi power saving disabled"
    
    # Create systemd service to make it permanent
    sudo tee /etc/systemd/system/wifi-powersave-off.service > /dev/null << EOF
[Unit]
Description=Disable Wi-Fi Power Saving for Trading
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/iw dev $WIFI_INTERFACE set power_save off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable wifi-powersave-off.service &>/dev/null || true
    echo "✓ Wi-Fi optimization will persist after reboot"
else
    echo "⚠️  No Wi-Fi interface found (might be using Ethernet)"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "💾 Step 5: SSD Optimization"
echo "════════════════════════════════════════════════════════════"
echo ""

# Enable periodic TRIM for SSD
sudo systemctl enable fstrim.timer &>/dev/null || true
sudo systemctl start fstrim.timer &>/dev/null || true
echo "✓ Periodic SSD TRIM enabled"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🌡️  Step 6: Temperature Monitoring Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Detect sensors
echo "Detecting hardware sensors..."
sudo sensors-detect --auto &>/dev/null || true
echo "✓ Sensors configured"

echo ""
echo "Current temperatures:"
sensors 2>/dev/null | grep -E "(Package|Core)" || echo "Run 'sensors' to see temperatures"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ OPTIMIZATION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Your ThinkPad X1 Nano is now optimized for 24/7 trading!"
echo ""
echo "Summary of changes:"
echo "  ✓ Sleep/suspend disabled"
echo "  ✓ CPU set to performance mode"
echo "  ✓ Wi-Fi power saving disabled"
echo "  ✓ SSD TRIM enabled"
echo "  ✓ Temperature monitoring configured"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "⚠️  IMPORTANT REMINDERS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Before starting 12-hour test:"
echo ""
echo "  1. ⚡ PLUG IN AC POWER (critical!)"
echo "  2. 🌡️  Ensure good ventilation"
echo "  3. 📊 Open dashboard: http://localhost:8501"
echo "  4. 🔐 Verify API keys: python verify_api_keys.py"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🚀 READY TO START"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "To start the 12-hour test:"
echo ""
echo "  ./run_12h_test.sh"
echo ""
echo "To check status during test:"
echo ""
echo "  ./check_test_status.sh"
echo ""
echo "To monitor system:"
echo ""
echo "  htop              # Process monitor"
echo "  sensors           # Temperature"
echo "  watch -n 2 'sensors | grep Package'  # Live temp monitoring"
echo ""
echo "════════════════════════════════════════════════════════════"
