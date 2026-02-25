import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Səhifə ayarları
st.set_page_config(page_title="Peşəkar Maliyyə Analizi", layout="wide")

st.title("🎯 Peşəkar Maliyyə Analiz və Qiymət Proqnozu")

# --- FUNKSİYALAR ---

@st.cache_data(ttl=3600)  # Məlumatı 1 saat yaddaşda saxlayır (Limiti aşmamaq üçün)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        # Son 1 illik məlumatı çəkirik
        df = stock.history(period="1y")
        
        if df.empty:
            return None, "Məlumat tapılmadı. Ticker-i düzgün yazdığınızdan əmin olun."
        
        info = stock.info
        return {"df": df, "info": info}, None
    
    except Exception as e:
        error_msg = str(e)
        if "Too Many Requests" in error_msg or "429" in error_msg:
            return None, "Sistem xətası: Çox sayda sorğu göndərilib. Zəhmət olmasa 5-10 dəqiqə gözləyin."
        return None, f"Xəta baş verdi: {error_msg}"

# --- İSTİFADƏÇİ İNTERFEYSİ ---

col1, col2 = st.columns([2, 1])

with col1:
    ticker = st.text_input("Şirkətin adını və ya Tickerini daxil edin (məs: AAPL, NVDA):", value="AAPL").upper()

with col2:
    period_options = {"1 Həftəlik": 7, "1 Aylıq": 30, "3 Aylıq": 90}
    selection = st.selectbox("Proqnoz Müddəti:", list(period_options.keys()))

if ticker:
    data, error = get_stock_data(ticker)
    
    if error:
        st.error(error)
    else:
        df = data["df"]
        info = data["info"]
        
        # Cari qiymət və dəyişim
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = current_price - prev_price
        
        st.metric(label=f"{info.get('longName', ticker)} Cari Qiymət", 
                  value=f"{current_price:.2f} USD", 
                  delta=f"{change:.2f} USD")

        # Qrafik
        st.subheader("Qiymət Qrafiki (Son 1 İl)")
        st.line_chart(df['Close'])

        # Analiz bölməsi (Warren Buffett tərzi sadə fundamentallar)
        st.subheader("📊 Fundamental Göstəricilər")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            st.write(**P/E Ratio:** {info.get('trailingPE', 'N/A')})
        with f_col2:
            st.write(**Market Cap:** {info.get('marketCap', 'N/A'):,})
        with f_col3:
            st.write(**Dividend Yield:** {info.get('dividendYield', 0)*100:.22f}%)

else:
    st.info("Analizə başlamaq üçün yuxarıya bir ticker daxil edin.")
