# ⚡ Lenovo ThinkPad X1 Nano Gen 1 - 24/7 Trading Optimization Guide

## 🖥️ System Specs
- **Model:** Lenovo ThinkPad X1 Nano Gen 1
- **CPU:** Intel Core i7-1160G7 (Intel Evo)
- **RAM:** 16GB LPDDR4x
- **OS:** Arch Linux 6.18.7
- **Purpose:** 24/7 Cryptocurrency Trading

---

## 🔧 Optimization Checklist

### ✅ 1. Prevent Sleep/Suspend (CRITICAL!)

**The 12-hour test script already handles this**, but for manual runs:

```bash
# Option 1: systemd-inhibit (best for Arch Linux)
systemd-inhibit --what=sleep:idle:handle-lid-switch \
  --who="VOLT-Trading" \
  --why="Running 24/7 trading" \
  --mode=block \
  python main.py
```

**Option 2: Disable sleep permanently (use with caution)**

```bash
# Check current settings
systemctl status sleep.target suspend.target

# Disable sleep (can re-enable later)
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# Re-enable when done
sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

**Option 3: GNOME/KDE Settings**

If using GNOME:
```bash
# Never suspend on AC power
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'

# Never suspend on battery
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

# Don't suspend when lid is closed (IMPORTANT for laptop!)
gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power lid-close-battery-action 'nothing'
```

---

### ✅ 2. Power Management

**Keep laptop plugged in for 24/7 trading!**

Check power settings:
```bash
# Install tlp for better power management
sudo pacman -S tlp tlp-rdw

# Edit TLP config for performance
sudo nano /etc/tlp.conf
```

Recommended TLP settings for 24/7 trading:
```bash
# /etc/tlp.conf

# Keep performance mode on AC
CPU_SCALING_GOVERNOR_ON_AC=performance
CPU_SCALING_GOVERNOR_ON_BAT=powersave

# Don't throttle CPU on AC
CPU_ENERGY_PERF_POLICY_ON_AC=performance
CPU_BOOST_ON_AC=1

# Keep full performance on AC
PLATFORM_PROFILE_ON_AC=performance

# Disable USB autosuspend
USB_AUTOSUSPEND=0

# Keep Wi-Fi active
WIFI_PWR_ON_AC=off
```

Start TLP:
```bash
sudo systemctl enable tlp
sudo systemctl start tlp
```

---

### ✅ 3. CPU Performance

**Intel i7-1160G7 optimization:**

```bash
# Install CPU frequency utils
sudo pacman -S cpupower

# Set performance governor
sudo cpupower frequency-set -g performance

# Make permanent
echo 'GOVERNOR="performance"' | sudo tee -a /etc/default/cpupower
sudo systemctl enable cpupower
```

Check CPU frequency:
```bash
watch -n 1 'grep MHz /proc/cpuinfo'
```

---

### ✅ 4. Thermal Management

**ThinkPad X1 Nano is fanless, so thermal management is critical!**

Install monitoring tools:
```bash
sudo pacman -S lm_sensors thermald

# Detect sensors
sudo sensors-detect

# Start thermal daemon
sudo systemctl enable thermald
sudo systemctl start thermald
```

Monitor temperatures:
```bash
# Real-time monitoring
watch -n 2 sensors

# Or with more detail
watch -n 2 'sensors | grep -E "(Package|Core)"'
```

**Temperature limits:**
- **Normal:** 40-60°C
- **Warning:** 60-80°C
- **Critical:** 80°C+ (CPU will throttle)

**If temps get too high:**
1. Ensure laptop has good airflow (not on blanket/soft surface)
2. Use laptop cooling pad
3. Clean vents (ThinkPad X1 Nano has bottom vents)
4. Reduce CPU governor to `powersave`

---

### ✅ 5. Network Stability

**Critical for trading - must maintain Binance connection!**

```bash
# Disable Wi-Fi power saving
sudo iw dev wlan0 set power_save off

# Make permanent - create systemd service
sudo tee /etc/systemd/system/wifi-powersave-off.service << 'EOF'
[Unit]
Description=Disable Wi-Fi Power Saving
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/iw dev wlan0 set power_save off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable wifi-powersave-off
sudo systemctl start wifi-powersave-off
```

**Monitor network:**
```bash
# Ping Binance to check connection
watch -n 5 'ping -c 1 api.binance.com | grep time'
```

**For extra stability, use Ethernet if available!**

---

### ✅ 6. Disk I/O Optimization

```bash
# Check if using SSD (should be yes on X1 Nano)
lsblk -d -o name,rota
# rota=0 means SSD

# Enable periodic TRIM for SSD health
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer
```

Ensure enough free space:
```bash
# Keep at least 10GB free for logs and metrics
df -h /home
```

---

### ✅ 7. Memory Management

```bash
# Check memory usage
free -h

# Monitor swap usage (should be minimal)
watch -n 2 'free -h'

