import streamlit as st
import json
import math
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="Robot Cycle Time Predictor", layout="wide")
st.title("🤖 취출기 사이클 타임 예측 프로그램")

# 2. 데이터 로드 (백데이터)
def load_data():
    with open('robot_data.json', 'r') as f:
        return json.load(f)

robot_db = load_data()

# 3. 사이클 타임 계산 함수
def calculate_move_time(dist, spec):
    if dist <= 0: return 0
    a, v = spec['acc'], spec['vel']
    d_acc = (v**2) / (2 * a)
    
    if dist >= 2 * d_acc:
        return (v / a) * 2 + (dist - 2 * d_acc) / v
    else:
        return 2 * math.sqrt(dist / a)

# 4. 사이드바: 기종 선택 및 정보 확인
st.sidebar.header("⚙️ 기종 설정")
selected_model = st.sidebar.selectbox("취출기 기종 선택", list(robot_db.keys()))
specs = robot_db[selected_model]

with st.sidebar.expander("선택 기종 상세 사양"):
    st.json(specs)

# 5. 메인 화면: 공정 입력 섹션
st.subheader(f"📍 {selected_model} 공정 시퀀스 입력")

# 세션 상태를 이용한 공정 리스트 관리
if 'rows' not in st.session_state:
    st.session_state.rows = [{"name": "금형진입(Z)", "axis": "Z", "dist": 500.0, "delay": 0.1, "is_takeout": True}]

def add_row():
    st.session_state.rows.append({"name": "신규공정", "axis": "X", "dist": 0.0, "delay": 0.0, "is_takeout": False})

# 공정 입력 테이블 구성
input_data = []
for i, row in enumerate(st.session_state.rows):
    cols = st.columns([2, 1, 1, 1, 1])
    name = cols[0].text_input(f"공정명 #{i+1}", value=row['name'], key=f"name_{i}")
    axis = cols[1].selectbox(f"축 #{i+1}", ["X", "Y", "Z", "R1", "R2"], index=["X", "Y", "Z", "R1", "R2"].index(row['axis']), key=f"axis_{i}")
    dist = cols[2].number_input(f"이동거리(mm) #{i+1}", value=row['dist'], key=f"dist_{i}")
    delay = cols[3].number_input(f"딜레이(s) #{i+1}", value=row['delay'], key=f"delay_{i}")
    is_takeout = cols[4].checkbox(f"취출구간 #{i+1}", value=row['is_takeout'], key=f"takeout_{i}")
    input_data.append({"name": name, "axis": axis, "dist": dist, "delay": delay, "is_takeout": is_takeout})

st.button("➕ 공정 추가", on_click=add_row)

# 6. 계산 및 결과 전시
takeout_time = 0
total_time = 0
results = []

for item in input_data:
    move_t = calculate_move_time(item['dist'], specs[item['axis']])
    step_t = move_t + item['delay']
    
    if item['is_takeout']:
        takeout_time += step_t
    total_time += step_t
    
    results.append({
        "공정": item['name'],
        "이동시간(s)": round(move_t, 3),
        "총 소요(s)": round(step_t, 3)
    })

# 결과 대시보드
st.divider()
c1, c2 = st.columns(2)
c1.metric("⏱ 예상 취출 시간 (Take-out)", f"{takeout_time:.2f} s")
c2.metric("🔄 전체 사이클 타임 (Total)", f"{total_time:.2f} s")

st.table(pd.DataFrame(results))
