import streamlit as st
import pandas as pd

# --- [고정 규칙 1 & 2] 타이틀 및 버전 표기 ---
st.markdown("## ✈️ 베어링 항공 운임 스마트 계산기 <small style='font-size: 15px; color: gray;'>Ver 3.5 (포워더 맞춤형)</small>", unsafe_allow_html=True)

# --- [고정 규칙 3] 기본적인 항공료 계산법 기재 ---
with st.expander("📋 기본적인 항공료 계산법 (클릭하여 보기)", expanded=False):
    st.caption("""
    1. **실무게(Actual Weight):** (개당 무게 × 수량) + 포장재 무게  
    2. **부피무게(Volume Weight):** (가로cm × 세로cm × 높이cm × 포장개수) ÷ 6,000  
    3. **청구무게(Chargeable Weight):** 실무게와 부피무게 중 큰 값 적용  
    4. **최종운임:** 청구무게(C.W) × [kg당 단가($) + 할증료($)] × 적용 환율(₩)
    """)

st.divider()

# --- 1. 베어링 규격 검색 (기존 로직 유지) ---
st.header("🔍 1. 베어링 규격 검색")
# (데이터 로드 및 검색 코드는 동일하므로 생략, 변수 초기화만 확인)
init_weight = 1.0 # 검색 결과가 없을 때의 기본값

# --- 2. 포워더 맞춤형 상세 입력 ---
st.header("📦 2. 화물 상세 정보 (포워더 기준)")

# 여러 종류의 박스를 입력받기 위한 리스트 세션 상태 이용
if 'boxes' not in st.session_state:
    st.session_state.boxes = [{'l': 910, 'w': 1070, 'h': 610, 'gw': 157.0, 'qty': 4}]

def add_box():
    st.session_state.boxes.append({'l': 0, 'w': 0, 'h': 0, 'gw': 0.0, 'qty': 1})

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ 박스 종류 추가"):
        add_box()
with col_btn2:
    if st.button("♻️ 초기화"):
        st.session_state.boxes = [{'l': 910, 'w': 1070, 'h': 610, 'gw': 157.0, 'qty': 1}]

total_gw = 0.0
total_vw = 0.0

for i, box in enumerate(st.session_state.boxes):
    with st.expander(f"📦 화물 타입 {i+1}", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        box['l'] = c1.number_input(f"가로(mm)", value=box['l'], key=f"l_{i}")
        box['w'] = c2.number_input(f"세로(mm)", value=box['w'], key=f"w_{i}")
        box['h'] = c3.number_input(f"높이(mm)", value=box['h'], key=f"h_{i}")
        box['gw'] = c4.number_input(f"실무게(kg)", value=box['gw'], key=f"gw_{i}")
        box['qty'] = c5.number_input(f"수량(개)", value=box['qty'], key=f"qty_{i}")
        
        # 개별 계산
        b_vw = (box['l']/10 * box['w']/10 * box['h']/10 * box['qty']) / 6000
        b_gw = box['gw'] * box['qty']
        total_gw += b_gw
        total_vw += b_vw

st.divider()

# --- 3. 포워더 계약 요율 설정 ---
st.header("🌐 3. 포워더 계약 요율 설정")
c_r1, c_r2, c_r3 = st.columns(3)

with c_r1:
    af_price = st.number_input("항공 순수 단가 (A/F) ($/kg)", value=1.75, step=0.01)
    surcharge = st.number_input("할증료 합계 (FSC+SSC) ($/kg)", value=1.35, step=0.01)

with c_r2:
    exch_rate = st.number_input("포워더 적용 환율 (원/$)", value=1463.2)
    use_aes = st.checkbox("미국 AES Filing 비용 포함 ($25)", value=True)

with c_r3:
    st.info(f"**총 실무게:** {total_gw:.2f} kg\n\n**총 부피무게:** {total_vw:.2f} kg")

# --- 최종 계산 ---
final_cw = max(total_gw, total_vw)
net_freight_usd = final_cw * (af_price + surcharge)
if use_aes:
    net_freight_usd += 25.0

final_total_krw = net_freight_usd * exch_rate

# --- 4. 최종 결과 ---
st.divider()
st.header("💰 4. 포워더 청구 예상 금액")
res1, res2, res3 = st.columns(3)
res1.metric("최종 청구 무게 (C.W)", f"{final_cw:.2f} kg")
res2.metric("총 합계 (USD)", f"$ {net_freight_usd:,.2f}")
res3.metric("최종 청구액 (KRW)", f"{int(final_total_krw):,} 원")

if total_vw > total_gw:
    st.warning(f"⚠️ 부피무게가 실무게보다 {total_vw - total_gw:.2f}kg 더 많이 나갑니다. 포장에 주의하세요!")