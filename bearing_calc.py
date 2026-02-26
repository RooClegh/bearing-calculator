import streamlit as st
import pandas as pd

# --- [고정 규칙 1 & 2] 타이틀 및 버전 표기 ---
st.markdown("## ✈️ 베어링 항공 운임 스마트 계산기 <small style='font-size: 15px; color: gray;'>Ver 3.6</small>", unsafe_allow_html=True)

# --- [고정 규칙 3] 기본적인 항공료 계산법 기재 ---
st.markdown("### 📋 기본적인 항공료 계산법")
st.caption("C.W(청구무게) = Max(실무게, 부피무게) | 부피무게 = (L*W*H / 6,000)")

st.divider()

# --- 1. 베어링 규격 검색 (데이터에서 사이즈 호출) ---
st.header("🔍 1. 베어링 규격 검색 및 수량 입력")
# (여기서 엑셀 데이터를 불러와 init_l, init_w, init_h, init_weight를 가져옵니다)
# 예시값 세팅 (실제로는 검색 결과가 들어감)
b_name = "22214 EK"
b_l, b_w, b_h, b_weight = 125, 125, 31, 1.55 # mm, kg

col1, col2 = st.columns(2)
with col1:
    st.info(f"**선택된 모델:** {b_name} ({b_l}x{b_w}x{b_h}mm / {b_weight}kg)")
with col2:
    order_qty = st.number_input("수입 예정 수량 (EA)", min_value=1, value=100)

st.divider()

# --- 2. 예상 포장 설계 (베어링 정보를 바탕으로) ---
st.header("📦 2. 예상 포장 설계")
p_col1, p_col2 = st.columns(2)

with p_col1:
    p_type = st.selectbox("사용할 포장재", ["표준 종이 박스", "표준 팔레트", "직접 입력"])
    p_qty = st.number_input("예상 포장 개수 (CTN/PLT)", min_value=1, value=5)

with p_col2:
    if p_type == "표준 종이 박스":
        l, w, h, p_added_w = 245, 275, 150, 0.5
    elif p_type == "표준 팔레트":
        l, w, h, p_added_w = 1100, 1100, 700, 20.0 # 높이는 적재 상황에 따라 변경
    
    l = st.number_input("포장 가로 (mm)", value=l)
    w = st.number_input("포장 세로 (mm)", value=w)
    h = st.number_input("포장 높이 (mm)", value=h)

st.divider()

# --- 3. 포워더 계산법 적용 ---
st.header("🌐 3. 포워더 요율 적용 (미국 노선 기준)")
f_col1, f_col2 = st.columns(2)

with f_col1:
    af_price = st.number_input("포워더 A/F 단가 ($/kg)", value=1.75)
    surcharge = st.number_input("할증료 합계 (FSC+SSC) ($/kg)", value=1.35)

with f_col2:
    exch_rate = st.number_input("적용 환율 (원/$)", value=1463.2)
    aes_fee = st.checkbox("AES Filing 비용 ($25) 포함", value=True)

# --- 계산 로직 ---
total_bearing_weight = b_weight * order_qty
total_packing_weight = p_added_w * p_qty
final_gross_weight = total_bearing_weight + total_packing_weight

final_volume_weight = (l/10 * w/10 * h/10 * p_qty) / 6000
final_cw = max(final_gross_weight, final_volume_weight)

total_usd = (final_cw * (af_price + surcharge)) + (25.0 if aes_fee else 0)
total_krw = total_usd * exch_rate

# --- 최종 결과 ---
st.divider()
st.header("💰 4. 예상 청구 금액")
res1, res2, res3 = st.columns(3)
res1.metric("청구 중량 (C.W)", f"{final_cw:.2f} kg")
res2.metric("예상 금액 (USD)", f"$ {total_usd:,.2f}")
res3.metric("예상 금액 (KRW)", f"{int(total_krw):,} 원")