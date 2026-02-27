import streamlit as st
import pandas as pd
import re

# --- [고정 규칙 1 & 2] 타이틀 설정 (비행기 아이콘 + 작은 버전 표시) ---
st.set_page_config(page_title="베어링 항공운임 스마트 계산기", page_icon="✈️")

st.markdown("""
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">✈️ 베어링 항공운임 스마트 계산기</h1>
        <span style="font-size: 0.9em; color: gray;">Ver 4.1</span>
    </div>
""", unsafe_allow_html=True)

# --- [고정 규칙 3] 항공 운임 기본 계산 방법 안내 ---
# 검색창 바로 위에 고정적으로 표시되도록 배치했습니다.
st.info("💡 **항공 운임 계산 가이드**")
st.markdown("""
* **실제 중량(A.W):** 화물의 실제 무게 (kg)
* **부피 중량(V.W):** 가로(cm) × 세로(cm) × 높이(cm) ÷ 6,000
* **운임 적용 중량:** 실제 중량과 부피 중량 중 **더 큰 값**을 기준으로 요금이 책정됩니다.
""")

st.divider()

# --- 지능형 매칭 함수 (90000번대 ASSY 완전 격리 로직) ---
def smart_match_logic(search_query, row_model):
    s_q = str(search_query).strip().upper()
    r_m = str(row_model).strip().upper()
    
    def extract_num(text):
        main = text.split('-')[0]
        return "".join(re.findall(r'\d+', main))
    
    s_num = extract_num(s_q)
    r_num = extract_num(r_m)

    # ASSY 특수 처리: 검색어나 데이터에 '-9'가 포함된 경우 (어제 성공한 그 로직!)
    if '-9' in s_q or '-9' in r_m:
        return s_q == r_m or (s_q in r_m and len(s_q) > 10)
    
    # 일반 모델: 숫자 기반 매칭
    return s_num == r_num if s_num else False

# --- 데이터 로드 ---
@st.cache_data
def load_data():
    try:
        # 실제 사용하시는 엑셀 파일명으로 확인해주세요!
        return pd.read_excel("bearing_list.xlsx")
    except Exception as e:
        st.error(f"엑셀 파일을 찾을 수 없습니다: {e}")
        return pd.DataFrame()

df = load_data()

# --- 메인 UI: 베어링 규격 검색 ---
if not df.empty:
    st.subheader("🔍 베어링 규격 검색")
    search_query = st.text_input("형번을 입력하세요 (예: 32034, 26822, HM266449-90158)", "").strip().upper()

    if search_query:
        mask = df['model'].apply(lambda x: smart_match_logic(search_query, x))
        filtered_df = df[mask]

        if not filtered_df.empty:
            selected_model = st.selectbox("리스트에서 정확한 모델을 선택하세요:", filtered_df['model'].tolist())
            
            # 선택된 데이터 상세 표시
            spec = filtered_df[filtered_df['model'] == selected_model].iloc[0]
            
            st.write(f"### 📋 {selected_model} 상세 정보")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("제조사", spec['maker'])
            with c2: st.metric("개당 중량", f"{spec['weight_kg']} kg")
            with c3: st.metric("가로x세로(mm)", f"{int(spec['length_mm'])}x{int(spec['width_mm'])}")
            with c4: st.metric("높이(mm)", f"{int(spec['height_mm'])}")

            # --- 항공 운임 계산기 섹션 ---
            st.divider()
            st.subheader("💰 항공 운임 시뮬레이션")
            
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                qty = st.number_input("주문 수량(pcs)", min_value=1, value=1)
            with col_in2:
                rate = st.number_input("항공 요율 (원/kg)", min_value=0, value=5500, step=100)

            # 계산 로직
            total_actual_weight = spec['weight_kg'] * qty
            # 부피 중량 (mm단위를 cm로 변환: /10, 그 후 /6)
            vol_weight = (spec['length_mm']/10 * spec['width_mm']/10 * spec['height_mm']/10 / 6) * qty
            chargeable_weight = max(total_actual_weight, vol_weight)
            total_cost = chargeable_weight * rate

            st.write("#### 📊 계산 결과")
            res1, res2, res3 = st.columns(3)
            with res1:
                st.write(f"실제 총 중량: **{total_actual_weight:.2f} kg**")
            with res2:
                st.write(f"부피 총 중량: **{vol_weight:.2f} kg**")
            with res3:
                st.success(f"적용 중량: **{chargeable_weight:.2f} kg**")

            st.warning(f"### 💵 예상 총 항공 운임: **{int(total_cost):,} 원**")

        else:
            st.error("일치하는 모델을 찾을 수 없습니다. 형번을 다시 확인해주세요.")
else:
    st.warning("엑셀 데이터를 먼저 준비해주세요.")