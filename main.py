import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Səhifənin geniş formatda ayarlanması
st.set_page_config(page_title="Universal Analiz Terminalı", layout="wide")

st.title("📊 Universal Maliyyə və Texniki Analiz Platforması")
st.markdown("Dəyər investorları və peşəkar treyderlər üçün tək ekranlı analiz terminalı.")

# İstifadəçidən Ticker almaq (Axtarış Modulu V1)
ticker_symbol = st.text_input("Şirkətin Tickerini daxil edin (məsələn: AAPL, TSLA, BRK-B):", "AAPL").upper()

if ticker_symbol:
    with st.spinner(f"{ticker_symbol} məlumatları yüklənir..."):
        try:
            # yfinance vasitəsilə 1 illik məlumatın çəkilməsi
            ticker_data = yf.Ticker(ticker_symbol)
            df = ticker_data.history(period="1y")

            if not df.empty:
                # Cari qiymət və şirkət adı
                info = ticker_data.info
                company_name = info.get("shortName", ticker_symbol)
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                price_change = current_price - prev_price
                change_percent = (price_change / prev_price) * 100

                # Göstəricilərin ekrana yazdırılması
                col1, col2, col3 = st.columns(3)
                col1.metric("Şirkət", company_name)
                col2.metric("Cari Qiymət (USD)", f"${current_price:.2f}", f"{price_change:.2f} ({change_percent:.2f}%)")
                
                # Texniki Analiz: SMA 50 və SMA 200 hesablanması
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()

                st.subheader(f"📈 {ticker_symbol} - 1 İllik Şam Qrafiki və Trend Analizi")

                # Plotly ilə interaktiv Şam (Candlestick) qrafikinin qurulması
                fig = go.Figure()

                # Şamlar
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'],
                                name='Qiymət'))

                # SMA 50 Xətti
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                                mode='lines', 
                                line=dict(color='blue', width=1.5),
                                name='SMA 50'))

                # SMA 200 Xətti
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], 
                                mode='lines', 
                                line=dict(color='orange', width=1.5),
                                name='SMA 200'))

                fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.error("Məlumat tapılmadı. Zəhmət olmasa düzgün ticker daxil etdiyinizə əmin olun.")
        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
