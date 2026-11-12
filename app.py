
import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import requests
from datetime import datetime

# ==========================================
# 1. SAHIFA SOZLAMALARI
# ==========================================

st.set_page_config(
    page_title="GOLD AI",
    page_icon="🥇",
    layout="wide"
)

HISTORY_FILE = "gold_history.json"
PREDICTION_FILE = "prediction_history.json"

GITHUB_STATE_URL = (
    "https://raw.githubusercontent.com/"
    "maxmudxonmaxmudxon8-sketch/"
    "gold-ai-dashboard/main/.gold_ai_state.json"
)


# ==========================================
# 2. GITHUB AVTOMATIK SIGNALINI OLISH
# ==========================================

@st.cache_data(ttl=60)
def get_automatic_signal():
    try:
        response = requests.get(
            GITHUB_STATE_URL,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None


# ==========================================
# 3. TARIXNI O'QISH VA SAQLASH
# ==========================================

def read_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                result = json.load(f)

                if isinstance(result, list):
                    return result

                return []

        except Exception:
            return []

    return []


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ==========================================
# 4. TELEGRAM
# ==========================================

def telegram_xabar(matn):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": matn
            },
            timeout=15
        )

        response.raise_for_status()

        return response.json().get("ok", False)

    except Exception:
        return False


# ==========================================
# 5. BOZOR MA'LUMOTLARINI OLISH
# ==========================================

def get_market_data():

    data = yf.download(
        "GC=F",
        period="1mo",
        interval="15m",
        progress=False
    )

    if data.empty:
        return None, None

    close = data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.to_numeric(
        close,
        errors="coerce"
    ).dropna()

    return data, close


# ==========================================
# 6. INDIKATORLAR
# ==========================================

