import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Universal Maliyyə Terminalı", layout="wide")

# Keşləmə funksiyası (Rate limit xətasının qarşısını almaq üçün)
@st.cache_data(ttl=3600)  # Məlumatları 1 saat yaddaşda saxlayır
def get_stock_data(ticker):
    data = yf.Ticker(ticker)
    hist = data.history(period="1y")
    info = data.info
    return hist, info

st.title("📊 Universal Maliyyə və Texniki Analiz Platforması")
st.markdown("---")

# Yan panel - Axtarış
st.sidebar.header("Axtarış Parametrləri")
ticker_symbol = st.sidebar.text_input("Şirkət Tickerini daxil edin:", "AAPL").upper()

if ticker_symbol:
    try:
        with st.spinner('Məlumatlar analiz edilir...'):
            df, info = get_stock_data(ticker_symbol)

            if not df.empty:
                # 1. Əsas Göstəricilər (Metrics)
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                price_change = current_price - prev_price
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Şirkət", info.get('shortName', ticker_symbol))
                col2.metric("Qiymət", f"${current_price:.2f}", f"{price_change:.2f}")
                col3.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                col4.metric("Dividend", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")

                # 2. Texniki Analiz (SMA və RSI)
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
                
                # RSI Hesablanması
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

                st.subheader("📈 Texniki Trend və Qrafik")
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Qiymət"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA 50 (Trend)", line=dict(color='blue', width=1.5)))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name="SMA 200 (Güç)", line=dict(color='orange', width=1.5)))
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # 3. Yekun Rəy (Yap-boz Analizi)
                st.divider()
                st.subheader("🧩 Analiz Xülasəsi və Yekun Rəy")
                
                rsi_val = df['RSI'].iloc[-1]
                score = 0
                
                # Skorlama məntiqi
                if current_price > df['SMA_50'].iloc[-1]: score += 25
                if current_price > df['SMA_200'].iloc[-1]: score += 25
                if 30 < rsi_val < 70: score += 25
                if info.get('trailingPE', 100) < 30: score += 25

                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.write(f"**RSI (Momentum):** {rsi_val:.2f}")
                    if rsi_val > 70: st.warning("Həddindən artıq alış (Riskli)")
                    elif rsi_val < 30: st.success("Həddindən artıq satış (Fürsət)")
                    else: st.info("Momentum neytraldır.")

                with res_col2:
                    st.write(f"**Güvən Skoru:** {score}%")
                    if score >= 75: st.success("YEKUN RƏY: GÜCLÜ AL (BUY)")
                    elif score >= 50: st.warning("YEKUN RƏY: GÖZLƏ (HOLD)")
                    else: st.error("YEKUN RƏY: SAT (SELL)")

            else:
                st.error("Ticker tapılmadı və ya data yüklənmədi.")
    except Exception as e:
        st.error(f"Xəta baş verdi: {e}")
