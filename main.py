import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="Professional Analiz Terminalı", layout="wide")

# 1. Şirkət adına görə Ticker tapmaq üçün API funksiyası
@st.cache_data(ttl=86400)
def get_ticker_from_name(query):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'quotes' in data and len(data['quotes']) > 0:
            return data['quotes'][0]['symbol']
    except Exception:
        pass
    return query.upper()

# 2. Maliyyə datalarını çəkmək üçün funksiya
@st.cache_data(ttl=3600)
def get_data(ticker):
    t = yf.Ticker(ticker)
    df = t.history(period="2y")
    return df, t.info

st.title("🎯 Peşəkar Maliyyə Analiz və Qiymət Proqnozu")

# Giriş Parametrləri
col_input1, col_input2 = st.columns([2, 1])
with col_input1:
    user_query = st.text_input("Şirkətin adını və ya Tickerini daxil edin (məs: Apple və ya AAPL):", "Apple")
with col_input2:
    target_period = st.selectbox("Proqnoz Müddəti:", ["1 Həftəlik", "1 Aylıq", "3 Aylıq", "6 Aylıq", "1 İllik"])

if user_query:
    with st.spinner('Məlumatlar axtarılır və analiz edilir...'):
        try:
            # Tickerin tapılması
            ticker_symbol = get_ticker_from_name(user_query)
            
            df, info = get_data(ticker_symbol)
            if df.empty:
                st.error("Məlumat tapılmadı. Zəhmət olmasa fərqli ad daxil edin.")
                st.stop()
                
            current_price = df['Close'].iloc[-1]
            company_name = info.get('shortName', ticker_symbol)
            
            st.markdown(f"### 📊 {company_name} ({ticker_symbol}) - Aktiv Analizi")

            # Texniki Hesablamalar (Proqnoz üçün)
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            atr = (df['High'] - df['Low']).rolling(window=14).mean().iloc[-1]

            # Şirkət Sağlamlıq Analizi
            st.subheader("🏛️ Şirkət Sağlamlıq Analizi")
            f1, f2, f3 = st.columns(3)
            
            pe = info.get('trailingPE', 0)
            de = info.get('debtToEquity', 0)
            fcf = info.get('freeCashflow', 0)

            f1.metric("P/E Ratio", f"{pe:.2f}", help="İdeal: < 20-25")
            st.caption(f"P/E: {pe:.2f} (İdeal: 15-25 arası)")
            
            f2.metric("Borc/Kapital", f"{de:.2f}%", help="İdeal: < 100%")
            st.caption(f"Borc/Kapital: {de:.2f} (İdeal: < 100)")
            
            f3.metric("Free Cash Flow", f"${fcf/1e9:.2f}B" if fcf else "N/A", help="İdeal: Müsbət və artan")
            st.caption(f"FCF: Müsbət olması sağlamlıq əlamətidir")

            # Qiymət Proqnozu və Ticarət Planı
            st.divider()
            st.subheader(f"🧩 {target_period} üçün Proqnoz və Ticarət Planı")
            
            volatility_factor = {"1 Həftəlik": 1, "1 Aylıq": 2, "3 Aylıq": 4, "6 Aylıq": 6, "1 İllik": 10}[target_period]
            expected_move = atr * volatility_factor
            
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

            # Orijinal TradingView İnteqrasiyası
            st.divider()
            st.subheader("📈 Qabaqcıl İnteraktiv Qrafik (TradingView)")
            
            # TradingView HTML/JS Widget kodu
            html_code = f"""
            <div class="tradingview-widget-container" style="height:600px;width:100%">
              <div id="tradingview_chart" style="height:100%;width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {{
              "autosize": true,
              "symbol": "{ticker_symbol}",
              "interval": "D",
              "timezone": "Etc/UTC",
              "theme": "dark",
              "style": "1",
              "locale": "en",
              "enable_publishing": false,
              "backgroundColor": "rgba(19, 23, 34, 1)",
              "gridColor": "rgba(42, 46, 57, 1)",
              "hide_top_toolbar": false,
              "hide_legend": false,
              "save_image": false,
              "container_id": "tradingview_chart",
              "toolbar_bg": "#f1f3f6",
              "withdateranges": true,
              "allow_symbol_change": false,
              "studies": [
                "STD;SMA"
              ]
            }}
              );
              </script>
            </div>
            """
            components.html(html_code, height=600)

        except Exception as e:
            st.error(f"Sistem xətası: Şirkət adını və ya Ticker-i düzgün yazdığınızdan əmin olun. (Xəta detalı: {e})")