def calculate_indicators(close):

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        float("nan")
    )

    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain > 0),
        100
    )

    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain == 0),
        50
    )

    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    ema50 = close.ewm(
        span=50,
        adjust=False
    ).mean()

    ema200 = close.ewm(
        span=200,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    return (
        rsi,
        ema12,
        ema26,
        ema50,
        ema200,
        macd,
        signal
    )


# ==========================================
# 7. DEMO BASHORAT
# ==========================================

def make_prediction(
    close,
    rsi,
    ema12,
    ema26,
    ema50,
    ema200,
    macd,
    signal
):

    score = 0

    if ema12.iloc[-1] > ema26.iloc[-1]:
        score += 1
    else:
        score -= 1

    if ema50.iloc[-1] > ema200.iloc[-1]:
        score += 1
    else:
        score -= 1

    if rsi.iloc[-1] > 52:
        score += 1

    elif rsi.iloc[-1] < 48:
        score -= 1

    if close.iloc[-1] > close.iloc[-5]:
        score += 1
    else:
        score -= 1

    if macd.iloc[-1] > signal.iloc[-1]:
        score += 1
    else:
        score -= 1

    if score >= 2:
        direction = "Yuqoriga"

    elif score <= -2:
        direction = "Pastga"

    else:
        direction = "Noaniq"

    strength = round(abs(score) / 5 * 100)

    return direction, strength


# ==========================================
# 8. OLDINGI BASHORATLARNI TEKSHIRISH
# ==========================================

def check_predictions(
    latest_time,
    latest_price,
    predictions
):

    checked_count = 0

    for item in predictions:

        if item.get("Tekshirildi", False):
            continue

        if item.get("Bashorat") == "Noaniq":
            continue

        try:
            start_time = pd.Timestamp(
                item["Vaqt"]
            )

            end_time = pd.Timestamp(
                latest_time
            )

            elapsed = (
                end_time - start_time
            ).total_seconds() / 60

            if elapsed < 15:
                continue

            start_price = float(
                item["Boshlangich_narx"]
            )

            if item["Bashorat"] == "Yuqoriga":
                correct = latest_price > start_price

            else:
                correct = latest_price < start_price

            item["Tekshirildi"] = True

            item["Natija"] = (
                "To'g'ri" if correct else "Noto'g'ri"
            )

            item["Yakuniy_narx"] = round(
                latest_price,
                2
            )

            item["Tekshiruv_vaqti"] = str(
                end_time
            )

            checked_count += 1

            message = (
                "🥇 GOLD AI — BASHORAT TEKSHIRUVI\n\n"
                f"Oldingi bashorat: {item['Bashorat']}\n"
                f"Boshlang'ich narx: {start_price}\n"
                f"Keyingi narx: {round(latest_price, 2)}\n"
                f"Natija: {item['Natija']}\n\n"
                "Bu faqat demo statistikadir."
            )

            telegram_xabar(message)

        except Exception:
            continue

    return checked_count


# ==========================================
# 9. SESSION STATE
# ==========================================

if "history" not in st.session_state:
    st.session_state.history = read_json(
        HISTORY_FILE
    )

if "predictions" not in st.session_state:
    st.session_state.predictions = read_json(
        PREDICTION_FILE
    )


# ==========================================
# 10. DASHBOARD SARLAVHASI
# ==========================================

st.title("🥇 GOLD AI")

st.subheader(
    "Oltin bozorini avtomatik kuzatish va demo tahlil"
)

st.info(
    "Demo rejim. Tizim haqiqiy savdo qilmaydi "
    "va savdo tavsiyasi bermaydi."
)

st.caption(
    "Ma'lumot manbasi: Yahoo Finance — GC=F oltin "
    "fyucherslari. Bu XAU/USD spot narxining aynan o'zi emas."
)


# ==========================================
# 11. GITHUB AVTOMATIK SIGNAL PANELI
# ==========================================

st.divider()

st.subheader("🤖 GOLD AI — AVTOMATIK SIGNAL")

if st.button(
    "🔄 Avtomatik ma'lumotni yangilash",
    use_container_width=True
):

    get_automatic_signal.clear()
    st.rerun()


automatic_state = get_automatic_signal()

if automatic_state:

    auto_signal = automatic_state.get(
        "last_signal",
        "Noma'lum"
    )

    auto_price = automatic_state.get(
        "last_price",
        0
    )

    auto_candle = automatic_state.get(
        "last_candle",
        "Noma'lum"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Oxirgi avtomatik signal",
        auto_signal
    )

    col2.metric(
        "Oxirgi narx",
        f"{float(auto_price):,.2f}"
    )

    col3.metric(
        "Oxirgi saqlangan shamcha",
        auto_candle
    )

    if auto_signal == "YUQORIGA":
        st.success(
            "📈 Avtomatik tizim signali: YUQORIGA"
        )

    elif auto_signal == "PASTGA":
        st.error(
            "📉 Avtomatik tizim signali: PASTGA"
        )

    elif auto_signal == "NEYTRAL":
        st.warning(
            "↔️ Avtomatik tizim signali: NEYTRAL"
        )

    else:
        st.info(
            "Avtomatik signal holati noma'lum."
        )

    st.caption(
        "Bu ma'lumot GitHub Actions tomonidan "
        "saqlangan oxirgi natijadir."
    )

else:

    st.warning(
        "GitHub'dan avtomatik ma'lumot olinmadi. "
        "Internetni yoki GitHub fayl manzilini tekshiring."
    )


# ==========================================
# 12. QO'LDA BOZOR TAHLILI
# ==========================================

st.divider()

st.subheader("📊 Qo'lda bozor tahlili")

if st.button(
    "🥇 Bozorni tahlil qilish",
    use_container_width=True
):

    with st.spinner(
        "Bozor ma'lumotlari olinmoqda..."
    ):

        try:

            data, close = get_market_data()

            if data is None or len(close) < 205:

                st.warning(
                    "Tahlil uchun yetarli bozor "
                    "ma'lumoti topilmadi."
                )

            else:

                (
                    rsi,
                    ema12,
                    ema26,
                    ema50,
                    ema200,
                    macd,
                    signal
                ) = calculate_indicators(close)

                price = float(close.iloc[-1])

                rsi_value = float(rsi.iloc[-1])

                macd_value = float(macd.iloc[-1])

                trend = (
                    "Yuqoriga"
                    if ema50.iloc[-1] > ema200.iloc[-1]
                    else "Pastga"
                )

                direction, strength = make_prediction(
                    close,
                    rsi,
                    ema12,
                    ema26,
                    ema50,
                    ema200,
                    macd,
                    signal
                )

                latest_time = str(
                    close.index[-1]
                )

                current_time = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # OLDINGI BASHORATLARNI TEKSHIRISH

                checked = check_predictions(
                    latest_time,
                    price,
                    st.session_state.predictions
                )

                save_json(
                    PREDICTION_FILE,
                    st.session_state.predictions
                )

                # YANGI BASHORAT

                prediction = {
                    "Vaqt": latest_time,
                    "Boshlangich_narx": round(
                        price,
                        2
                    ),
                    "Bashorat": direction,
                    "Signal_kuchi": strength,
                    "Tekshirildi": False,
                    "Natija": "Kutilmoqda"
                }

                st.session_state.predictions.insert(
                    0,
                    prediction
                )

                st.session_state.predictions = (
                    st.session_state.predictions[:200]
                )

                save_json(
                    PREDICTION_FILE,
                    st.session_state.predictions
                )

                # TAHLIL TARIXI

                record = {
                    "Vaqt": current_time,
                    "Narx": round(price, 2),
                    "RSI": round(rsi_value, 2),
                    "MACD": round(macd_value, 4),
                    "Trend": trend,
                    "Bashorat": direction,
                    "Signal kuchi": strength
                }

                st.session_state.history.insert(
                    0,
                    record
                )

                st.session_state.history = (
                    st.session_state.history[:100]
                )

                save_json(
                    HISTORY_FILE,
                    st.session_state.history
                )

                st.success(
                    "Tahlil yakunlandi!"
                )

                if checked:
                    st.info(
                        f"{checked} ta oldingi bashorat tekshirildi."
                    )

                # KO'RSATKICHLAR

                st.subheader(
                    "📊 Joriy bozor holati"
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Oltin narxi",
                    f"{price:,.2f}"
                )

                c2.metric(
                    "RSI",
                    round(rsi_value, 2)
                )

                c3.metric(
                    "MACD",
                    round(macd_value, 4)
                )

                # BASHORAT

                st.subheader(
                    "🤖 GOLD AI — 15 daqiqalik demo taxmin"
                )

                if direction == "Yuqoriga":

                    st.success(
                        "📈 Ehtimoliy yo'nalish: YUQORIGA"
                    )

                elif direction == "Pastga":

                    st.error(
                        "📉 Ehtimoliy yo'nalish: PASTGA"
                    )

                else:

                    st.warning(
                        "↔️ Yo'nalish: NOANIQ"
                    )

                st.metric(
                    "Indikatorlar signali kuchi",
                    f"{strength}%"
                )

                st.caption(
                    "Bu aniqlik foizi emas, indikatorlar "
                    "ovozining kuchini bildiradi."
                )

                st.write(
                    "Umumiy trend:",
                    trend
                )

                st.warning(
                    "Bashorat tajribaviy. Keyingi narx "
                    "o'zgarishi boshqacha bo'lishi mumkin. "
                    "Bu savdo tavsiyasi emas."
                )

                # TELEGRAM

                message = (
                    "🥇 GOLD AI — DEMO TAHLIL\n\n"
                    f"Vaqt: {current_time}\n"
                    f"Oltin narxi: {round(price, 2)}\n"
                    f"RSI: {round(rsi_value, 2)}\n"
                    f"MACD: {round(macd_value, 4)}\n"
                    f"Trend: {trend}\n"
                    f"15 daqiqalik taxmin: {direction}\n"
                    f"Signal kuchi: {strength}%\n\n"
                    "Bu tajribaviy demo tahlil."
                )

                if telegram_xabar(message):

                    st.success(
                        "Telegramga xabar yuborildi!"
                    )

                else:

                    st.warning(
                        "Telegram xabari yuborilmadi."
                    )

                # GRAFIKLAR

                st.subheader(
                    "📈 Oltin narxi"
                )

                st.line_chart(close)

                st.subheader(
                    "📊 RSI"
                )

                st.line_chart(rsi)

                st.subheader(
                    "📉 EMA"
                )

                st.line_chart(
                    pd.DataFrame({
                        "Narx": close,
                        "EMA 50": ema50,
                        "EMA 200": ema200
                    })
                )

                st.subheader(
                    "📊 MACD"
                )

                st.line_chart(
                    pd.DataFrame({
                        "MACD": macd,
                        "Signal": signal
                    })
                )

        except Exception as e:

            st.error(
                f"Xatolik: {e}"
            )


# ==========================================
# 13. BASHORAT STATISTIKASI
# ==========================================

st.divider()

st.subheader(
    "🎯 Bashorat natijalari"
)

predictions = st.session_state.predictions

checked_items = [
    p for p in predictions
    if p.get("Tekshirildi", False)
]

correct_count = sum(
    1 for p in checked_items
    if p.get("Natija") == "To'g'ri"
)

wrong_count = sum(
    1 for p in checked_items
    if p.get("Natija") == "Noto'g'ri"
)

total = len(checked_items)

a, b, c = st.columns(3)

a.metric(
    "Tekshirilgan",
    total
)

b.metric(
    "To'g'ri",
    correct_count
)

c.metric(
    "Noto'g'ri",
    wrong_count
)

if total > 0:

    accuracy = round(
        correct_count / total * 100,
        1
    )

    st.metric(
        "Tarixiy natijalar bo'yicha mos kelish",
        f"{accuracy}%"
    )

else:

    st.info(
        "Hozircha tekshirilgan bashoratlar yo'q. "
        "15 daqiqadan keyin bozor tahlilini yana bajaring."
    )

if predictions:

    st.dataframe(
        pd.DataFrame(predictions),
        use_container_width=True
    )


# ==========================================
# 14. TAHLIL TARIXI
# ==========================================

st.divider()

st.subheader(
    "🗂 GOLD AI — Tahlil tarixi"
)

if st.session_state.history:

    st.dataframe(
        pd.DataFrame(st.session_state.history),
        use_container_width=True
    )

    if st.button(
        "Tahlil tarixini tozalash"
    ):

        st.session_state.history = []

        save_json(
            HISTORY_FILE,
            []
        )

        st.rerun()

else:

    st.info(
        "Hozircha tarix bo'sh."
    )


# ==========================================
# 15. OXIRGI ESLATMA
# ==========================================

st.divider()

st.caption(
    "GOLD AI — tajribaviy kuzatuv tizimi. "
    "GC=F oltin fyucherslari ma'lumotlaridan foydalanadi. "
    "Signallar kafolatlangan natija bermaydi."
)
