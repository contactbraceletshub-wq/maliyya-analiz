import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Professional Analiz Terminalı", layout="wide")

@st.cache_data(ttl=3600)
def get_data(ticker, interval_choice):
    # Zaman diliminə görə data çəkmək
    interval_map = {"Gündəlik": "1d", "Həftəlik": "1wk", "Aylıq": "1mo"}
    t = yf.Ticker(ticker)
    df = t.history(period="2y", interval=interval_map[interval_choice])
    return df, t.info

st.title("🎯 Peşəkar Maliyyə Analiz və Qiymət Proqnozu")

# 1. Giriş Parametrləri
col_input1, col_input2, col_input3 = st.columns(3)
with col_input1:
    ticker_symbol = st.text_input("Ticker daxil edin:", "AAPL").upper()
with col_input2:
    chart_interval = st.selectbox("Şam Zaman Dilimi:", ["Gündəlik", "Həftəlik", "Aylıq"])
with col_input3:
    target_period = st.selectbox("Proqnoz Müddəti:", ["1 Həftəlik", "1 Aylıq", "3 Aylıq", "6 Aylıq", "1 İllik"])

if ticker_symbol:
    try:
        df, info = get_data(ticker_symbol, chart_interval)
        current_price = df['Close'].iloc[-1]
        
        # Texniki Hesablamalar
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        atr = (df['High'] - df['Low']).rolling(window=14).mean().iloc[-1] # Volatillik üçün

        # 2. Şirkət Sağlamlıq Analizi (İdeal Limitlərlə)
        st.subheader("🏛️ Şirkət Sağlamlıq Analizi")
        f1, f2, f3 = st.columns(3)
        
        pe = info.get('trailingPE', 0)
        de = info.get('debtToEquity', 0)
        fcf = info.get('freeCashflow', 0)

        f1.metric("P/E Ratio", f"{pe:.2f}", help="İdeal: < 20-25")
        st.caption(f"P/E: {pe:.2f} (İdeal: 15-25 arası)")
        
        f2.metric("Borc/Kapital", f"{de:.2f}%", help="İdeal: < 100%")
        st.caption(f"Borc/Kapital: {de:.2f} (İdeal: < 100)")
        
        f3.metric("Free Cash Flow", f"${fcf/1e9:.2f}B", help="İdeal: Müsbət və artan")
        st.caption(f"FCF: Müsbət olması sağlamlıq əlamətidir")

        # 3. Qiymət Proqnozu və Giriş/Çıxış (Alqoritmik Hesablama)
        st.divider()
        st.subheader(f"🧩 {target_period} üçün Proqnoz və Ticarət Planı")
        
        # Sadələşdirilmiş Proqnoz Alqoritmi
        volatility_factor = {"1 Həftəlik": 1, "1 Aylıq": 2, "3 Aylıq": 4, "6 Aylıq": 6, "1 İllik": 10}[target_period]
        expected_move = atr * volatility_factor
        
        # Trend analizi
        is_uptrend = current_price > df['SMA_50'].iloc[-1]
        
        if is_uptrend:
            pred_price = current_price + (expected_move * 0.5)
            buy_zone = (current_price - (atr * 0.5), current_price)
            sell_zone = (pred_price * 0.98, pred_price * 1.05)
            signal = "BUY (AL)"
            color = "green"
        else:
            pred_price = current_price - (expected_move * 0.3)
            buy_zone = (pred_price * 0.95, pred_price)
            sell_zone = (current_price, current_price + atr)
            signal = "SELL (SAT)"
            color = "red"

        p1, p2 = st.columns(2)
        with p1:
            st.info(f"**Təxmini Hədəf Qiymət:** ${pred_price:.2f}")
            st.write(f"**Tövsiyə:** :{color}[{signal}]")
        
        with p2:
            st.success(f"**Alış Aralığı (Entry):** ${buy_zone[0]:.2f} - ${buy_zone[1]:.2f}")
            st.error(f"**Satış Aralığı (Target):** ${sell_zone[0]:.2f} - ${sell_zone[1]:.2f}")

        # 4. İnteraktiv Qrafik
        fig = go.Figure(data=[go.Candlestick(x=df.index[-150:], open=df['Open'][-150:], 
                        high=df['High'][-150:], low=df['Low'][-150:], close=df['Close'][-150:], name="Şamlar")])
        fig.add_trace(go.Scatter(x=df.index[-150:], y=df['SMA_50'][-150:], name="SMA 50", line=dict(color='blue')))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Xəta: {e}. Ticker-in düzgünlüyünü yoxlayın.")
