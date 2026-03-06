import streamlit as st
import pandas as pd

st.set_page_config(page_title="베어링 형번 검색", layout="wide")
st.title("🔍 베어링 형번 검색")

@st.cache_data
def load_data():
    # 혹시 한글 깨짐이 있다면 encoding='cp949'를 넣어주세요
    df = pd.read_csv("Bearing Cross Reference.csv") 
    return df

df = load_data()

# 1. F열부터 L열까지의 인덱스 확인 (CSV의 5번째 열부터 11번째 열까지)
# 파이썬은 0부터 시작하므로 F열은 index 5, L열은 index 11입니다.
# 만약 열 위치가 다르다면 이 숫자들(5, 12)만 조정하세요.
target_columns = df.iloc[:, 5:12] 

st.write("데이터베이스에서 검색 중...")
search_input = st.text_input("찾으시는 형번을 입력하세요:")

if search_input:
    search_term = search_input.strip().upper()
    
    # 2. 모든 타겟 열에서 검색어를 포함하는지 확인 (하나라도 포함하면 True)
    mask = target_columns.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
    results = df[mask]
    
    if not results.empty:
        st.success(f"총 {len(results)}건의 결과를 찾았습니다.")
        
        # [수정된 부분] 
        # 검색 결과의 인덱스를 1부터 시작하도록 새로 생성합니다.
        display_results = results.copy()
        display_results.index = range(1, len(display_results) + 1)
        
        # 인덱스 이름에 '순번'이라고 붙여줍니다.
        display_results.index.name = '순번'
        
        # 표를 출력합니다.
        st.dataframe(display_results, use_container_width=True)