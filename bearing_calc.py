import streamlit as st
import requests

# 실시간 환율을 참고용으로 가져오는 함수
def get_realtime_usd():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        data = response.json()
        return data['rates']['KRW']
    except:
        return 1450.0  # 실패 시 기본 설정값

# 페이지 설정
st.set_page_config(page_title="항공 운임 계산기", layout="wide")

# 사이드바 또는 상단에 현재 실시간 환율 정보 표시 (참고용)
realtime_rate = get_realtime_usd()

st.title("🚢 베어링 항공 운임 예측 계산기")
st.markdown(f"**현재 시장 환율(참고):** 1$ = {realtime_rate:,.2f} 원")

# 1. 입력 섹션
st.header("1. 정보 입력")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📏 규격 (cm)")
    length = st.number_input("가로", min_value=1.0, value=10.0)
    width = st.number_input("세로", min_value=1.0, value=10.0)
    height = st.number_input("높이", min_value=1.0, value=10.0)

with col2:
    st.subheader("⚖️ 중량 및 수량")
    weight = st.number_input("개당 무게 (kg)", min_value=0.1, value=1.0)
    quantity = st.number_input("총 수량 (EA)", min_value=1, value=100)

with col3:
    st.subheader("💰 요금 및 환율")
    unit_price = st.number_input("kg당 운임 ($)", min_value=0.0, value=5.0)
    # 기본값을 1450원으로 설정한 환율 입력창
    exchange_rate = st.number_input("적용 환율 (원/$)", min_value=1.0, value=1450.0)

# 2. 계산 로직
total_actual_weight = weight * quantity
total_volume = (length * width * height) * quantity
total_volume_weight = total_volume / 6000

# Chargeable Weight 판정
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

# 정보 메시지
if chargeable_weight == total_volume_weight:
    st.warning("⚠️ 부피 중량이 실제 무게보다 커서 부피 중량이 적용되었습니다.")
else:
    st.success("✅ 실제 무게를 기준으로 운임이 계산되었습니다.")

st.caption(f"※ 적용 환율 {exchange_rate:,.1f}원 기준으로 계산된 결과입니다.")