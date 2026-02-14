# 🔐 API Key Setup Guide

## Metod 1: Automatisk Setup (REKOMMENDERAD)

Kör detta script och följ instruktionerna:

```bash
cd ~/VOLT-trading
./setup_api_keys.sh
```

Scriptet kommer att:
1. Fråga dig om testnet eller production mode
2. Säkert samla in dina API-nycklar (syns inte på skärmen)
3. Skapa backup av nuvarande config
4. Uppdatera config/trading.json
5. Verifiera att allt sparades korrekt

---

## Metod 2: Manuell Setup

Om du föredrar att redigera själv:

### Steg 1: Öppna config filen

```bash
cd ~/VOLT-trading
nano config/trading.json
# Eller i VS Code: Ctrl+P -> skriv "trading.json"
```

### Steg 2: Lägg till dina nycklar

Hitta denna sektion:
```json
"exchange": {
  "name": "binance",
  "sandbox": true,
  "api_key": "",
  "api_secret": "",
  "password": ""
}
```

Ändra till:
```json
"exchange": {
  "name": "binance",
  "sandbox": true,              ← true = Testnet, false = Production
  "api_key": "DIN_API_KEY",     ← Klistra in här
  "api_secret": "DIN_SECRET",   ← Klistra in här
  "password": ""                ← Lämna tom (används inte av Binance)
}
```

### Steg 3: Spara filen

- **Nano:** Ctrl+O, Enter, Ctrl+X
- **VS Code:** Ctrl+S

---

## ⚠️ VIKTIGT: Testnet vs Production

### Testnet (REKOMMENDERAD för första gången)
```json
"sandbox": true
```
- **URL:** https://testnet.binance.vision/
- Fake pengar, riktig trading-miljö
- Perfekt för att testa strategin
- **INGEN RISK** - helt säkert!

### Production (RIKTIGA PENGAR!)
```json
"sandbox": false
```
- **URL:** https://www.binance.com/
- RIKTIGA pengar på spel!
- Använd ENDAST efter noggrann testning på testnet
- Börja med SMÅ belopp!

---

## 🔒 Säkerhet

### API Key Permissions

Dina Binance API-nycklar bör ha följande permissions:

**Testnet:**
- ✅ Enable Reading
- ✅ Enable Spot & Margin Trading
- ❌ Enable Withdrawals (ALDRIG aktivera detta!)

**Production (om du använder det):**
- ✅ Enable Reading
- ✅ Enable Spot & Margin Trading
- ❌ Enable Withdrawals (ALDRIG AKTIVERA!)
- ✅ IP Whitelist (lägg till din IP för extra säkerhet)

### Git Säkerhet

Filen `config/trading.json` är redan i `.gitignore` så dina nycklar pushas ALDRIG till GitHub.

Verifiera:
```bash
git status
# Du ska INTE se config/trading.json i listan
```

---

## 🚀 Efter du lagt till nycklar

### Steg 1: Stoppa nuvarande system

I terminalen där trading körs:
```bash
Ctrl+C
```

Eller:
```bash
python control.py stop
```

### Steg 2: Starta om systemet

```bash
./start_dryrun.sh
```

### Steg 3: Verifiera att API-nycklar fungerar

Du ska se i loggarna:
```
✅ Binance exchange ready — sandbox, authenticated
✅ Balance fetched: USDT 10000.00
```

Istället för:
```
⚠️ Binance exchange ready — sandbox, public-only (no API keys)
```

---

## 🧪 Testa API-nycklarna

Innan du startar trading, testa att nycklarna fungerar:

```bash
cd ~/VOLT-trading
source .venv/bin/activate
python -c "
from src.exchanges.exchange_factory import create_exchange
from src.core.config_manager import ConfigManager

config = ConfigManager()
exchange = create_exchange(config)

# Testa balance fetch
balance = exchange.exchange.fetch_balance()
print(f'✅ Balance: {balance}')

# Testa ticker fetch
ticker = exchange.exchange.fetch_ticker('BTC/USDT')
print(f'✅ BTC/USDT Price: {ticker[\"last\"]}')

print('🎉 API-nycklar fungerar perfekt!')
"
```

Om du ser felmeddelanden:
- `401 Unauthorized` = Fel API key eller secret
- `403 Forbidden` = IP inte whitelistad
- `418 I'm a teapot` = IP-ban (för många requests)

---

## 📝 Felsökning

### "Invalid API-key, IP, or permissions"

**Lösning:**
1. Dubbelkolla att du kopierade hela API key och secret (inga extra mellanslag)
2. Verifiera att nycklarna har "Enable Spot & Margin Trading" aktiverat
3. Om production: lägg till din IP i whitelist på Binance

### "Timestamp for this request is outside of the recvWindow"

**Lösning:**
```bash
# Synkronisera systemklockan
sudo ntpdate -s time.nist.gov
```

### "Insufficient balance"

**Lösning för Testnet:**
1. Gå till https://testnet.binance.vision/
2. Logga in med ditt testnet konto
3. Klicka "Get Test Funds" för att få fake USDT

---

## 📊 Förväntat Beteende Efter Setup

### Med API-nycklar (Testnet):
```
✅ Hämtar live market data
✅ Beräknar tekniska indikatorer
✅ Genererar trading signaler
✅ PLACERAR RIKTIGA ORDERS (på testnet)
✅ Kan läsa account balance
✅ Kan hämta order history
```

### Utan API-nycklar (Public-only):
```
✅ Hämtar live market data
✅ Beräknar tekniska indikatorer
✅ Genererar trading signaler
❌ Kan INTE placera orders
❌ Kan INTE läsa balance
❌ Kan INTE se positions
```

---

## 🎯 Nästa Steg

1. ✅ Lägg till API-nycklar med `./setup_api_keys.sh`
2. 🔄 Starta om systemet med `./start_dryrun.sh`
3. 👀 Övervaka logs: `tail -f logs/trading.log`
4. 📊 Kolla dashboard: http://localhost:8501
5. ⏰ Låt systemet köra i 1-2 timmar
6. 📈 Granska trades i `reports/monitoring_metrics.json`

---

## ⚡ Quick Command Reference

```bash
# Setup API keys (interactive)
./setup_api_keys.sh

# Stoppa system
python control.py stop

# Starta system
./start_dryrun.sh

# Visa logs
tail -f logs/trading.log

# Visa metrics
cat reports/monitoring_metrics.json | python -m json.tool

# Testa API-nycklar
python tests/test_binance_exchange.py -v
```

---

**När du är redo, kör:**
```bash
./setup_api_keys.sh
```

Lycka till! 🚀
