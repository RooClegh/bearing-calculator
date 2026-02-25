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

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    file_name = "bearing_list.xlsx"
    try:
        df = pd.read_excel(file_name)
    except Exception:
        try:
            df = pd.read_csv(file_name)
        except Exception:
            return None
    for col in ['base_model', 'model', 'maker']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

st.set_page_config(page_title="동명베아링 운임 계산기", layout="wide")
realtime_rate = get_realtime_usd()
df = load_data()

# --- 타이틀 및 안내 섹션 ---
st.title("🚢 베어링 항공 운임 스마트 계산기 (Ver 3.1)")

st.info("💡 베어링 개별 수량과 실제 '포장 덩어리(박스/팔레트)'의 개수를 각각 입력해 주세요.")

# 사이드바: 회사 정보
st.sidebar.markdown("### 📍 도착지 정보")
st.sidebar.info("**동명베아링**\n\n부산광역시 사상구 새벽로215번길 123")

# --- 1. 검색 섹션 ---
st.header("🔍 1. 베어링 규격 검색")
init_l, init_w, init_h, init_weight = 100.0, 100.0, 100.0, 1.0

if df is not None:
    search_query = st.text_input("검색할 형번을 입력하세요 (예: 22214