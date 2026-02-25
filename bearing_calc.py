import streamlit as st
import pandas as pd
import requests

# 1. 실시간 환율 가져오기 함수 (통화 코드 추가)
def get_exchange_rate(target_currency="USD"):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{target_currency}"
        response = requests.get(url)
        data = response.json()
        return data['rates']['KRW']
    except:
        # 에러 발생 시 기본값 (현재 기준 대략적 수치)
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
df = load_data()

# --- 타이틀 및 안내 섹션 ---
st.title("🚢 베어링 항공 운임 스마트 계산기 (Ver 3.2)")
st.info("💡 국가를 선택하면 해당 국가의 통화 환율과 표준 운임 단가가 자동으로 로드됩니다.")

# 사이드바: 회사 정보
st.sidebar.markdown("### 📍 도착지 정보")
st.sidebar.info("**동명베아링**\n\n부산광역시 사상구 새벽로215번길 123")

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

# --- 3. 국가 선택 및 환율/단가 자동화 ---
st.header("🌐 3. 수입 국가 및 운임 설정")
col_rate1, col_rate2 = st.columns(2)

# 국가별 정보 설정: {국가명: (표준단가$, 통화코드)}
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
    
    # 국가 선택에 따른 실시간 환율 가져오기
    current_rate = get_exchange_rate(currency_code)

with col_rate2:
    u_price = st.number_input(f"kg당 운임 ($) - {selected_country}", min_value=0.0, value=default_unit_price, step=0.1)
    # 일본의 경우 엔화 환율은 보통 100엔 기준이므로 화면 표시를 조정
    rate_label = f"적용 환율 (원/{currency_code})"
    e_rate = st.number_input(rate_label, min_value=0.1, value=current_rate, format="%.2f")

# --- 계산 로직 ---
total_actual_weight = (b_weight * bearing_qty) + (p_added_w * p_qty)
total_volume_weight = (p_l/10 * p_w/10 * p_h/10 * p_qty) / 6000
chargeable_weight = max(total_actual_weight, total_volume_weight)

# 최종 금액 계산
# 만약 일본(JPY)이라면 단가($)를 환산하는 방식에 따라 로직이 달라질 수 있지만, 
# 여기서는 사용자가 입력한 $ 단가에 해당 국가 환율을 곱하는 것으로 설정했습니다.
final_usd = chargeable_weight * u_price
final_krw = final_usd * e_rate

# --- 결과 출력 ---
st.divider()
st.header("💰 4. 최종 예상 운임 결과")
res1, res2, res3 = st.columns(3)
res1.metric("청구 무게 (C.W)", f"{chargeable_weight:.2f} kg")
res2.metric("예상 운임 (USD)", f"$ {final_usd:,.2f}")
res3.metric(f"예상 운임 (KRW)", f"{int(final_krw):,} 원")