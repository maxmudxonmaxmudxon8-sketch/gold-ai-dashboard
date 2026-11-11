
import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import requests
from datetime import datetime

st.set_page_config(
    page_title="GOLD AI",
    page_icon="🥇",
    layout="wide"
)

HISTORY_FILE = "gold_history.json"


# TARIXNI YUKLASH
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


# TARIXNI SAQLASH
def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


# TELEGRAMGA XABAR YUBORISH
def telegram_xabar(matn):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        javob = requests.post(
            url,
            data={"chat_id": chat_id, "text": matn},
            timeout=15
        )

        return javob.json().get("ok", False)

    except Exception:
        return False


# BASHORAT HISOBLASH
def bashorat_hisobla(close, ema12, ema26, ema50, ema200,
                     rsi, macd, signal):

    ball = 0

    if ema12.iloc[-1] > ema26.iloc[-1]:
        ball += 1
    else:
        ball -= 1

    if ema50.iloc[-1] > ema200.iloc[-1]:
        ball += 1
    else:
        ball -= 1

    if rsi.iloc[-1] > 52:
        ball += 1
    elif rsi.iloc[-1] < 48:
        ball -= 1

    if close.iloc[-1] > close.iloc[-5]:
        ball += 1
    else:
        ball -= 1

    if macd.iloc[-1] > signal.iloc[-1]:
        ball += 1
    else:
        ball -= 1

    if ball >= 2:
        yonalish = "Yuqoriga"
    elif ball <= -2:
        yonalish = "Pastga"
    else:
        yonalish = "Noaniq"

    kuch = round(abs(ball) / 5 * 100)

    return yonalish, kuch, ball


# DASHBOARD
st.title("🥇 GOLD AI")
st.subheader("Oltin bozorini kuzatish va tahlil qilish")

st.info(
    "Demo rejim. Tizim real bozor ma'lumotlarini kuzatadi, "
    "lekin haqiqiy savdo qilmaydi."
)

st.caption(
    "Manba: Yahoo Finance — GC=F oltin fyucherslari. "
    "Bu XAU/USD spot narxining aynan o'zi emas."
)

if "history" not in st.session_state:
    st.session_state.history = load_history()


