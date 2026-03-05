import streamlit as st
import pandas as pd
import re

# --- [고정 규칙 1 & 2] 타이틀 설정 ---
st.set_page_config(page_title="베어링 항공운임 스마트 계산기", page_icon="✈️")

st.markdown("""
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">✈️ 베어링 항공운임 스마트 계산기</h1>
        <span style="font-size: 0.9em; color: gray;">Ver 5.6</span>
    </div>
""", unsafe_allow_html=True)

# --- [고정 규칙 3] 항공 운임 기본 계산 방법 안내 ---
st.info("💡 **항공 운임 계산 가이드**")
st.markdown("""
* **실제 중량(Actual Weight):** 화물 + 포장재의 실제 무게 (kg)
* **부피 중량(Volume Weight):** 가로(cm) × 세로(cm) × 높이(cm) ÷ 6,000
* **운임 적용 중량:** 실제 중량과 부피 중량 중 **더 큰 값**을 기준으로 요금이 책정됩니다.
""")

st.divider()

# --- 1. 베어링 규격 조회 섹션 ---
st.subheader("🔍 베어링 규격 통합 조회")

@st.cache_data
def load_data():
    # 파일명은 업로드된 실제 파일명에 맞춰 설정
    file_path = "bearing_list.xlsx - Sheet1.csv"
    try:
        df = pd.read_csv(file_path)
        # 컬럼명 정리 (공백 제거 등)
        df.columns = [col.strip() for col in df.columns]
        return df
    except:
        try:
            # 엑셀 원본 파일명 시도
            df = pd.read_excel("bearing_list.xlsx")
            df.columns = [col.strip() for col in df.columns]
            return df
        except:
            return pd.DataFrame()

df = load_data()

# 검색어 입력창
raw_query = st.text_input("조회할 형번을 입력하세요 (예: 1204C3, 30311J 등)", "").strip().upper()

# --- 안내 문구 최소화 적용 (폰트 크기 0.7em) ---
st.markdown("<p style='color: #999; font-size: 0.7em; margin-top: -15px; margin-left: 2px;'>※ NSK 일반 규격 시리즈를 기준으로 검색 가능하며, 추후 추가 예정입니다.</p>", unsafe_allow_html=True)

if raw_query:
    if not df.empty:
        # 정규표현식: 입력어에서 숫자 덩어리만 추출하여 유연하게 매칭
        match = re.search(r'\d+', raw_query)
        if match:
            core_num = match.group()
            # '모델명(Model)' 컬럼에서 숫자 포함 여부 확인
            res = df[df['모델명(Model)'].astype(str).str.contains(core_num, na=False)]
            
            if not res.empty:
                st.write(f"✅ **'{core_num}'** 관련 규격 검색 결과입니다.")
                st.table(res)
            else:
                st.warning(f"'{core_num}' 관련 데이터를 찾을 수 없습니다.")
        else:
            # 숫자가 없는 검색어는 전체 텍스트 매칭
            res = df[df['모델명(Model)'].astype(str).str.contains(raw_query, na=False)]
            if not res.empty:
                st.table(res)
    else:
        st.error("데이터 파일을 로드할 수 없습니다. 파일명을 확인해 주세요.")

st.divider()

# --- 2. 선적 단위별 운임 계산 섹션 ---
st.subheader("📦 선적 단위별 운임 계산")

mode = st.radio("포장 형태를 선택하세요", ["종이박스", "팔레트(Pallet)", "수기 입력"], horizontal=True)

col1, col2 = st.columns([1, 1.2])
total_a_w, total_v_w = 0.0, 0.0

with col1:
    st.markdown("#### 🛠️ 세부 설정")
    
    if mode == "종이박스":
        st.write("**기본 박스 규격:** 245 x 275 x 150 mm")
        # mm -> cm 변환
        l_cm, w_cm, h_cm = 24.5, 27.5, 15.0
        
        box_qty = st.number_input("박스 수량(pcs)", min_value=1, value=1)
        content_w = st.number_input("박스당 내용물 무게(kg)", min_value=0.0, value=10.0)
        box_tare = st.number_input("박스 자체 무게(kg)", min_value=0.0, value=0.5)
        
        total_a_w = (content_w + box_tare) * box_qty
        total_v_w = ((l_cm * w_cm * h_cm) / 6000) * box_qty

    elif mode == "팔레트(Pallet)":
        p_choice = st.selectbox("팔레트 규격 선택 (mm)", ["800 x 600", "900 x 900", "1050 x 950", "1200 x 800"])
        # 규격 분리 및 cm 변환
        p_l_mm, p_w_mm = map(float, p_choice.split(" x "))
        p_l_cm, p_w_cm = p_l_mm / 10, p_w_mm / 10
        
        p_height_mm = st.number_input("적재 높이(mm)", min_value=100, value=1000, step=50)
        p_height_cm = p_height_mm / 10
        
        p_content_w = st.number_input("적재물 총 무게(kg)", min_value=0.0, value=200.0)
        p_tare = st.number_input("팔레트 자체 무게(kg)", min_value=0.0, value=15.0)
        
        total_a_w = p_content_w + p_tare
        total_v_w = (p_l_cm * p_w_cm * p_height_cm) / 6000

    elif mode == "수기 입력":
        pack_type = st.selectbox("포장재 유형 선택", ["없음 (0kg)", "종이박스 (0.5kg)", "팔레트 (15kg)"])
        # 포장재에 따른 기본 무게 설정
        tare_val = 0.5 if "종이박스" in pack_type else 15.0 if "팔레트" in pack_type else 0.0
        
        c_l = st.number_input("가로(mm)", min_value=0, value=250)
        c_w = st.number_input("세로(mm)", min_value=0, value=250)
        c_h = st.number_input("높이(mm)", min_value=0, value=250)
        c_qty = st.number_input("총 수량(pcs)", min_value=1, value=1)
        c_weight = st.number_input("내용물 무게(kg/개)", min_value=0.0, value=10.0)
        c_tare = st.number_input("포장재 무게(kg/개)", value=tare_val)
        
        total_a_w = (c_weight + c_tare) * c_qty
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
    
    if total_v_w > total_a_w:
        st.caption("💡 부피 중량이 더 커서 부피 기준으로 운임이 책정되었습니다.")
    else:
        st.caption("💡 실제 중량이 더 커서 무게 기준으로 운임이 책정되었습니다.")