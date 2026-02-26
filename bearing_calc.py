import streamlit as st
import pandas as pd

# 1. 데이터 로드 함수
@st.cache_data
def load_data():
    file_name = "bearing_list.xlsx" 
    try:
        df = pd.read_excel(file_name)
        for col in ['base_model', 'model', 'maker']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    except:
        return None

# 설정 및 데이터 로드
st.set_page_config(page_title="동명베아링 운임 계산기", layout="wide")

df = load_data()

# --- [고정 규칙 1 & 2] 타이틀 및 버전 표기 ---
# 타이틀과 버전 정보를 안전한 마크다운 형식으로 변경
st.markdown(f"## ✈️ 베어링 항공 운임 스마트 계산기 <span style='font-size: 0.8em; color: gray; font-weight: normal;'>Ver 3.8</span>", unsafe_allow_html=True)

# --- [고정 규칙 3] 기본적인 항공료 계산법 기재 (스타일 수정본) ---
st.markdown("### 📋 기본적인 항공료 계산법")

# 스타일을 강제로 통일하기 위해 보이지 않는 설정을 살짝 넣고 텍스트 출력
st.info("""
1. 실무게(Actual Weight): (베어링 개당 무게 × 수량) + 포장재 무게
2. 부피무게(Volume Weight): (가로cm × 세로cm × 높이cm × 포장개수) ÷ 6,000
3. 청구무게(Chargeable Weight): 실무게와 부피무게 중 큰 값 적용
4. 최종운임: 청구무게(C.W) × [A/F단가(\$) + 할증료합계(\$)] × 적용 환율(￦)
""")

st.divider()

# --- 1. 베어링 규격 검색 및 수량 입력 ---
st.header("🔍 1. 베어링 규격 검색 및 수량 입력")
init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0
selected_model_name = "미선택"

if df is not None:
    search_query = st.text_input("검색할 베어링 형번을 입력하세요 (예: 22214)", "").strip()
    if search_query:
        mask = (df['base_model'].str.contains(search_query, case=False, na=False)) | \
               (df['model'].str.contains(search_query, case=False, na=False))
        filtered_df = df[mask]
        if not filtered_df.empty:
            selection_list = filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1).tolist()
            selected_item = st.selectbox("정확한 모델을 선택하세요", selection_list)
            row = filtered_df[filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1) == selected_item].iloc[0]
            
            init_l, init_w, init_h = float(row['length_mm']), float(row['width_mm']), float(row['height_mm'])
            init_weight = float(row['weight_kg'])
            selected_model_name = selected_item
            st.success(f"✅ {selected_item} 데이터 로드 완료")
else:
    st.error("⚠️ bearing_list.xlsx 파일을 불러올 수 없습니다.")

order_qty = st.number_input("수입 예정 총 수량 (EA)", min_value=1, value=100)

st.divider()

# --- 2. 예상 포장 설계 ---
st.header("📦 2. 예상 포장 설계")
p_col1, p_col2 = st.columns(2)

with p_col1:
    p_type = st.selectbox("사용할 포장 단위", ["표준 종이 박스", "표준 팔레트", "직접 입력"])
    p_qty = st.number_input("예상 포장 덩어리 개수 (CTN/PLT)", min_value=1, value=1)

with p_col2:
    if p_type == "표준 종이 박스":
        def_l, def_w, def_h, p_added_w = 245, 275, 150, 0.5
    elif p_type == "표준 팔레트":
        def_l, def_w, def_h, p_added_w = 1100, 1100, 700, 20.0
    else:
        def_l, def_w, def_h, p_added_w = init_l, init_w, init_h, 0.0
    
    final_l = st.number_input("최종 포장 가로 (mm)", value=int(def_l))
    final_w = st.number_input("최종 포장 세로 (mm)", value=int(def_w))
    final_h = st.number_input("최종 포장 높이 (mm)", value=int(def_h))

st.divider()

# --- 3. 포워더 요율 적용 ---
st.header("🌐 3. 포워더 계약 요율 적용")
f_col1, f_col2 = st.columns(2)

with f_col1:
    af_price = st.number_input("포워더 A/F 단가 ($/kg)", value=1.75)
    surcharge = st.number_input("할증료 합계 (FSC+SSC) ($/kg)", value=1.35)

with f_col2:
    exch_rate = st.number_input("적용 환율 (원/$)", value=1463.2)
    aes_fee = st.checkbox("미국 AES Filing 비용 ($25) 포함", value=True)

# --- 계산 로직 ---
total_bearing_net_weight = init_weight * order_qty
total_packing_tare_weight = p_added_w * p_qty
gross_weight = total_bearing_net_weight + total_packing_tare_weight
volume_weight = (final_l/10 * final_w/10 * final_h/10 * p_qty) / 6000
chargeable_weight = max(gross_weight, volume_weight)
total_usd = (chargeable_weight * (af_price + surcharge)) + (25.0 if aes_fee else 0)
total_krw = total_usd * exch_rate

# --- 4. 최종 결과 ---
st.divider()
st.header("💰 4. 포워더 예상 청구 금액")
res1, res2, res3 = st.columns(3)
res1.metric("청구 중량 (C.W)", f"{chargeable_weight:.2f} kg")
res2.metric("예상 금액 (USD)", f"$ {total_usd:,.2f}")
res3.metric("예상 금액 (KRW)", f"{int(total_krw):,} 원")