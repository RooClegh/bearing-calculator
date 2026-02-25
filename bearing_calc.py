import streamlit as st
import pandas as pd
import requests

# 1. 환율 가져오기 함수
def get_realtime_usd():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        data = response.json()
        return data['rates']['KRW']
    except:
        return 1450.0

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

st.set_page_config(page_title="항공 운임 계산기", layout="wide")
realtime_rate = get_realtime_usd()
df = load_data()

# --- 타이틀 및 안내 섹션 ---
st.title("🚢 베어링 항공 운임 스마트 계산기 (Ver 3.0)")

with st.expander("📝 항공 운임 계산 공식 확인하기"):
    st.write("""
    1. **실무게(Actual Weight):** (개당 무게 × 수량) + 포장재 무게
    2. **부피무게(Volume Weight):** (가로cm × 세로cm × 높이cm) ÷ 6,000
    3. **청구무게(Chargeable Weight):** 실무게와 부피무게 중 큰 값 적용
    """)

st.info("💡 국가를 선택하면 표준 단가가 자동으로 입력됩니다. 실제 견적에 따라 수정이 가능합니다.")

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

# --- 2. 입력 및 포장 섹션 ---
st.header("📦 2. 정보 확인 및 포장 선택")
col_input1, col_input2 = st.columns(2)

with col_input1:
    st.subheader("⚙️ 기본 정보")
    qty = st.number_input("총 수량 (EA)", min_value=1, value=100)
    b_weight = st.number_input("개당 무게 (kg)", min_value=0.01, value=init_weight, format="%.2f")

with col_input2:
    st.subheader("🎁 포장 옵션")
    p_type = st.selectbox("포장 종류 선택", [
        "단품 (포장 없음)", 
        "표준 종이 박스 (245*275*150)", 
        "팔레트 (800*600) - 기본", 
        "팔레트 (900*900)", 
        "팔레트 (1050*950)", 
        "팔레트 (1200*800) - 인도 수출용"
    ])
    
    p_l, p_w, p_h, p_added_w = init_l, init_w, init_h, 0.0
    if "종이 박스" in p_type:
        p_l, p_w, p_h, p_added_w = 245, 275, 150, 0.5
    elif "팔레트" in p_type:
        dims = p_type.split("(")[1].split(")")[0].split("*")
        p_l, p_w = float(dims[0]), float(dims[1])
        p_h = st.number_input("팔레트 적재 높이 (mm)", min_value=100, value=500, step=50)
        p_added_w = 20.0

st.divider()

# --- 3. 국가 선택 및 단가 섹션 ---
st.header("🌐 3. 수입 국가 및 운임 설정")
col_rate1, col_rate2 = st.columns(2)

# 국가별 표준 단가 설정 (딕셔너리)
country_rates = {
    "일본 🇯🇵": 2.5,
    "미국 🇺🇸": 5.5,
    "독일 🇩🇪": 4.5,
    "중국 🇨🇳": 1.5,
    "직접 입력": 0.0
}

with col_rate1:
    selected_country = st.selectbox("출발 국가를 선택하세요", list(country_rates.keys()))
    # 선택된 국가에 맞는 기본 단가 가져오기
    default_unit_price = country_rates[selected_country]

with col_rate2:
    # 국가를 바꾸면 value가 자동으로 변경됨
    u_price = st.number_input(f"kg당 운임 ($) - {selected_country} 기준", min_value=0.0, value=default_unit_price, step=0.1)
    e_rate = st.number_input("적용 환율 (원/$)", min_value=1.0, value=realtime_rate)

# --- 계산 로직 ---
total_actual_weight = (b_weight * qty) + p_added_w
total_volume_weight = (p_l/10 * p_w/10 * p_h/10) / 6000
if "팔레트" not in p_type:
    total_volume_weight *= qty

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