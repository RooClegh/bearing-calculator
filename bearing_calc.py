import streamlit as st
import pandas as pd
import re

# --- [고정 규칙 1 & 2] 타이틀 설정 ---
st.set_page_config(page_title="베어링 항공운임 스마트 계산기", page_icon="✈️")

st.markdown("""
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">✈️ 베어링 항공운임 스마트 계산기</h1>
        <span style="font-size: 0.9em; color: gray;">Ver 4.2</span>
    </div>
""", unsafe_allow_html=True)

# --- [고정 규칙 3] 항공 운임 기본 계산 방법 안내 ---
st.info("💡 **항공 운임 계산 가이드**")
st.markdown("""
* **실제 중량(A.W):** 화물의 실제 무게 (kg)
* **부피 중량(V.W):** 가로(cm) × 세로(cm) × 높이(cm) ÷ 6,000
* **운임 적용 중량:** 실제 중량과 부피 중량 중 **더 큰 값** 기준
""")

st.divider()

# --- 지능형 매칭 함수 (엑셀의 공백 및 특수 형식 완벽 대응) ---
def smart_match_logic(search_query, row_model):
    # 엑셀 데이터의 불필요한 공백 제거 (캡처의 *H* 5 같은 부분 대응)
    s_q = str(search_query).strip().upper()
    r_m = str(row_model).strip().upper()
    r_m = " ".join(r_m.split()) # 중간의 여러 공백을 하나로 합침
    
    def extract_num(text):
        main = text.split('-')[0]
        # 숫자만 추출
        nums = "".join(re.findall(r'\d+', main))
        return nums
    
    s_num = extract_num(s_q)
    r_num = extract_num(r_m)

    # 1. 90000번대 ASSY 모델 특수 매칭
    if '-9' in s_q or '-9' in r_m:
        return s_q in r_m or r_m in s_q
    
    # 2. 일반 모델: 숫자가 포함된 경우 숫자 기반 매칭
    if s_num and r_num:
        return s_num == r_num
    
    # 3. 숫자가 없는 경우 문자열 포함 여부로 결정
    return s_q in r_m

# --- 데이터 로드 ---
@st.cache_data
def load_data():
    try:
        # 파일명이 다르면 여기만 수정하세요!
        return pd.read_excel("bearing_list.xlsx")
    except Exception as e:
        st.error(f"엑셀 파일을 불러올 수 없습니다. 파일명을 확인해 주세요: {e}")
        return pd.DataFrame()

df = load_data()

# --- 메인 UI ---
if not df.empty:
    st.subheader("🔍 베어링 규격 검색")
    search_query = st.text_input("형번을 입력하세요 (예: 22214, HM266449-90158)", "").strip().upper()

    if search_query:
        # 매칭 수행
        mask = df['model'].apply(lambda x: smart_match_logic(search_query, x))
        filtered_df = df[mask]

        if not filtered_df.empty:
            # 엑셀의 model 컬럼을 리스트로 보여줌
            choices = filtered_df['model'].unique().tolist()
            selected_model = st.selectbox("정확한 모델을 선택하세요:", choices)
            
            # 선택된 데이터 상세 정보 추출
            spec = filtered_df[filtered_df['model'] == selected_model].iloc[0]
            
            st.write(f"### 📋 {selected_model} 상세 정보")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("제조사", spec['maker'])
            with c2: st.metric("개당 중량", f"{spec['weight_kg']} kg")
            with c3: st.metric("박스(L/W)", f"{int(spec['length_mm'])}x{int(spec['width_mm'])} mm")
            with c4: st.metric("박스 높이", f"{int(spec['height_mm'])} mm")

            # --- 항공 운임 계산기 ---
            st.divider()
            st.subheader("💰 항공 운임 시뮬레이션")
            
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                qty = st.number_input("주문 수량(pcs)", min_value=1, value=1)
            with col_in2:
                rate = st.number_input("항공 요율 (원/kg)", min_value=0, value=5500, step=100)

            # 계산 (mm를 cm로 변환하여 부피 계산)
            total_actual_weight = spec['weight_kg'] * qty
            vol_weight = (spec['length_mm']/10 * spec['width_mm']/10 * spec['height_mm']/10 / 6) * qty
            chargeable_weight = max(total_actual_weight, vol_weight)
            total_cost = chargeable_weight * rate

            st.write("#### 📊 계산 결과")
            res1, res2, res3 = st.columns(3)
            with res1: st.write(f"실제 총 중량: **{total_actual_weight:.2f} kg**")
            with res2: st.write(f"부피 총 중량: **{vol_weight:.2f} kg**")
            with res3: st.success(f"적용 중량: **{chargeable_weight:.2f} kg**")

            st.warning(f"### 💵 예상 총 항공 운임: **{int(total_cost):,} 원**")
        else:
            st.error("일치하는 모델을 찾을 수 없습니다.")
else:
    st.warning("엑셀 파일(bearing_list.xlsx)을 프로그램 폴더에 넣어주세요.")