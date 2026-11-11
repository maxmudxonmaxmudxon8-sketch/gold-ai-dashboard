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
            st.success("Ma'lumotlar yuklandi!")
            st.line_chart(data["Close"])
            st.dataframe(data.tail())
        else:
            st.warning("Ma'lumotlar hozircha mavjud emas.")
