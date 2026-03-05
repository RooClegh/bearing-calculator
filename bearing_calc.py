import streamlit as st
import pandas as pd

# --- [고정 규칙 1 & 2] 타이틀 설정 ---
st.set_page_config(page_title="베어링 항공운임 스마트 계산기", page_icon="✈️")

st.markdown("""
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">✈️ 베어링 항공운임 스마트 계산기</h1>
        <span style="font-size: 0.9em; color: gray;">Ver 5.1</span>
    </div>
""", unsafe_allow_html=True)

# --- [고정 규칙 3] 항공 운임 기본 계산 방법 안내 ---
st.info("💡 **항공 운임 계산 가이드**")
st.markdown("""
* **실제 중량(A.W):** 화물 + 포장재의 실제 무게 (kg)
* **부피 중량(V.W):** 가로(cm) × 세로(cm) × 높이(cm) ÷ 6,000
* **운임 적용 중량:** 실제 중량과 부피 중량 중 **더 큰 값** 기준
""")

st.divider()

# --- 1. 베어링 규격 조회 섹션 (참고용) ---
st.subheader("🔍 베어링 형번 규격 조회 (참고용)")

@st.cache_data
def load_data():
    try:
        return pd.read_excel("bearing_list.xlsx")
    except:
        return pd.DataFrame()

df = load_data()

search_query = st.text_input("참고할 형번을 입력하세요", "").strip().upper()
if search_query and not df.empty:
    mask = df['model'].str.contains(search_query, na=False)
    res = df[mask]
    if not res.empty:
        st.dataframe(res[['model', 'maker', 'weight_kg', 'length_mm', 'width_mm', 'height_mm']], hide_index=True)

st.divider()

# --- 2. 선적 단위별 운임 계산 섹션 ---
st.subheader("📦 선적 단위별 운임 계산")

mode = st.radio("포장 형태를 선택하세요", ["종이박스", "팔레트(Pallet)", "수기 입력"], horizontal=True)

col1, col2 = st.columns([1, 1.2])

total_a_w = 0.0
total_v_w = 0.0

with col1:
    st.markdown("#### 🛠️ 세부 설정")
    
    if mode == "종이박스":
        st.write("**기본 박스 규격:** 245 x 275 x 150 mm")
        # mm 단위를 그대로 곱하고 마지막에 6,000,000으로 나누거나, cm로 변환 후 6,000으로 나눕니다.
        l_cm, w_cm, h_cm = 24.5, 27.5, 15.0
        
        box_qty = st.number_input("박스 수량(pcs)", min_value=1, value=1)
        content_w = st.number_input("박스당 내용물 무게(kg)", min_value=0.0, value=10.0)
        box_tare = st.number_input("박스 자체 무게(kg)", min_value=0.0, value=0.5)
        
        total_a_w = (content_w + box_tare) * box_qty
        # 표준 공식 적용: (L*W*H)/6000
        total_v_w = ((l_cm * w_cm * h_cm) / 6000) * box_qty

    elif mode == "팔레트(Pallet)":
        p_choice = st.selectbox("팔레트 규격 선택 (mm)", ["800 x 600", "900 x 900", "1050 x 950", "1200 x 800"])
        p_l_mm, p_w_mm = map(float, p_choice.split(" x "))
        p_l_cm, p_w_cm = p_l_mm / 10, p_w_mm / 10
        
        p_height_mm = st.number_input("적재 높이(mm)", min_value=100, value=1000)
        p_height_cm = p_height_mm / 10
        
        p_content_w = st.number_input("적재물 총 무게(kg)", min_value=0.0, value=200.0)
        p_tare = st.number_input("팔레트 자체 무게(kg)", min_value=0.0, value=15.0)
        
        total_a_w = p_content_w + p_tare
        # 표준 공식 적용
        total_v_w = (p_l_cm * p_w_cm * p_height_cm) / 6000

    elif mode == "수기 입력":
        manual_packaging = st.selectbox("포장재 유형", ["없음 (0kg)", "종이박스 (0.5kg)", "팔레트 (15kg)"])
        default_tare = 0.5 if "종이박스" in manual_packaging else 15.0 if "팔레트" in manual_packaging else 0.0
            
        c_l = st.number_input("가로(mm)", min_value=0, value=250)
        c_w = st.number_input("세로(mm)", min_value=0, value=250)
        c_h = st.number_input("높이(mm)", min_value=0, value=250)
        c_qty = st.number_input("총 수량(pcs)", min_value=1, value=1)
        c_content_w = st.number_input("내용물 무게(kg/개)", min_value=0.0, value=10.0)
        c_tare_w = st.number_input("포장재 무게(kg/개)", value=default_tare)

        total_a_w = (c_content_w + c_tare_w) * c_qty
        # 표준 공식 적용 (mm -> cm 변환 후 6000으로 나누기)
        total_v_w = ((c_l/10 * c_w/10 * c_h/10) / 6000) * c_qty

with col2:
    st.markdown("#### 💰 운임 계산 결과")
    rate = st.number_input("항공 요율 (원/kg)", min_value=0, value=5500)
    
    chargeable_weight = max(total_a_w, total_v_w)
    total_cost = chargeable_weight * rate
    
    st.info(f"**실제 총 중량(Actual):** {total_a_w:.2f} kg")
    st.info(f"**부피 총 중량(Volume):** {total_v_w:.2f} kg")
    st.success(f"### 적용 중량: {chargeable_weight:.2f} kg")
    st.warning(f"### 예상 운임: {int(total_cost):,} 원")