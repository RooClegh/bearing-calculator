import streamlit as st
import pandas as pd
import requests

# 1. 실시간 환율 가져오기 함수
def get_exchange_rate(target_currency="USD"):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{target_currency}"
        response = requests.get(url)
        data = response.json()
        return data['rates']['KRW']
    except:
        defaults = {"USD": 1450.0, "JPY": 9.5, "EUR": 1550.0, "CNY": 200.0}
        return defaults.get(target_currency, 1450.0)

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    file_name = "bearing_list.xlsx"
    try:
        df = pd.read_excel(file_name)
    except Exception:
        try:
            df = pd.read_csv(file_name)
        except Exception:
            return None
    for col in ['base_model', 'model', 'maker']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

st.set_page_config(page_title="동명베아링 운임 계산기", layout="wide")

# 기본 USD 환율 로드
usd_rate = get_exchange_rate("USD")
df = load_data()

# --- [고정 규칙 1 & 2] 타이틀 및 버전 표기 ---
# st.title 대신 마크다운을 사용하여 버전 정보를 우측에 작게 배치합니다.
st.markdown("## ✈️ 베어링 항공 운임 스마트 계산기 <small style='font-size: 15px; color: gray;'>Ver 3.4</small>", unsafe_allow_html=True)

st.info("💡 모든 운임은 **USD($)** 기준으로 계산되며, 국가별 환율은 참고 정보로 제공됩니다.")

# 사이드바: 회사 정보
st.sidebar.markdown("### 📍 도착지 정보")
st.sidebar.info("**동명베아링**\n\n부산광역시 사상구 새벽로215번길 123")

# --- [고정 규칙 3] 기본적인 항공료 계산법 기재 ---
st.markdown("### 📋 기본적인 항공료 계산법")
st.caption("""
1. **실무게(Actual Weight):** (개당 무게 × 수량) + 포장재 무게  
2. **부피무게(Volume Weight):** (가로cm × 세로cm × 높이cm × 포장개수) ÷ 6,000  
3. **청구무게(Chargeable Weight):** 실무게와 부피무게 중 큰 값 적용  
4. **최종운임:** 청구무게(C.W) × kg당 단가($) × 적용 환율(₩)
""")

st.divider()

# --- 1. 검색 섹션 ---
st.header("🔍 1. 베어링 규격 검색")
init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0

if df is not None:
    search_query = st.text_input("검색할 형번을 입력하세요 (예: 22214)", "").strip()
    if search_query:
        mask = (df['base_model'].str.contains(search_query, case=False, na=False)) | \
               (df['model'].str.contains(search_query, case=False, na=False))
        filtered_df = df[mask]
        if not filtered_df.empty:
            selection_list = filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1).tolist()
            selected_item = st.selectbox("정확한 모델을 선택하세요", selection_list)
            row = filtered_df[filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1) == selected_item].iloc[0]
            init_l, init_w, init_h, init_weight = float(row['length_mm']), float(row['width_mm']), float(row['height_mm']), float(row['weight_kg'])
            st.success(f"✅ {selected_item} 데이터 로드 완료")
else:
    st.error("⚠️ 엑셀 파일을 읽을 수 없습니다.")

st.divider()

# --- 2. 정보 확인 및 포장 선택 ---
st.header("📦 2. 정보 확인 및 포장 선택")
col_input1, col_input2 = st.columns(2)

with col_input1:
    st.subheader("⚙️ 상품 정보")
    bearing_qty = st.number_input("베어링 총 수량 (EA)", min_value=1, value=100)
    b_weight = st.number_input("베어링 개당 무게 (kg)", min_value=0.01, value=init_weight, format="%.2f")

with col_input2:
    st.subheader("🎁 포장 정보")
    p_type = st.selectbox("포장 종류 선택", [
        "단품 (포장 없음)", 
        "표준 종이 박스 (245*275*150)", 
        "팔레트 (800*600) - 기본", 
        "팔레트 (900*900)", 
        "팔레트 (1050*950)", 
        "팔레트 (1200*800) - 인도 수출용"
    ])
    
    unit_label = "포장 총 개수"
    if "팔레트" in p_type:
        unit_label = "팔레트 총 개수 (PLT)"
    elif "박스" in p_type:
        unit_label = "박스 총 개수 (CTN)"
    
    p_qty = st.number_input(f"{unit_label}", min_value=1, value=1)

    p_l, p_w, p_h, p_added_w = init_l, init_w, init_h, 0.0
    if "종이 박스" in p_type:
        p_l, p_w, p_h, p_added_w = 245, 275, 150, 0.5
    elif "팔레트" in p_type:
        dims = p_type.split("(")[1].split(")")[0].split("*")
        p_l, p_w = float(dims[0]), float(dims[1])
        p_h = st.number_input("적재 높이 (mm)", min_value=100, value=500, step=50)
        p_added_w = 20.0

st.divider()

# --- 3. 국가 선택 및 환율/단가 설정 ---
st.header("🌐 3. 수입 국가 및 운임 설정")
col_rate1, col_rate2 = st.columns(2)

country_info = {
    "미국 🇺🇸": (5.5, "USD"),
    "일본 🇯🇵": (2.5, "JPY"),
    "독일 🇩🇪": (4.5, "EUR"),
    "중국 🇨🇳": (1.5, "CNY"),
    "직접 입력": (0.0, "USD")
}

with col_rate1:
    selected_country = st.selectbox("출발 국가를 선택하세요", list(country_info.keys()))
    default_unit_price, currency_code = country_info[selected_country]
    
    ref_rate = get_exchange_rate(currency_code)
    st.caption(f"📢 참고: 현재 {selected_country} 실시간 환율은 1 {currency_code} = {ref_rate:,.2f}원 입니다.")

with col_rate2:
    u_price = st.number_input(f"kg당 운임 ($) - {selected_country}", min_value=0.0, value=default_unit_price, step=0.1)
    e_rate = st.number_input("계산 적용 환율 (원/USD)", min_value=1.0, value=usd_rate, format="%.2f")

# --- 계산 로직 ---
total_actual_weight = (b_weight * bearing_qty) + (p_added_w * p_qty)
total_volume_weight = (p_l/10 * p_w/10 * p_h/10 * p_qty) / 6000
chargeable_weight = max(total_actual_weight, total_volume_weight)

final_usd = chargeable_weight * u_price
final_krw = final_usd * e_rate

# --- 결과 출력 ---
st.divider()
st.header("💰 4. 최종 예상 운임 결과")
res1, res2, res3 = st.columns(3)
res1.metric("청구 무게 (C.W)", f"{chargeable_weight:.2f} kg")
res2.metric("예상 운임 (USD)", f"$ {final_usd:,.2f}")
res3.metric("예상 운임 (KRW)", f"{int(final_krw):,} 원")