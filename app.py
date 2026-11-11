
import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="GOLD AI", page_icon="🥇", layout="wide")

HISTORY_FILE = "signal_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

st.title("🥇 GOLD AI")
st.subheader("XAU/USD — Oltin bozorini kuzatish")
st.info("Demo rejim. Haqiqiy savdo amalga oshirilmaydi.")

if "history" not in st.session_state:
    st.session_state.history = load_history()

if st.button("Bozor ma'lumotlarini yuklash"):

    with st.spinner("Tahlil qilinmoqda..."):

        data = yf.download("GC=F", period="5d",
                           interval="15m", progress=False)

        if not data.empty:

            close = data["Close"]

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean()

            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()

            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()

            price = float(close.iloc[-1])
            rsi_value = float(rsi.dropna().iloc[-1])
            macd_value = float(macd.iloc[-1])
            signal_value = float(signal.iloc[-1])

            if ema50.iloc[-1] > ema200.iloc[-1]:
                trend = "Yuqoriga"
            else:
                trend = "Pastga"

            if trend == "Yuqoriga" and macd_value > signal_value:
                conclusion = "Yuqoriga yo'nalish kuzatilmoqda"
            elif trend == "Pastga" and macd_value < signal_value:
                conclusion = "Pastga yo'nalish kuzatilmoqda"
            else:
                conclusion = "Aralash holat"

            record = {
                "Vaqt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Narx": round(price, 2),
                "RSI": round(rsi_value, 2),
                "MACD": round(macd_value, 4),
                "Trend": trend,
                "Xulosa": conclusion
            }

            st.session_state.history.insert(0, record)
            st.session_state.history = st.session_state.history[:100]
            save_history(st.session_state.history)

            st.success("Tahlil tayyor va tarixga saqlandi!")

            st.subheader("🥇 Joriy bozor holati")
            c1, c2, c3 = st.columns(3)
            c1.metric("Oltin narxi", price)
            c2.metric("RSI", round(rsi_value, 2))
            c3.metric("MACD", round(macd_value, 4))

            st.subheader("🤖 GOLD AI demo xulosasi")
            st.write("Trend:", trend)
            st.write("Xulosa:", conclusion)

            st.warning("Bu o'quv-demо tahlili. Foyda kafolati yo'q.")

            st.subheader("📈 Oltin narxi")
            st.line_chart(close)

            st.subheader("📊 RSI")
            st.line_chart(rsi)

            st.subheader("📉 EMA")
            st.line_chart(pd.DataFrame({
                "Narx": close,
                "EMA 50": ema50,
                "EMA 200": ema200
            }))

            st.subheader("📊 MACD")
            st.line_chart(pd.DataFrame({
                "MACD": macd,
                "Signal": signal
            }))

        else:
            st.warning("Ma'lumotlar hozircha mavjud emas.")

st.divider()

st.subheader("🗂 GOLD AI — Signal tarixi")

if st.session_state.history:
    st.dataframe(
        pd.DataFrame(st.session_state.history),
        use_container_width=True
    )

    if st.button("Tarixni tozalash"):
        st.session_state.history = []
        save_history([])
        st.rerun()
else:
    st.info("Hozircha tarix bo'sh. Birinchi tahlilni bajaring.")
