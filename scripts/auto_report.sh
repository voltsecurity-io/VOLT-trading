#!/bin/bash
# Auto-save trading report every 15 minutes
# Add to crontab: */15 * * * * /home/omarchy/VOLT-trading/scripts/auto_report.sh

cd /home/omarchy/VOLT-trading
python scripts/generate_report.py

# Also sync to GitHub/GitLab every hour
minute=$(date +%M)
if [ "$minute" = "00" ]; then
    echo "Hourly Git sync..."
    git -C /home/omarchy/VOLT-trading add reports/
    git -C /home/omarchy/VOLT-trading commit -m "Auto-save: $(date)" || true
    git -C /home/omarchy/VOLT-trading push origin master 2>/dev/null || true
    git -C /home/omarchy/VOLT-trading push gitlab master 2>/dev/null || true
fi
