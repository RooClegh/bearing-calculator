import streamlit as st

# 웹 페이지 제목
st.title("🚢 베어링 항공 운임 예측 계산기")
st.write("규격과 수량을 입력하면 예상 운임을 산출합니다.")

# 1. 입력 섹션
st.header("1. 베어링 및 포장 정보 입력")
col1, col2 = st.columns(2)

with col1:
    length = st.number_input("가로 길이 (cm)", min_value=1.0, value=10.0)
    width = st.number_input("세로 길이 (cm)", min_value=1.0, value=10.0)
    height = st.number_input("높이 (cm)", min_value=1.0, value=10.0)

with col2:
    weight = st.number_input("실제 무게 (kg)", min_value=0.1, value=1.0)
    quantity = st.number_input("수량 (EA)", min_value=1, value=100)
    unit_price = st.number_input("kg당 예상 요금 ($)", min_value=0.0, value=5.0)

# 2. 물류 로직 계산
total_actual_weight = weight * quantity
total_volume = (length * width * height) * quantity
# 항공 부피 중량 공식 (V.W = CBM / 6000)
total_volume_weight = total_volume / 6000

# Chargeable Weight 판정 (둘 중 큰 값)
chargeable_weight = max(total_actual_weight, total_volume_weight)
estimated_cost = chargeable_weight * unit_price

# 3. 결과 출력
st.divider()
st.header("2. 예상 결과")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric("실제 총 무게", f"{total_actual_weight:.2f} kg")
res_col2.metric("부피 환산 무게", f"{total_volume_weight:.2f} kg")
res_col3.metric("최종 청구 무게", f"{chargeable_weight:.2f} kg", delta_color="inverse")

st.success(f"### 💰 예상 총 운임: $ {estimated_cost:,.2} (약 {estimated_cost * 1350:,.0f} 원)")

st.info("※ 본 계산은 단순 참고용이며, 실제 유류할증료 및 부대비용에 따라 달라질 수 있습니다.")