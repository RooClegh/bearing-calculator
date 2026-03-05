import streamlit as st
import pandas as pd
import re

# --- [고정 규칙 1 & 2] 타이틀 설정 ---
st.set_page_config(page_title="베어링 항공운임 스마트 계산기", page_icon="✈️")

st.markdown("""
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">✈️ 베어링 항공운임 스마트 계산기</h1>
        <span style="font-size: 0.9em; color: gray;">Ver 5.0</span>
    </div>
""", unsafe_allow_html=True)

# --- [고정 규칙 3] 항공 운임 기본 계산 방법 안내 ---
st.info("💡 **항공 운임 계산 가이드**")
st.markdown("""
* **실제 중량(A.W):** 화물 + 포장재의 실제 무게 (kg)
* **부피 중량(V.W):** 가로(cm) × 세로(cm) × 높이(cm) ÷ 6,000
* **운임 적용 중량:** 실제 중량과 부피 중량 중 **더 큰 값**을 기준으로 요금이 책정됩니다.
""")

st.divider()

# --- 1. 베어링 규격 조회 섹션 (참고용) ---
st.subheader("🔍 베어링 형번 규격 조회 (참고용)")

# (기존 데이터 로드 로직 포함)
@st.cache_data
def load_data():
    try:
        return pd.read_excel("bearing_list.xlsx")
    except:
        return pd.DataFrame()

df = load_data()

search_query = st.text_input("참고할 형번을 입력하세요 (예: 22214)", "").strip().upper()
if search_query and not df.empty:
    # 간단 매칭 로직
    mask = df['model'].str.contains(search_query, na=False)
    res = df[mask]
    if not res.empty:
        st.dataframe(res[['model', 'maker', 'weight_kg', 'length_mm', 'width_mm', 'height_mm']], hide_index=True)
    else:
        st.caption("일치하는 형번 데이터가 없습니다.")

st.divider()

# --- 2. 선적 단위별 운임 계산 섹션 ---
st.subheader("📦 선적 단위별 운임 계산")

# 선적 모드 선택 (종이박스, 파렛트, 직접 입력)
mode = st.radio("포장 형태를 선택하세요", ["종이박스", "팔레트(Pallet)", "수기 입력"], horizontal=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("#### 🛠️ 세부 설정")
    
    if mode == "종이박스":
        # 1. 종이박스 기본 사이즈 지정 (245*275*150)
        st.write("**기본 박스 규격:** 245 x 275 x 150 mm")
        l, w, h = 24.5, 27.5, 15.0 # cm 변환
        
        box_qty = st.number_input("박스 수량(pcs)", min_value=1, value=1)
        content_w = st.number_input("박스당 내용물 무게(kg)", min_value=0.0, value=10.0)
        # 4. 박스 자체 무게 추가
        box_tare = st.number_input("박스 자체 무게(kg)", min_value=0.0, value=0.5, step=0.1)
        
        total_a_w = (content_w + box_tare) * box_qty
        total_v_w = (l * w * h / 6) * box_qty

  elif mode == "팔레트(Pallet)":
        p_choice = st.selectbox("팔레트 규격 선택 (mm)", [
            "800 x 600", 
            "900 x 900", 
            "1050 x 950", 
            "1200 x 800"
        ])
        # 1. 규격 파싱 및 mm -> cm 변환
        p_l_mm, p_w_mm = map(float, p_choice.split(" x "))
        p_l_cm, p_w_cm = p_l_mm / 10, p_w_mm / 10
        
        p_height_mm = st.number_input("적재 높이(mm)", min_value=100, value=1000, step=50)
        p_height_cm = p_height_mm / 10
        
        p_content_w = st.number_input("적재물 총 무게(kg)", min_value=0.0, value=10.0)
        p_tare = st.number_input("팔레트 자체 무게(kg)", min_value=0.0, value=15.0)
        
        # 실제 중량: 물건 + 팔레트
        total_a_w = p_content_w + p_tare
        # 부피 중량: (L * W * H) / 6000 (cm 기준)
        total_v_w = (p_l_cm * p_w_cm * p_height_cm) / 6

    elif mode == "수기 입력":
        st.markdown("##### ✏️ 커스텀 규격 입력")
        
        # 1. 수기 입력 시에도 포장재 유형 선택
        manual_packaging = st.selectbox("추가할 포장재 무게", ["없음 (0kg)", "종이박스 (0.5kg)", "팔레트 (15kg)"])
        
        # 선택에 따른 기본 무게 설정
        if "종이박스" in manual_packaging:
            default_tare = 0.5
        elif "팔레트" in manual_packaging:
            default_tare = 15.0
        else:
            default_tare = 0.0
            
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            c_l = st.number_input("가로(mm)", min_value=0, value=250)
            c_w = st.number_input("세로(mm)", min_value=0, value=250)
            c_h = st.number_input("높이(mm)", min_value=0, value=250)
        with col_m2:
            c_qty = st.number_input("총 수량(pcs)", min_value=1, value=1)
            c_content_w = st.number_input("내용물 순수 무게(kg/개)", min_value=0.0, value=10.0)
            c_tare_w = st.number_input("선택 포장재 무게(kg/개)", value=default_tare)

        # 최종 계산 (실제 중량 = (내용물 + 포장재) * 수량)
        total_a_w = (c_content_w + c_tare_w) * c_qty
        total_v_w = (c_l/10 * c_w/10 * c_h/10 / 6) * c_qty

with col2:
    st.markdown("#### 💰 운임 계산 결과")
    rate = st.number_input("항공 요율 (원/kg)", min_value=0, value=5500, step=100)
    
    chargeable_weight = max(total_a_w, total_v_w)
    total_cost = chargeable_weight * rate
    
    # 결과 요약 카드
    st.info(f"**실제 총 중량(Actual):** {total_a_w:.2f} kg")
    st.info(f"**부피 총 중량(Volume):** {total_v_w:.2f} kg")
    
    st.success(f"### 적용 중량: {chargeable_weight:.2f} kg")
    st.warning(f"### 예상 운임: {int(total_cost):,} 원")
    
    if total_v_w > total_a_w:
        st.caption("💡 부피 중량이 더 커서 부피 기준으로 운임이 책정되었습니다.")
    else:
        st.caption("💡 실제 중량이 더 커서 무게 기준으로 운임이 책정되었습니다.")