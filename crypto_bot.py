import requests
import time
import datetime

TOKEN = "8679676195:AAHZamSd5VhU0F8YtWfNC3Y-6bhskGUE9aE"
CHAT_ID = "5411921418"
INTERVALO = 300

COINS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
last_signals = {}

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

def get_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50"
    r = requests.get(url, timeout=10)
    return [float(k[4]) for k in r.json()]

def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    r = requests.get(url, timeout=10)
    d = r.json()
    return float(d["lastPrice"]), float(d["priceChangePercent"])

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains, losses = 0, 0
    for i in range(len(closes) - period, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0: gains += diff
        else: losses += abs(diff)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0: return 100
    return round(100 - (100 / (1 + avg_gain / avg_loss)))

def calc_ema(data, period):
    k = 2 / (period + 1)
    val = data[0]
    for i in range(1, len(data)):
        val = data[i] * k + val * (1 - k)
    return val

def calc_macd(closes):
    if len(closes) < 26: return "neutral"
    return "bull" if calc_ema(closes, 12) > calc_ema(closes, 26) else "bear"

def analyze(coin, symbol):
    closes = get_klines(symbol)
    price, change = get_price(symbol)
    rsi = calc_rsi(closes)
    macd = calc_macd(closes)
    trend = "bull" if price > sum(closes[-20:]) / 20 else "bear"
    if rsi < 35 and macd == "bull" and trend == "bull":
        return "COMPRAR", "buy", f"RSI en sobreventa ({rsi}), MACD alcista y precio sobre SMA20.", price, change
    elif rsi > 65 and macd == "bear":
        return "VENDER", "sell", f"RSI en sobrecompra ({rsi}) y MACD bajista.", price, change
    elif rsi < 40 and trend == "bull":
        return "COMPRAR", "buy", f"RSI bajo ({rsi}) con tendencia alcista.", price, change
    elif rsi > 60 and trend == "bear":
        return "VENDER", "sell", f"RSI elevado ({rsi}) y precio bajo SMA20.", price, change
    else:
        return "ESPERAR", "wait", f"RSI neutral ({rsi}). Sin señal clara.", price, change

def main():
    print("Bot iniciado")
    send_message("✅ <b>CryptoSignal Bot activo</b>\nAnalizando BTC y ETH cada 5 minutos.")
    while True:
        for coin, symbol in COINS.items():
            try:
                action, stype, reason, price, change = analyze(coin, symbol)
                if stype != "wait" and last_signals.get(coin) != action:
                    emoji = "🟢" if stype == "buy" else "🔴"
                    pfmt = f"${price:,.0f}" if price > 100 else f"${price:,.2f}"
                    link = f"https://www.binance.com/es/trade/{coin}_USDT"
                    hora = datetime.datetime.now().strftime("%H:%M")
                    msg = f"{emoji} <b>{action} {coin}</b>\n━━━━━━━━━━━━━━━━\n💰 Precio: <b>{pfmt}</b> ({'+' if change>=0 else ''}{change:.2f}% hoy)\n📝 {reason}\n━━━━━━━━━━━━━━━━\n🏦 Ejecutar en: <a href='{link}'>Binance</a>\n🕐 {hora} hs"
                    send_message(msg)
                    last_signals[coin] = action
            except Exception as e:
                print(f"Error {coin}: {e}")
        time.sleep(INTERVALO)

if __name__ == "__main__":
    main()
