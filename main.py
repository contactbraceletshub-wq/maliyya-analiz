import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="ProAnaliz Terminalı", layout="wide")

@st.cache_data(ttl=3600)
def get_data(ticker):
    t = yf.Ticker(ticker)
    return t.history(period="2y"), t.info

st.title("🎯 Peşəkar Analiz və Zaman Proqnozları")

# 1. Ticker və Zaman Seçimi
col_input1, col_input2 = st.columns([1, 1])
with col_input1:
    ticker_symbol = st.text_input("Ticker daxil edin (məs: AAPL):", "AAPL").upper()
with col_input2:
    target_period = st.selectbox("Analiz və Proqnoz müddəti:", 
                                 ["1 Həftəlik", "1 Aylıq", "3 Aylıq", "6 Aylıq", "1 İllik"])

if ticker_symbol:
    try:
        df, info = get_data(ticker_symbol)
        
        # Göstəricilərin hesablanması
        current_price = df['Close'].iloc[-1]
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        rsi_now = df['RSI'].iloc[-1]

        # 2. YAP-BOZ ANALİZİ (Məntiq mərkəzi)
        st.markdown(f"### 🧩 {target_period} üçün Strateji Analiz")
        
        # Proqnoz Məntiqi (Trend + Fundamental + RSI kombinasiyası)
        trend = "Müsbət" if current_price > df['SMA_50'].iloc[-1] else "Mənfi"
        pe_val = info.get('trailingPE', 25)
        
        # Proqnoz Hesablanması (Simulyasiya edilmiş peşəkar rəy)
        if trend == "Müsbət" and rsi_now < 70 and pe_val < 30:
            outlook = "Yüksəliş ehtimalı yüksəkdir"
            signal = "BUY (AL)"
            color = "green"
        elif trend == "Mənfi" or rsi_now > 75:
            outlook = "Düzəliş (Eniş) gözlənilir"
            signal = "SELL (SAT)"
            color = "red"
        else:
            outlook = "Stabil / Gözləmə mövqeyi"
            signal = "HOLD (GÖZLƏ)"
            color = "orange"

        # 3. Nəticə Cədvəli
        res1, res2, res3 = st.columns(3)
        res1.metric("Cari Qiymət", f"${current_price:.2f}")
        res2.metric("Trend İstiqaməti", trend)
        res3.metric("RSI (Güc)", f"{rsi_now:.2f}")

        st.info(f"**Yekun Proqnoz ({target_period}):** {outlook} | **Tövsiyə:** :{color}[{signal}]")

        # 4. Fundamental Sağlamlıq bölməsi
        with st.expander("Şirkətin Fundamental Sağlamlıq Analizi"):
            st.write(f"**P/E Ratio:** {pe_val} (Sektor ortalaması ilə müqayisə edilməlidir)")
            st.write(f"**Borc/Kapital:** {info.get('debtToEquity', 'N/A')}")
            st.write(f"**Free Cash Flow:** {info.get('freeCashflow', 'N/A')}")

        # 5. Qrafik
        fig = go.Figure(data=[go.Candlestick(x=df.index[-100:], open=df['Open'][-100:], 
                        high=df['High'][-100:], low=df['Low'][-100:], close=df['Close'][-100:])])
        fig.update_layout(title=f"{ticker_symbol} Son 100 Şam", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Xəta: {e}")
