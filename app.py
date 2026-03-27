import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# ==============================================================
# [1] 토스 프리미엄 디자인 & 레이아웃 설정
# ==============================================================
st.set_page_config(page_title="하이브리드 투자 봇", page_icon="🎯", layout="wide")

# 오늘 날짜 (2026년 기준)
TODAY = datetime.date.today()
MAX_DATE = datetime.date(2026, 12, 31) 

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .toss-card { background-color: #f2f4f6; border-radius: 24px; padding: 28px; margin-bottom: 24px; }
    .toss-card-white { background-color: #ffffff; border: 1px solid #e5e8eb; border-radius: 20px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
    .toss-title { color: #191f28; font-weight: 800; font-size: 28px; margin-bottom: 8px; }
    .toss-desc { color: #4e5968; font-size: 16px; margin-bottom: 32px; }
    .toss-huge { font-size: 38px; font-weight: 900; letter-spacing: -1.2px; margin: 8px 0; }
    .toss-red { color: #f04452; }
    .toss-blue { color: #3182f6; }
    .toss-gray { color: #8b95a1; font-size: 14px; font-weight: 500; }
    .toss-dark { color: #333d4b; font-weight: 700; font-size: 19px; }
</style>
""", unsafe_allow_html=True)

TICKER_OPTIONS = {
    "QLD (나스닥 100 2배)": "QLD",
    "418660.KS (KODEX 나스닥 2배)": "418660.KS",
    "426030.KS (TIME 액티브)": "426030.KS",
    "0015B0.KS (KoAct 성장기업)": "0015B0.KS"
}

def fmt_p(ticker, val):
    if ticker == "QLD": return f"${val:,.2f}"
    return f"{int(val):,}원"

st.markdown("<div class='toss-title'>나만의 하이브리드 투자 봇 🤖</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎯 오늘의 스나이퍼 타점", "📉 무제한 시뮬레이터"])

# ==============================================================
# [2] 탭 1: 스나이퍼 타점 계산기
# ==============================================================
with tab1:
    st.markdown("<div class='toss-desc'>오늘 장에서 사야 할지 팔아야 할지, 토스가 계산해 봤어요.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    selected_label = c1.selectbox("종목을 골라주세요", list(TICKER_OPTIONS.keys()))
    ticker_t1 = TICKER_OPTIONS[selected_label]

    if st.button("🔥 지금 가장 유리한 가격 확인하기", use_container_width=True):
        with st.spinner("최신 시장 데이터 분석 중..."):
            df_t = yf.download(ticker_t1, period="2y", auto_adjust=True, progress=False)
            df_m = yf.download("QQQ", period="2y", auto_adjust=True, progress=False)
            if df_t.index[-1].date() == TODAY:
                df_t, df_m = df_t.iloc[:-1], df_m.iloc[:-1]
            
            close_s, qqq_s = df_t['Close'].squeeze(), df_m['Close'].squeeze()
            sma200 = qqq_s.rolling(window=200).mean()
            is_bull = qqq_s.iloc[-1] > sma200.iloc[-1]
            
            delta = close_s.diff()
            gain = delta.where(delta > 0, 0).ewm(alpha=0.5, adjust=False).mean()
            loss = -delta.where(delta < 0, 0).ewm(alpha=0.5, adjust=False).mean()
            l_close, l_up, l_down = float(close_s.iloc[-1]), float(gain.iloc[-1]), float(loss.iloc[-1])
            curr_rsi = 100 - (100 / (1 + l_up/l_down)) if l_down != 0 else 100
            
            t_buy_rsi, t_sell_rsi = (19, 96) if is_bull else (28, 54)
            def solve(trsi, c, u, d):
                tr = trsi / (100 - trsi)
                return c + (tr*d*0.5 - u*0.5)/0.5 if trsi > (100-(100/(1+u/d)) if d!=0 else 100) else c - (u*0.5/tr - d*0.5)/0.5
            buy_p, sell_p = solve(t_buy_rsi, l_close, l_up, l_down), solve(t_sell_rsi, l_close, l_up, l_down)

            st.markdown(f"""
            <div class='toss-card'>
                <div class='toss-gray'>기준일: {df_t.index[-1].strftime('%Y년 %m월 %d일')}</div>
                <div style='font-size: 22px; font-weight: bold; color: #333d4b;'>지금 시장은 <span style='color:{"#f04452" if is_bull else "#3182f6"};'>{"상승장" if is_bull else "하락장"}</span> 이에요 📈</div>
                <div style='display:flex; justify-content:space-between; margin-top:20px; background:white; padding:18px; border-radius:14px;'>
                    <div><div class='toss-gray'>현재 가격</div><div class='toss-dark'>{fmt_p(ticker_t1, l_close)}</div></div>
                    <div><div class='toss-gray'>과열도(RSI)</div><div class='toss-dark'>{curr_rsi:.1f}</div></div>
                    <div><div class='toss-gray'>지수(QQQ)</div><div class='toss-dark'>${qqq_s.iloc[-1]:.2f}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            ca, cb = st.columns(2)
            ca.markdown(f"<div class='toss-card-white' style='border-top: 6px solid #f04452;'><div class='toss-gray'>🛒 사야 할 가격 (RSI {t_buy_rsi})</div><div class='toss-huge toss-red'>{fmt_p(ticker_t1, buy_p)}</div><div class='toss-gray'>지금보다 <b>{((buy_p/l_close-1)*100):+.2f}%</b> 낮을 때</div></div>", unsafe_allow_html=True)
            cb.markdown(f"<div class='toss-card-white' style='border-top: 6px solid #3182f6;'><div class='toss-gray'>🎉 팔아야 할 가격 (RSI {t_sell_rsi})</div><div class='toss-huge toss-blue'>{fmt_p(ticker_t1, sell_p)}</div><div class='toss-gray'>지금보다 <b>{((sell_p/l_close-1)*100):+.2f}%</b> 높을 때</div></div>", unsafe_allow_html=True)

# ==============================================================
# [3] 탭 2: 백테스트 시뮬레이터 (투자 기간 & 연도 추가)
# ==============================================================
with tab2:
    st.markdown("<div class='toss-desc'>과거의 폭락장을 이 전략으로 버텼다면 지금 얼마가 되었을까요?</div>", unsafe_allow_html=True)
    with st.form("backtest_form"):
        c1, c2 = st.columns(2)
        target_bt = c1.selectbox("종목 선택", list(TICKER_OPTIONS.keys()))
        TARGET_TICKER = TICKER_OPTIONS[target_bt]
        
        c3, c4 = st.columns(2)
        T_START = c3.date_input("투자 시작 날짜", value=datetime.date(2008, 1, 1), min_value=datetime.date(1990, 1, 1), max_value=MAX_DATE)
        T_END = c4.date_input("투자 종료 날짜", value=TODAY, min_value=datetime.date(1990, 1, 1), max_value=MAX_DATE)
        
        c5, c6 = st.columns(2)
        INIT_CAP = c5.number_input("시작 금액 (원)", value=50000000, step=1000000)
        MON_INJ = c6.number_input("매달 넣을 돈 (원)", value=2000000, step=100000)
        submitted = st.form_submit_button("📉 시뮬레이션 결과 보기", use_container_width=True)

    if submitted:
        with st.spinner("데이터 분석 중..."):
            START_D = T_START - datetime.timedelta(days=365)
            df_m = yf.download("QQQ", start=START_D, end=T_END, progress=False)['Close'].squeeze()
            df_t_c = yf.download(TARGET_TICKER, start=START_D, end=T_END, progress=False)['Close'].squeeze()
            df_t_l = yf.download(TARGET_TICKER, start=START_D, end=T_END, progress=False)['Low'].squeeze()
            df = pd.DataFrame({"QQQ": df_m, "Target": df_t_c, "Low": df_t_l}).dropna()
            df['SMA'] = df['QQQ'].rolling(window=200).mean()
            df['IsBull'] = (df['QQQ'] > df['SMA']) & (df['QQQ'].shift(1) > df['SMA'].shift(1))
            delta = df['Target'].diff()
            up = delta.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
            down = -delta.clip(upper=0).ewm(alpha=0.5, adjust=False).mean()
            df['RSI'] = 100 - (100 / (1 + up/down))
            df = df.loc[pd.Timestamp(T_START):].dropna()

            cash, invested, shares, avg_p = INIT_CAP, INIT_CAP, 0, 0.0
            peak, mdd, win, lose, entry_date = INIT_CAP, 0.0, 0, 0, None
            hold_periods, logs, last_inj_m = [], [], None
            bnh_shares = invested / df['Target'].iloc[0]; qqq_shares = invested / df['QQQ'].iloc[0]
            b_peak, q_peak, b_mdd, q_mdd = invested, invested, 0.0, 0.0

            for d, r in df.iterrows():
                p, low, q_p, rsi, bull = r['Target'], r['Low'], r['QQQ'], r['RSI'], r['IsBull']
                d_s = d.strftime('%Y.%m.%d')
                if d.day >= 25 and last_inj_m != d.month:
                    cash += MON_INJ; invested += MON_INJ; bnh_shares += MON_INJ/p; qqq_shares += MON_INJ/q_p; last_inj_m = d.month
                    logs.append({"date": d_s, "icon": "💰", "color": "#333d4b", "title": "월급 투입", "desc": f"+{MON_INJ/10000:,.0f}만원", "asset": (cash + shares * p)})
                if shares > 0:
                    sp = avg_p * 0.9
                    if (not bull) and (low <= sp):
                        lose += 1; profit = (sp - avg_p) * shares; hold_periods.append((d - entry_date).days)
                        cash += shares * sp; shares, avg_p = 0, 0.0
                        logs.append({"date": d_s, "icon": "💧", "color": "#3182f6", "title": "방어적 손절", "desc": f"-10.00% ({profit/10000:,.0f}만원)", "asset": cash})
                    elif rsi > (96 if bull else 54):
                        profit = (p - avg_p) * shares; p_pct = (p/avg_p-1)*100
                        if p_pct > 0: win += 1
                        else: lose += 1
                        hold_periods.append((d - entry_date).days)
                        cash += shares * p; shares, avg_p = 0, 0.0
                        logs.append({"date": d_s, "icon": "🎉" if p_pct>0 else "💧", "color": "#f04452" if p_pct>0 else "#3182f6", "title": "전량 매도", "desc": f"{p_pct:+.2f}% ({profit/10000:+,.0f}만원)", "asset": cash})
                if shares == 0 and rsi < (19 if bull else 28):
                    ratio = 1.0 if bull else 0.5; buy_amt = cash * ratio
                    if buy_amt > 10000:
                        shares = buy_amt / p; cash -= buy_amt; avg_p = p; entry_date = d
                        logs.append({"date": d_s, "icon": "🛒", "color": "#333d4b", "title": f"매수({int(ratio*100)}%)", "desc": f"체결: {fmt_p(TARGET_TICKER, p)}", "asset": (cash + shares * p)})
                cv = cash + shares * p; peak = max(peak, cv); mdd = min(mdd, (cv - peak)/peak*100)
                bv = bnh_shares * p; b_peak = max(b_peak, bv); b_mdd = min(b_mdd, (bv - b_peak)/b_peak*100)
                qv = qqq_shares * q_p; q_peak = max(q_peak, qv); q_mdd = min(q_mdd, (qv - q_peak)/q_peak*100)

            # 통계 데이터 (투자 기간 계산 추가)
            final_v = cash + shares * df['Target'].iloc[-1]
            total_r = (final_v/invested-1)*100
            
            # 투자 기간 계산 (일수 및 연수)
            total_days = (df.index[-1] - df.index[0]).days
            yrs = total_days / 365.25
            
            cagr = ((final_v / invested)**(1/yrs)-1)*100 if yrs > 0 else 0
            b_final = bnh_shares * df['Target'].iloc[-1]; b_r = (b_final/invested-1)*100; b_cagr = ((b_final/invested)**(1/yrs)-1)*100 if yrs > 0 else 0
            q_final = qqq_shares * df['QQQ'].iloc[-1]; q_r = (q_final/invested-1)*100; q_cagr = ((q_final/invested)**(1/yrs)-1)*100 if yrs > 0 else 0

            # 📋 토스 스타일 성적표 카드 (투자 기간 강조)
            st.markdown(f"""
            <div class='toss-card'>
                <h3 style='margin:0;'>{TARGET_TICKER} 투자 요약 📝</h3>
                <p class='toss-desc'>
                    {df.index[0].strftime('%Y.%m.%d')}부터 {df.index[-1].strftime('%Y.%m.%d')}까지<br>
                    <b>총 {total_days:,}일 ({yrs:.1f}년)</b> 동안 <b>{invested/10000:,.0f}만원</b>을 넣었어요.
                </p>
                <div class='toss-huge toss-{"red" if total_r>0 else "blue"}'>{(final_v-invested)/10000:+,.0f}만원 ({total_r:+.2f}%)</div>
                <div style='background:white; padding:14px; border-radius:10px; font-size:14px; color:#4e5968;'>
                    💡 그냥 가지고만 있었을 때보다 <b>{(final_v-b_final)/10000:,.0f}만원</b>을 더 {"지켜냈어요! 🛡️" if final_v>b_final else "잃었네요.."}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='toss-card-white'><div class='toss-gray'>내 전략 🎯</div><div class='toss-dark' style='font-size:24px;'>CAGR {cagr:.1f}%</div><div class='toss-gray'>최대낙폭: <b class='toss-blue'>{mdd:.1f}%</b></div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='toss-card-white'><div class='toss-gray'>{TARGET_TICKER} 단순 보유</div><div class='toss-dark' style='font-size:24px;'>CAGR {b_cagr:.1f}%</div><div class='toss-gray'>최대낙폭: <b class='toss-blue'>{b_mdd:.1f}%</b></div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='toss-card-white'><div class='toss-gray'>시장(QQQ) 성적</div><div class='toss-dark' style='font-size:24px;'>CAGR {q_cagr:.1f}%</div><div class='toss-gray'>최대낙폭: <b class='toss-blue'>{q_mdd:.1f}%</b></div></div>", unsafe_allow_html=True)

            # 매매 통계 요약
            st.markdown(f"""
            <div class='toss-card-white'>
                <div class='toss-gray'>매매 기록 분석</div>
                <div style='display:flex; justify-content:space-between; margin-top:12px;'>
                    <div><span class='toss-gray'>총 거래</span><br><span class='toss-dark'>{win+lose}회</span></div>
                    <div><span class='toss-gray'>매매 승률</span><br><span class='toss-dark'>{(win/(win+lose)*100 if win+lose>0 else 0):.1f}% (익절 {win} / 손절 {lose})</span></div>
                    <div><span class='toss-gray'>평균 보유일</span><br><span class='toss-dark'>{np.mean(hold_periods) if hold_periods else 0:.0f}일</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='toss-dark' style='margin:20px 0 10px 5px;'>상세 거래 내역</div>", unsafe_allow_html=True)
            l_box = "<div style='background:white; border:1px solid #e5e8eb; border-radius:20px; height:450px; overflow-y:auto; padding:0 20px;'>"
            for l in sorted(logs, key=lambda x: x['date'], reverse=True):
                l_box += f"""
                <div style='padding:20px 0; border-bottom:1px solid #f2f4f6; display:flex; align-items:center;'>
                    <div style='font-size:26px; margin-right:16px;'>{l['icon']}</div>
                    <div style='flex-grow:1;'>
                        <div style='display:flex; justify-content:space-between;'><span style='font-weight:700; color:#191f28; font-size:16px;'>{l['title']}</span><span style='color:{l['color']}; font-weight:700; font-size:16px;'>{l['desc']}</span></div>
                        <div style='display:flex; justify-content:space-between; font-size:13px; color:#8b95a1; margin-top:4px;'><span>{l['date']}</span><span>내 자산 {l['asset']/10000:,.0f}만원</span></div>
                    </div>
                </div>"""
            st.markdown(l_box + "</div>", unsafe_allow_html=True)