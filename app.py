
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="GOLD AI", page_icon="🥇", layout="wide")

st.title("🥇 GOLD AI")
st.subheader("XAU/USD — Oltin bozorini kuzatish")
st.info("Demo rejim. Haqiqiy savdo amalga oshirilmaydi.")

if st.button("Bozor ma'lumotlarini yuklash"):

    with st.spinner("Bozor ma'lumotlari yuklanmoqda..."):

        data = yf.download(
            "GC=F",
            period="5d",
            interval="15m",
            progress=False
        )

        if not data.empty:

            close = data["Close"]

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

            st.success("Ma'lumotlar yuklandi!")

            st.subheader("📈 Oltin narxi")
            st.line_chart(close)

            # RSI
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            st.subheader("📊 RSI")
            st.line_chart(rsi)
            st.metric("RSI qiymati", round(rsi.dropna().iloc[-1], 2))

            # EMA
            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean()

            st.subheader("📉 EMA 50 va EMA 200")
            st.line_chart(pd.DataFrame({
                "Narx": close,
                "EMA 50": ema50,
                "EMA 200": ema200
            }))

            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()

            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()

            st.subheader("📊 MACD")
            st.line_chart(pd.DataFrame({
                "MACD": macd,
                "Signal": signal
            }))

            st.subheader("📋 Narxlar jadvali")
            st.dataframe(data.tail())

        else:
            st.warning("Ma'lumotlar hozircha mavjud emas.")
