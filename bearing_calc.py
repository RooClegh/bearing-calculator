import streamlit as st
import requests

# 실시간 환율 참고 함수
def get_realtime_usd():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        data = response.json()
        return data['rates']['KRW']
    except:
        return 1450.0

st.set_page_config(page_title="항공 운임 계산기", layout="wide")
realtime_rate = get_realtime_usd()

st.title("🚢 베어링 항공 운임 예측 계산기 (mm 버전)")
st.markdown(f"**현재 시장 환율(참고):** 1$ = {realtime_rate:,.2f} 원")

# 1. 입력 섹션
st.header("1. 정보 입력")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📏 규격 (mm)") # 단위를 mm로 변경
    l_mm = st.number_input("가로 (mm)", min_value=1.0, value=100.0, step=1.0)
    w_mm = st.number_input("세로 (mm)", min_value=1.0, value=100.0, step=1.0)
    h_mm = st.number_input("높이 (mm)", min_value=1.0, value=100.0, step=1.0)
    
    # 내부 계산을 위한 cm 변환
    length_cm = l_mm / 10
    width_cm = w_mm / 10
    height_cm = h_mm / 10

with col2:
    st.subheader("⚖️ 중량 및 수량")
    weight = st.number_input("개당 무게 (kg)", min_value=0.01, value=1.0, format="%.2f")
    quantity = st.number_input("총 수량 (EA)", min_value=1, value=100)

with col3:
    st.subheader("💰 요금 및 환율")
    unit_price = st.number_input("kg당 운임 ($)", min_value=0.0, value=5.0)
    exchange_rate = st.number_input("적용 환율 (원/$)", min_value=1.0, value=1450.0)

# 2. 계산 로직
total_actual_weight = weight * quantity
# 항공 운임 공식: (가로cm * 세로cm * 높이cm * 수량) / 6000
total_volume_cm3 = (length_cm * width_cm * height_cm) * quantity
total_volume_weight = total_volume_cm3 / 6000

chargeable_weight = max(total_actual_weight, total_volume_weight)
estimated_cost_usd = chargeable_weight * unit_price
estimated_cost_krw = estimated_cost_usd * exchange_rate

# 3. 결과 출력
st.divider()
st.header("2. 예상 운임 결과")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric("최종 청구 무게 (C.W)", f"{chargeable_weight:.2f} kg")
res_col2.metric("예상 운임 (USD)", f"$ {estimated_cost_usd:,.2f}")
res_col3.metric("예상 운임 (KRW)", f"{int(estimated_cost_krw):,} 원")

# 계산 상세 근거 표시 (검증용)
with st.expander("계산 상세 근거 보기"):
    st.write(f"- 입력된 규격: {l_mm} x {w_mm} x {h_mm} mm")
    st.write(f"- 변환된 규격: {length_cm} x {width_cm} x {height_cm} cm")
    st.write(f"- 실제 총 중량: {total_actual_weight:.2f} kg")
    st.write(f"- 부피 환산 중량: {total_volume_weight:.2f} kg")

if chargeable_weight == total_volume_weight:
    st.warning("⚠️ 부피 중량이 더 커서 부피 기준으로 계산되었습니다.")
else:
    st.success("✅ 실제 무게 기준으로 계산되었습니다.")