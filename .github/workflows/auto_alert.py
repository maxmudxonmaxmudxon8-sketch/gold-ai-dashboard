
import os
import json
import requests
import yfinance as yf
import pandas as pd

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = ".gold_ai_state.json"


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Telegram sozlamalari topilmadi!")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError("Telegram xabarni yubormadi!")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as file:
                return json.load(file)
        except Exception:
            return {}

    return {}


def save_state(state):
    temp_file = STATE_FILE + ".tmp"

    with open(temp_file, "w") as file:
        json.dump(state, file, indent=4)

    os.replace(temp_file, STATE_FILE)


def get_market_data():
    data = yf.download(
        "GC=F",
        period="5d",
        interval="15m",
        progress=False
    )

    if data.empty:
        raise ValueError("Bozor ma'lumotlari topilmadi!")

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.to_numeric(
        close, errors="coerce"
    ).dropna()

    if len(close) < 30:
        raise ValueError("Ma'lumotlar yetarli emas!")

    return close


def calculate_analysis(close):

    ema12 = close.ewm(
        span=12, adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26, adjust=False
    ).mean()

    delta = close.diff()

    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    rsi = 100 - (
        100 / (1 + gain / loss.replace(0, float("nan")))
    )

    rsi = rsi.mask(
        (loss == 0) & (gain > 0), 100
    )

    rsi = rsi.mask(
        (loss == 0) & (gain == 0), 50
    )

    price = float(close.iloc[-1])
    rsi_value = float(rsi.iloc[-1])
    fast = float(ema12.iloc[-1])
    slow = float(ema26.iloc[-1])

    if pd.isna(rsi_value):
        raise ValueError("RSI hisoblanmadi!")

    if fast > slow and rsi_value < 70:
        signal = "YUQORIGA"

    elif fast < slow and rsi_value > 30:
        signal = "PASTGA"

    else:
        signal = "NEYTRAL"

    market_time = str(close.index[-1])

    return price, rsi_value, fast, slow, signal, market_time


def main():

    close = get_market_data()

    price, rsi, fast, slow, signal, market_time = (
        calculate_analysis(close)
    )

    state = load_state()

    previous_signal = state.get("last_signal")

    print("GOLD AI tahlili bajarildi.")
    print("Narx:", price)
    print("RSI:", round(rsi, 2))
    print("Signal:", signal)

    # Bir xil signalni qayta yubormaslik
    if previous_signal == signal:
        print("Signal o'zgarmadi. Telegram xabari yuborilmadi.")
        return

    if previous_signal is None:
        change_text = "Birinchi avtomatik signal"
    else:
        change_text = (
            f"Signal o'zgardi: {previous_signal} → {signal}"
        )

    message = (
        "🥇 GOLD AI — YANGI SIGNAL\n\n"
        f"📊 Instrument: Gold Futures (GC=F)\n"
        f"💰 Narx: {price:.2f}\n"
        f"📈 RSI: {rsi:.2f}\n"
        f"🔹 EMA 12: {fast:.2f}\n"
        f"🔹 EMA 26: {slow:.2f}\n"
        f"📍 Signal: {signal}\n"
        f"🔔 {change_text}\n"
        f"🕒 Bozor shamchasi: {market_time}\n\n"
        "⚠️ Demo tahlil. Bu savdo tavsiyasi emas."
    )

    send_telegram(message)

    # Faqat muvaffaqiyatli yuborilgandan keyin saqlash
    save_state({
        "last_signal": signal,
        "last_price": round(price, 2),
        "last_candle": market_time
    })

    print("Telegram xabari yuborildi!")
    print("Yangi signal saqlandi.")


if __name__ == "__main__":
    main()
