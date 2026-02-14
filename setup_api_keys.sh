#!/bin/bash
# VOLT-Trading API Key Setup Script
# Säkert sätt att lägga till Binance API-nycklar

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════"
echo "🔐 VOLT-Trading API Key Setup"
echo "════════════════════════════════════════════════════════"
echo ""
echo "⚠️  VIKTIGT:"
echo "   • Använd ENDAST Binance TESTNET nycklar!"
echo "   • Testnet URL: https://testnet.binance.vision/"
echo "   • ALDRIG lägga till production keys här!"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Fråga användaren vilket mode
echo "Välj trading mode:"
echo "  1) Testnet (Sandbox) - REKOMMENDERAD för första körningen"
echo "  2) Production (REAL MONEY) - ENDAST för erfarna traders"
echo ""
read -p "Välj (1 eller 2): " mode_choice

if [ "$mode_choice" == "2" ]; then
    echo ""
    echo "⚠️⚠️⚠️  VARNING: PRODUCTION MODE  ⚠️⚠️⚠️"
    echo ""
    echo "Du är på väg att aktivera RIKTIG trading med RIKTIGA PENGAR!"
    echo ""
    read -p "Är du HELT SÄKER? Skriv 'JA JAG FÖRSTÅR': " confirm
    
    if [ "$confirm" != "JA JAG FÖRSTÅR" ]; then
        echo "Avbryter. Fortsätter med testnet mode."
        mode_choice="1"
    fi
fi

# Sätt sandbox flag
if [ "$mode_choice" == "2" ]; then
    sandbox="false"
    mode_name="PRODUCTION (REAL MONEY)"
else
    sandbox="true"
    mode_name="TESTNET (Sandbox)"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "Mode vald: $mode_name"
echo "════════════════════════════════════════════════════════"
echo ""

# Samla API-nycklar (syns inte när du skriver)
echo "Ange din Binance API Key:"
read -s api_key
echo ""
echo "Ange din Binance API Secret:"
read -s api_secret
echo ""

# Validera att något angivits
if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
    echo "❌ ERROR: API key och secret får inte vara tomma!"
    exit 1
fi

echo ""
echo "✓ API-nycklar mottagna"
echo ""

# Backup existing config
if [ -f "config/trading.json" ]; then
    backup_file="config/trading.json.backup.$(date +%Y%m%d_%H%M%S)"
    cp config/trading.json "$backup_file"
    echo "✓ Backup skapad: $backup_file"
fi

# Skapa ny config med API-nycklar
cat > config/trading.json << EOF
{
  "trading": {
    "initial_capital": 20000,
    "max_position_size": 0.10,
    "risk_per_trade": 0.025,
    "stop_loss": 0.05,
    "take_profit": 0.10,
    "max_drawdown": 0.15,
    "timeframe": "5m",
    "pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"]
  },
  "exchange": {
    "name": "binance",
    "sandbox": $sandbox,
    "api_key": "$api_key",
    "api_secret": "$api_secret",
    "password": ""
  },
  "risk_management": {
    "kelly_criterion": true,
    "max_leverage": 1.0,
    "correlation_limit": 0.7,
    "volatility_adjustment": true
  },
  "monitoring": {
    "dashboard_port": 8501,
    "log_level": "INFO",
    "metrics_enabled": true
  }
}
EOF

echo "✓ Config uppdaterad med API-nycklar"
echo ""

# Verifiera att filen sparades korrekt
if grep -q "\"api_key\": \"\"" config/trading.json; then
    echo "❌ ERROR: API key verkar inte ha sparats korrekt!"
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "✅ KLART!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Mode: $mode_name"
echo "API Key: ${api_key:0:8}..." 
echo "Status: Konfigurerad"
echo ""
echo "════════════════════════════════════════════════════════"
echo "🚀 NÄSTA STEG"
echo "════════════════════════════════════════════════════════"
echo ""
echo "1. Stoppa nuvarande trading system (Ctrl+C)"
echo "2. Starta om med: ./start_dryrun.sh"
echo "3. Systemet kommer nu kunna placera RIKTIGA orders!"
echo ""
echo "Övervaka logs noga efter omstart:"
echo "  tail -f logs/trading.log"
echo ""

if [ "$mode_choice" == "2" ]; then
    echo "⚠️  PRODUCTION MODE AKTIVT - ÖVERVAKA NOGA! ⚠️"
fi

echo "════════════════════════════════════════════════════════"
