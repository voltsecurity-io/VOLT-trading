# VOLT Trading System - Analys: Låg Trading-Frekvens

**Test:** 2026-02-13 17:45 → 2026-02-14 05:08 (11.39h)  
**Resultat:** 4 trades (endast köp), 13 misslyckade orders

---

## 🔍 HUVUDORSAKER

### 1. **Strategi-trösklar för KONSERVATIVA**

**Problem:** Dubbel tröskel-filter som blockerar de flesta signaler

```python
# volt_strategy.py rad 165-173
if buy_score >= 3.0 and buy_score > sell_score:
    signal_action = "buy"
    signal_strength = min(buy_score / buy_total, 1.0)  # buy_total = 6

# Rad 173: Kräver OCKSÅ signal_strength > 0.6
if signal_action and signal_strength > 0.6:
    return signal  # Godkänd
```

**Matematik:**
- Buy: Behöver 3.0 poäng + strength > 0.6
- Strength = score / 6.0
- 3.0 / 6.0 = 0.50 (UNDER 0.6 tröskeln!)
- **Krävs minst:** 3.6 / 6.0 = 0.6 → **60% av max score**

**Sell:** Samma problem
- Sell: Behöver 3.0 poäng + strength > 0.6  
- Strength = score / 5.0
- 3.0 / 5.0 = 0.60 (EXAKT på gränsen)
- **Krävs minst:** 3.0 / 5.0 = 0.6 → **60% av max score**

**Konsekvens:** Endast MYCKET starka signaler passerar

---

### 2. **SÄLJ-signaler kan ALDRIG exekveras**

**Orsak:** Systemet startade med endast USDT (20,000)

```json
// Startbalans
{"USDT": 20000.0}
```

**Signalfördelning:**
- **13 SÄLJ-signaler** (SOL, AVAX, BNB, ETH)
- **4 KÖP-signaler** (ETH, BNB)

**Problem:** Man kan inte sälja mynt man inte äger!

```log
DryRun: Insufficient SOL for sell 0.09 SOL/USDT (have 0.000000)
DryRun: Insufficient AVAX for sell 0.01 AVAX/USDT (have 0.000000)
```

**76% av signalerna (13/17) var dödfödda!**

---

### 3. **Endast 17 signaler på 11.39 timmar**

**Frekvens:** 1 signal var 40:e minut (138 trading loops)

**Tidsfördelning:**
- 17:45-23:45 (6h): 5 signaler (0.83/timme)
- 00:00-05:08 (5h): 12 signaler (2.4/timme)

**Marknaden var mer aktiv på natten** → Fler signaler genererades

---

### 4. **Signaler blockerades av korrelationskontroll**

Endast **1 signal** blockerades av risk manager:

```log
03:28:35 - High correlation (1.00) between ETH/USDT and ETH/USDT
03:28:35 - Signal rejected: ETH/USDT buy
```

(Försökte köpa mer ETH när vi redan äger ETH - korrekt blockering)

---

## 📊 SIGNALSAMMANFATTNING

### **KÖP-signaler (4):**
- **ETH/USDT:** 1 signal → ✅ Exekverad  
- **BNB/USDT:** 3 signaler → ✅ Alla 3 exekverade

### **SÄLJ-signaler (13):**
- **SOL/USDT:** 5 signaler → ❌ Alla misslyckade (äger ej)
- **AVAX/USDT:** 3 signaler → ❌ Alla misslyckade (äger ej)
- **BNB/USDT:** 4 signaler → ❌ Alla misslyckade (äger ej)
- **ETH/USDT:** 1 signal → ❌ Misslyckad (äger ej)

**Notera:** ALLA sälj-signaler kom INNAN vi köpte mynten!

---

## 💡 LÖSNINGAR

### **Lösning 1: Justera strategi-trösklar** (REKOMMENDERAS)

```python
# volt_strategy.py rad 161-173

# NUVARANDE (för strikt):
if buy_score >= 3.0 and buy_score > sell_score:
    signal_action = "buy"
    signal_strength = min(buy_score / buy_total, 1.0)

if signal_action and signal_strength > 0.6:  # ← SÄNK DENNA
    return signal

# FÖRESLAGEN ÄNDRING:
if signal_action and signal_strength > 0.45:  # 45% istället för 60%
    return signal
```

**Förväntad effekt:** 
- +50-100% fler signaler passerar
- Fortfarande selektiv (inte alla signaler)

---

### **Lösning 2: Starta med diversifierad portfolio** (VALFRITT)

Istället för 100% USDT, börja med:
```python
initial_balance = {
    "USDT": 10000,   # 50%
    "BTC": 0.05,     # ~$2000-2500
    "ETH": 1.0,      # ~$2000
    "BNB": 5.0,      # ~$3000
    "SOL": 10.0,     # ~$1000
    "AVAX": 30.0     # ~$1000
}
```

**Fördel:** Kan sälja från dag 1  
**Nackdel:** Mindre realistiskt för cold start-scenario

---

### **Lösning 3: Sänk RSI/MACD-trösklar** (ALTERNATIV)

```python
# volt_strategy.py rad 26-27
self.rsi_overbought = 70  →  65  # Sälj tidigare
self.rsi_oversold = 30    →  35  # Köp tidigare
```

**Effekt:** Fler RSI-baserade signaler triggas

---

## 🎯 REKOMMENDATION

**Kör i denna ordning:**

1. **Sänk signal_strength > 0.6 till > 0.45** (rad 173)
2. **Testa 12h igen** med samma 20,000 USDT start
3. **Analysera:** Förvänta 8-15 trades istället för 4

**Om fortfarande för få trades:**
4. Sänk RSI-trösklar (70→65, 30→35)
5. Testa ytterligare 12h

---

## 📈 FÖRVÄNTADE RESULTAT

**Med signal_strength > 0.45:**
- Signaler som passerar: ~12-20 av 17 (nuvarande: 4/17)
- Trades per timme: ~1.0-1.5 (nuvarande: 0.35)
- Total trades på 12h: ~12-18 (nuvarande: 4)

**Med båda ändringarna:**
- Signaler som passerar: ~20-30 totalt
- Trades per timme: ~1.5-2.5
- Total trades på 12h: ~18-30
