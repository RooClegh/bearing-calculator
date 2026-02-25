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
st.title("🚢 베어링 항공 운임 스마트 계산기 (Ver 2.5)")

with st.expander("📝 항공 운임 계산 공식 확인하기"):
    st.write("""
    1. **실무게(Actual Weight):** (개당 무게 × 수량) + 포장재 무게
    2. **부피무게(Volume Weight):** (가로cm × 세로cm × 높이cm) ÷ 6,000
    3. **청구무게(Chargeable Weight):** 실무게와 부피무게 중 큰 값 적용
    """)

st.info("💡 본 계산기는 **동명베아링 표준 박스 및 팔레트 규격**이 반영된 예상치입니다.")

st.sidebar.markdown("### 📍 도착지 정보")
st.sidebar.info("**동명베아링**\n\n부산광역시 사상구 새벽로215번길 123")

# --- 검색 섹션 ---
st.header("🔍 1. 베어링 규격 검색")
init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0

if df is not None:
    search_query = st.text_input("검색할 형번을 입력하세요", "").strip()
    if search_query:
        mask = (df['base_model'].str.contains(search_query, case=False, na=False)) | \
               (df['model'].str.contains(search_query, case=False, na=False))
        filtered_df = df[mask]
        if not filtered_df.empty:
            selection_list = filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1).tolist()
            selected_item = st.selectbox("정확한 모델을 선택하세요", selection_list)
            row = filtered_df[filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1) == selected_item].iloc[0]
            init_l, init_w, init_h, init_weight = float(row['length_mm']), float(row['width_mm']), float(row['height_mm']), float(row['weight_kg'])
            st.success(f"✅ {selected_item} 로드 완료")
else:
    st.error("⚠️ 엑셀 파일을 읽을 수 없습니다.")

st.divider()

# --- 입력 및 포장 섹션 ---
st.header("📦 2. 정보 확인 및 포장 선택")
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ 기본 정보")
    qty = st.number_input("총 수량 (EA)", min_value=1, value=100)
    b_weight = st.number_input("개당 무게 (kg)", min_value=0.01, value=init_weight, format="%.2f")

with col2:
    st.subheader("🎁 포장 옵션")
    p_type = st.selectbox("포장 종류 선택", [
        "단품 (포장 없음)", 
        "표준 종이 박스 (245*275*150)", 
        "팔레트 (800*600) - 기본", 
        "팔레트 (900*900)", 
        "팔레트 (1050*950)", 
        "팔레트 (1200*800) - 인도 수출용"
    ])

    # 포장별 규격 및 추가 무게 설정
    p_l, p_w, p_h, p_added_w = init_l, init_w, init_h, 0.0
    
    if "종이 박스" in p_type:
        p_l, p_w, p_h, p_added_w = 245, 275, 150, 0.5
    elif "팔레트" in p_type:
        dims = p_type.split("(")[1].split(")")[0].split("*")
        p_l, p_w = float(dims[0]), float(dims[1])
        p_h = st.number_input("팔레트 적재 높이 (mm)", min_value=100, value=500, step=50)
        p_added_w = 20.0 # 팔레트 자체 무게 대략 20kg 가정

# --- 계산 로직 ---
total_actual_weight = (b_weight * qty) + p_added_w
# 부피 무게 계산 (cm 단위로 변환)
total_volume_weight = (p_l/10 * p_w/10 * p_h/10) / 6000
# 만약 단품이거나 박스라면 수량을 곱해줘야 함 (팔레트는 전체가 하나의 덩어리이므로 수량 안 곱함)
if "팔레트" not in p_type:
    total_volume_weight *= qty

chargeable_weight = max(total_actual_weight, total_volume_weight)

# --- 결과 출력 ---
st.divider()
st.header("💰 3. 최종 예상 운임")
u_price = st.number_input("kg당 운임 ($)", min_value=0.0, value=5.0)
e_rate = st.number_input("적용 환율 (원/$)", min_value=1.0, value=realtime_rate)

res1, res2, res3 = st.columns(3)
res1.metric("청구 무게 (C.W)", f"{chargeable_weight:.2f} kg")
res2.metric("예상 운임 (USD)", f"$ {chargeable_weight * u_price:,.2f}")
res3.metric("예상 운임 (KRW)", f"{int(chargeable_weight * u_price * e_rate):,} 원")