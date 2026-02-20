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

# 2. 엑셀 데이터 로드 함수 (캐싱 처리하여 속도 향상)
@st.cache_data
def load_data():
    try:
        # 엑셀 파일 이름을 'bearing_list.xlsx'로 저장해서 업로드했다고 가정합니다.
        df = pd.read_excel("bearing_list.xlsx")
        # 데이터의 공백 제거 및 문자열 변환
        df['base_model'] = df['base_model'].astype(str).str.strip()
        df['model'] = df['model'].astype(str).str.strip()
        return df
    except:
        return None

st.set_page_config(page_title="항공 운임 계산기", layout="wide")
realtime_rate = get_realtime_usd()
df = load_data()

st.title("🚢 베어링 항공 운임 스마트 계산기")
st.markdown(f"**현재 시장 환율(참고):** 1$ = {realtime_rate:,.2f} 원")

# --- 검색 섹션 ---
st.header("🔍 베어링 규격 검색")
if df is not None:
    search_query = st.text_input("검색할 형번을 입력하세요 (예: 22214)", "").strip()
    
    if search_query:
        # 부분 일치 검색 (형번이나 전체 모델명에 포함된 경우)
        filtered_df = df[df['base_model'].str.contains(search_query, case=False) | 
                         df['model'].str.contains(search_query, case=False)]
        
        if not filtered_df.empty:
            # 검색된 결과 중 하나를 선택 (모델명 + 메이커)
            selection_list = filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1).tolist()
            selected_item = st.selectbox("정확한 모델을 선택하세요", selection_list)
            
            # 선택된 데이터 추출
            selected_row = filtered_df[filtered_df.apply(lambda x: f"{x['model']} ({x['maker']})", axis=1) == selected_item].iloc[0]
            
            # 자동 입력값 설정
            init_l = float(selected_row['length_mm'])
            init_w = float(selected_row['width_mm'])
            init_h = float(selected_row['height_mm'])
            init_weight = float(selected_row['weight_kg'])
            st.success(f"✅ {selected_item} 규격이 로드되었습니다.")
        else:
            st.warning("❌ 검색 결과가 없습니다. 직접 입력해 주세요.")
            init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0
    else:
        init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0
else:
    st.error("엑셀 파일을 찾을 수 없습니다. 'bearing_list.xlsx' 파일이 업로드되었는지 확인하세요.")
    init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0

st.divider()

# --- 입력 및 계산 섹션 ---
st.header("1. 정보 확인 및 입력")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📏 규격 (mm)")
    l_mm = st.number_input("가로 (mm)", min_value=1.0, value=init_l)
    w_mm = st.number_input("세로 (mm)", min_value=1.0, value=init_w)
    h_mm = st.number_input("높이 (mm)", min_value=1.0, value=init_h)

with col2:
    st.subheader("⚖️ 중량 및 수량")
    weight = st.number_input("개당 무게 (kg)", min_value=0.01, value=init_weight, format="%.2f")
    quantity = st.number_input("총 수량 (EA)", min_value=1, value=100)

with col3:
    st.subheader("💰 요금 및 환율")
    unit_price = st.number_input("kg당 운임 ($)", min_value=0.0, value=5.0)
    exchange_rate = st.number_input("적용 환율 (원/$)", min_value=1.0, value=1450.0)

# 계산 로직
length_cm, width_cm, height_cm = l_mm/10, w_mm/10, h_mm/10
total_actual_weight = weight * quantity
total_volume_weight = (length_cm * width_cm * height_cm * quantity) / 6000
chargeable_weight = max(total_actual_weight, total_volume_weight)
estimated_cost_usd = chargeable_weight * unit_price
estimated_cost_krw = estimated_cost_usd * exchange_rate

# 결과 출력
st.divider()
st.header("2. 예상 운임 결과")
res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric("최종 청구 무게 (C.W)", f"{chargeable_weight:.2f} kg")
res_col2.metric("예상 운임 (USD)", f"$ {estimated_cost_usd:,.2f}")
res_col3.metric("예상 운임 (KRW)", f"{int(estimated_cost_krw):,} 원")