# BOZORNI TAHLIL QILISH
if st.button("🥇 Bozorni tahlil qilish", use_container_width=True):

    with st.spinner("Bozor ma'lumotlari olinmoqda..."):

        try:
            data = yf.download(
                "GC=F",
                period="1mo",
                interval="15m",
                progress=False
            )

            if data.empty:
                st.warning("Bozor ma'lumotlari topilmadi.")

            else:
                close = data["Close"]

                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                close = close.dropna()

                if len(close) < 205:
                    st.warning(
                        "Bashorat uchun yetarli tarixiy ma'lumot yo'q."
                    )

                else:
                    # RSI
                    delta = close.diff()
                    gain = delta.clip(lower=0)
                    loss = -delta.clip(upper=0)

                    avg_gain = gain.rolling(14).mean()
                    avg_loss = loss.rolling(14).mean()

                    rs = avg_gain / avg_loss.replace(0, float("nan"))
                    rsi = 100 - (100 / (1 + rs))

                    # EMA
                    ema12 = close.ewm(
                        span=12, adjust=False
                    ).mean()

                    ema26 = close.ewm(
                        span=26, adjust=False
                    ).mean()

                    ema50 = close.ewm(
                        span=50, adjust=False
                    ).mean()

                    ema200 = close.ewm(
                        span=200, adjust=False
                    ).mean()

                    # MACD
                    macd = ema12 - ema26
                    signal = macd.ewm(
                        span=9, adjust=False
                    ).mean()

                    price = float(close.iloc[-1])
                    rsi_value = float(rsi.iloc[-1])
                    macd_value = float(macd.iloc[-1])
                    signal_value = float(signal.iloc[-1])

                    # TREND
                    if ema50.iloc[-1] > ema200.iloc[-1]:
                        trend = "Yuqoriga"
                    else:
                        trend = "Pastga"

                    # BASHORAT
                    yonalish, kuch, ball = bashorat_hisobla(
                        close, ema12, ema26, ema50,
                        ema200, rsi, macd, signal
                    )

                    vaqt = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    record = {
                        "Vaqt": vaqt,
                        "Narx": round(price, 2),
                        "RSI": round(rsi_value, 2),
                        "MACD": round(macd_value, 4),
                        "Trend": trend,
                        "Bashorat": yonalish,
                        "Signal kuchi": kuch
                    }

                    # TARIXGA SAQLASH
                    st.session_state.history.insert(0, record)
                    st.session_state.history = (
                        st.session_state.history[:100]
                    )

                    save_history(st.session_state.history)

                    # NATIJALAR
                    st.success("Tahlil muvaffaqiyatli yakunlandi!")

                    st.subheader("📊 Joriy bozor holati")

                    c1, c2, c3 = st.columns(3)

                    c1.metric("Oltin narxi", price)
                    c2.metric("RSI", round(rsi_value, 2))
                    c3.metric("MACD", round(macd_value, 4))

                    st.subheader("🤖 GOLD AI bashorati")

                    if yonalish == "Yuqoriga":
                        st.success("📈 Ehtimoliy yo'nalish: YUQORIGA")
                    elif yonalish == "Pastga":
                        st.error("📉 Ehtimoliy yo'nalish: PASTGA")
                    else:
                        st.warning("↔️ Yo'nalish: NOANIQ")

                    st.metric(
                        "Indikatorlar signali kuchi",
                        f"{kuch}%"
                    )

                    st.caption(
                        "Bu foiz bashorat aniqligi yoki foyda ehtimoli "
                        "emas. U indikatorlar ovozining kuchini bildiradi."
                    )

                    st.write("Umumiy trend:", trend)
                    st.write("RSI:", round(rsi_value, 2))
                    st.write("MACD:", round(macd_value, 4))

                    st.warning(
                        "Bu indikatorlarga asoslangan tajribaviy "
                        "bashorat. Keyingi 15 daqiqada yo'nalish "
                        "o'zgarishi mumkin. Bu savdo tavsiyasi emas."
                    )

                    # TELEGRAM
                    xabar = (
                        "🥇 GOLD AI — DEMO TAHLIL\n\n"
                        f"Vaqt: {vaqt}\n"
                        f"Oltin fyuchers narxi: {round(price, 2)}\n"
                        f"RSI: {round(rsi_value, 2)}\n"
                        f"MACD: {round(macd_value, 4)}\n"
                        f"Trend: {trend}\n\n"
                        f"15 daqiqalik taxmin: {yonalish}\n"
                        f"Indikatorlar signali kuchi: {kuch}%\n\n"
                        "Bu tajribaviy demo tahlil. "
                        "Haqiqiy savdo buyrug'i emas."
                    )

                    if telegram_xabar(xabar):
                        st.success("Telegramga xabar yuborildi!")
                    else:
                        st.warning(
                            "Telegram xabari yuborilmadi. "
                            "Secrets sozlamalarini tekshiring."
                        )

                    # GRAFIKLAR
                    st.subheader("📈 Oltin narxi")
                    st.line_chart(close)

                    st.subheader("📊 RSI")
                    st.line_chart(rsi)

                    st.subheader("📉 EMA")
                    st.line_chart(
                        pd.DataFrame({
                            "Narx": close,
                            "EMA 50": ema50,
                            "EMA 200": ema200
                        })
                    )

                    st.subheader("📊 MACD")
                    st.line_chart(
                        pd.DataFrame({
                            "MACD": macd,
                            "Signal": signal
                        })
                    )

        except Exception as e:
            st.error(f"Xatolik yuz berdi: {e}")


# TARIX
st.divider()
st.subheader("🗂 GOLD AI — Tahlil tarixi")

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
    st.info("Hozircha tahlil tarixi bo'sh.")
