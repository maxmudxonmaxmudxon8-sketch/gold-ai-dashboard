
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="GOLD AI",
    page_icon="🥇",
    layout="wide"
)

st.title("🥇 GOLD AI")
st.subheader("XAU/USD — Oltin bozorini kuzatish")

st.info("Demo rejim. Bu tizim haqiqiy savdo qilmaydi.")

if st.button("Bozor ma'lumotlarini yuklash"):

    with st.spinner("Ma'lumotlar yuklanmoqda..."):

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

            st.subheader("📈 Oltin narxi grafigi")
            st.line_chart(close)

            st.subheader("📊 RSI indikatori")

            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            st.line_chart(rsi)

            last_rsi = rsi.dropna().iloc[-1]

            st.metric("Oxirgi RSI qiymati", round(last_rsi, 2))

            if last_rsi >= 70:
                st.warning("RSI 70 dan yuqori: bozor haddan tashqari xarid qilingan bo‘lishi mumkin.")
            elif last_rsi <= 30:
                st.warning("RSI 30 dan past: bozor haddan tashqari sotilgan bo‘lishi mumkin.")
            else:
                st.info("RSI 30–70 oralig‘ida.")

            st.subheader("📋 Narxlar jadvali")
            st.dataframe(data.tail())

        else:
            st.warning("Ma'lumotlar hozircha mavjud emas.")
