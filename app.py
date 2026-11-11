
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="GOLD AI", page_icon="🥇", layout="wide")

st.title("🥇 GOLD AI")
st.subheader("XAU/USD — Oltin bozorini kuzatish")
st.info("Demo rejim. Haqiqiy savdo amalga oshirilmaydi.")

if st.button("Bozor ma'lumotlarini yuklash"):

    with st.spinner("Tahlil qilinmoqda..."):

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

            # RSI
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # EMA
            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean()

            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()

            # Oxirgi qiymatlar
            last_price = float(close.iloc[-1])
            last_rsi = float(rsi.dropna().iloc[-1])
            last_ema50 = float(ema50.iloc[-1])
            last_ema200 = float(ema200.iloc[-1])
            last_macd = float(macd.iloc[-1])
            last_signal = float(signal.iloc[-1])

            st.success("Bozor ma'lumotlari tayyor!")

            st.subheader("🥇 Joriy bozor holati")

            c1, c2, c3 = st.columns(3)
            c1.metric("Oltin narxi", round(last_price, 2))
            c2.metric("RSI", round(last_rsi, 2))
            c3.metric("MACD", round(last_macd, 4))

            st.subheader("🤖 GOLD AI — Demo tahlil")

            if last_ema50 > last_ema200:
                trend = "Yuqoriga yo'nalgan trend"
            elif last_ema50 < last_ema200:
                trend = "Pastga yo'nalgan trend"
            else:
                trend = "Aniq trend yo'q"

            if last_rsi >= 70:
                rsi_text = "RSI yuqori"
            elif last_rsi <= 30:
                rsi_text = "RSI past"
            else:
                rsi_text = "RSI o'rtacha"

            if last_macd > last_signal:
                macd_text = "MACD signal chizig'idan yuqori"
            elif last_macd < last_signal:
                macd_text = "MACD signal chizig'idan past"
            else:
                macd_text = "MACD signal bilan teng"

            st.write("**Trend:**", trend)
            st.write("**RSI holati:**", rsi_text)
            st.write("**MACD holati:**", macd_text)

            bullish = sum([
                last_ema50 > last_ema200,
                last_macd > last_signal,
                last_price > last_ema50
            ])

            if bullish == 3:
                st.info("Demo xulosa: indikatorlar yuqoriga yo'nalishni ko'rsatmoqda.")
            elif bullish == 0:
                st.info("Demo xulosa: indikatorlar pastga yo'nalishni ko'rsatmoqda.")
            else:
                st.info("Demo xulosa: indikatorlar bir xil fikrda emas.")

            st.warning(
                "Bu avtomatik indikator tahlili, haqiqiy AI bashorati emas. "
                "Savdo signali yoki foyda kafolati bermaydi."
            )

            st.subheader("📈 Narx grafigi")
            st.line_chart(close)

            st.subheader("📊 RSI grafigi")
            st.line_chart(rsi)

            st.subheader("📉 EMA grafigi")
            st.line_chart(pd.DataFrame({
                "Narx": close,
                "EMA 50": ema50,
                "EMA 200": ema200
            }))

            st.subheader("📊 MACD grafigi")
            st.line_chart(pd.DataFrame({
                "MACD": macd,
                "Signal": signal
            }))

            st.subheader("📋 Narxlar jadvali")
            st.dataframe(data.tail())

        else:
            st.warning("Ma'lumotlar hozircha mavjud emas.")