# If swap is being used heavily, add more:
# (Not usually needed with 16GB RAM)
```

---

### ✅ 8. Auto-restart on Crash

Create a systemd service for auto-restart:

```bash
sudo tee /etc/systemd/system/volt-trading.service << 'EOF'
[Unit]
Description=VOLT Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=omarchy
WorkingDirectory=/home/omarchy/VOLT-trading
ExecStart=/home/omarchy/VOLT-trading/.venv/bin/python /home/omarchy/VOLT-trading/main.py
Restart=always
RestartSec=30
StandardOutput=append:/home/omarchy/VOLT-trading/logs/systemd.log
StandardError=append:/home/omarchy/VOLT-trading/logs/systemd.log

# Prevent sleep
ExecStartPre=/usr/bin/systemd-inhibit --what=sleep:idle --who="VOLT-Trading" --why="24/7 Trading" --mode=block sleep infinity &

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable volt-trading
sudo systemctl start volt-trading

# Check status
sudo systemctl status volt-trading
```

---

### ✅ 9. Log Rotation

Prevent logs from filling disk:

```bash
sudo tee /etc/logrotate.d/volt-trading << 'EOF'
/home/omarchy/VOLT-trading/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 omarchy omarchy
}
EOF
```

---

### ✅ 10. Monitor System Health

**Create monitoring dashboard:**

```bash
# Install monitoring tools
sudo pacman -S htop btop iotop nethogs

# Real-time system overview
btop
```

**Auto-alert on high temps:**

Create a simple temp monitor:
```bash
#!/bin/bash
# Save as ~/VOLT-trading/monitor_temp.sh

while true; do
    TEMP=$(sensors | grep 'Package id 0' | awk '{print $4}' | sed 's/+//;s/°C//')
    
    if (( $(echo "$TEMP > 85" | bc -l) )); then
        notify-send "⚠️ HIGH CPU TEMP" "Temperature: ${TEMP}°C - Consider stopping trading!"
        # Or send email/telegram alert
    fi
    
    sleep 60
done
```

---

### ✅ 11. Battery Health (for 24/7 use)

**ThinkPad has battery charge thresholds!**

```bash
# Install TLP (if not already)
sudo pacman -S tlp

# Set battery thresholds (keeps battery at 60-80% when plugged in)
# This extends battery lifespan for 24/7 use
sudo tee /etc/tlp.conf << 'EOF'
START_CHARGE_THRESH_BAT0=60
STOP_CHARGE_THRESH_BAT0=80
EOF

sudo tlp start
```

Check battery:
```bash
sudo tlp-stat -b
```

---

### ✅ 12. Backup Strategy

**CRITICAL: Always backup your data!**

```bash
# Auto-backup metrics every hour
crontab -e

# Add this line:
0 * * * * cp /home/omarchy/VOLT-trading/reports/monitoring_metrics.json /home/omarchy/VOLT-trading/reports/backup_$(date +\%Y\%m\%d_\%H00).json

# Clean old backups (keep 7 days)
0 0 * * * find /home/omarchy/VOLT-trading/reports -name "backup_*.json" -mtime +7 -delete
```

---

## 🚀 Quick Setup Script

Run this to optimize everything at once:

```bash
#!/bin/bash
# ThinkPad X1 Nano 24/7 Trading Setup

echo "🔧 Optimizing ThinkPad X1 Nano for 24/7 trading..."

# 1. Install required packages
sudo pacman -S --needed tlp cpupower lm_sensors thermald

# 2. Disable sleep
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action 'nothing'

# 3. Enable performance
sudo cpupower frequency-set -g performance

# 4. Start thermal management
sudo systemctl enable --now thermald

# 5. Enable TLP
sudo systemctl enable --now tlp

# 6. Disable Wi-Fi power saving
sudo iw dev wlan0 set power_save off

# 7. Enable SSD TRIM
sudo systemctl enable --now fstrim.timer

echo "✅ Optimization complete!"
echo ""
echo "Next steps:"
echo "  1. Edit /etc/tlp.conf for battery thresholds"
echo "  2. Ensure laptop is plugged into AC power"
echo "  3. Run: ./run_12h_test.sh"
```

---

## 📊 Monitoring Commands

```bash
# System overview
btop

# Trading process
htop -p $(pgrep -f "python.*main.py")

# Temperature
watch -n 2 sensors

# Network
nethogs

# Disk I/O
sudo iotop

# Test status
./check_test_status.sh
```

---

## ⚠️ Important Notes

1. **Keep plugged in:** X1 Nano battery is small (48Wh), won't last 12 hours under load
2. **Good ventilation:** Place on hard surface, not bed/pillow
3. **Monitor temps:** Check every few hours, especially first time
4. **Stable network:** Ethernet cable > Wi-Fi for critical trading
5. **Backup config:** Your API keys are in config/trading.json (gitignored)
6. **Test first:** Always test on Binance Testnet before production!

---

## 🎯 Pre-Test Checklist

Before running 12-hour test:

- [ ] Laptop plugged into AC power
- [ ] Battery charge threshold set (60-80%)
- [ ] Sleep/suspend disabled
- [ ] CPU governor set to performance
- [ ] Wi-Fi power saving disabled
- [ ] Good airflow around laptop
- [ ] Dashboard accessible (http://localhost:8501)
- [ ] API keys verified (`python verify_api_keys.py`)
- [ ] Enough disk space (>10GB free)
- [ ] Test mode enabled (sandbox: true)

---

**Ready to start? Run:**
```bash
./run_12h_test.sh
```

Monitor at: http://localhost:8501
