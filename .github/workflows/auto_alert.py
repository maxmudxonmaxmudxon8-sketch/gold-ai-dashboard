
import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def main():
    data = yf.download(
        "GC=F",
        period="5d",
        interval="15m",
        progress=False
    )

    if data.empty or len(data) < 30:
        raise ValueError("Bozor ma'lumotlari yetarli emas!")

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()

    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))

    price = float(close.iloc[-1])
    rsi_value = float(rsi.iloc[-1])
    fast = float(ema12.iloc[-1])
    slow = float(ema26.iloc[-1])

    if fast > slow and rsi_value < 70:
        signal = "YUQORIGA"
    elif fast < slow and rsi_value > 30:
        signal = "PASTGA"
    else:
        signal = "NEYTRAL"

    market_time = str(close.index[-1])

    message = (
        "🥇 GOLD AI — AVTOMATIK TAHLIL\n\n"
        f"📊 Instrument: Gold Futures (GC=F)\n"
        f"💰 Narx: {price:.2f}\n"
        f"📈 RSI: {rsi_value:.2f}\n"
        f"🔹 EMA 12: {fast:.2f}\n"
        f"🔹 EMA 26: {slow:.2f}\n"
        f"📍 Signal: {signal}\n"
        f"🕒 Bozor shamchasi: {market_time}\n\n"
        "⚠️ Bu demo tahlil. Signal kafolat emas va "
        "haqiqiy savdo amalga oshirilmaydi."
    )

    send_telegram(message)
    print("Telegram xabari muvaffaqiyatli yuborildi!")

if __name__ == "__main__":
    main()
