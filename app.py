import streamlit as st
import pandas as pd
from data_manager import load_data, save_data
from calc_engine import calculate_sequence

st.set_page_config(page_title="취출기 사이클 타임 예측", layout="wide")
st.title("🤖 취출기 사이클 타임 예측 프로그램")

robot_db = load_data()

tab1, tab2, tab3 = st.tabs(["사이클 계산", "기종 사양 관리", "결과 분석"])

# ---------------------------
# 탭 1: 사이클 계산
# ---------------------------
with tab1:
    st.subheader("공정 입력")

    selected_model = st.selectbox("취출기 기종 선택", list(robot_db.keys()))
    specs = robot_db[selected_model]

    with st.expander("선택 기종 축 사양 보기"):
        st.json(specs)

    default_row = {
        "name": "금형진입",
        "axis": "Z",
        "dist": 500.0,
        "delay": 0.1,
        "is_takeout": True,
        "group": 1
    }

    if "rows" not in st.session_state:
        st.session_state.rows = [default_row.copy()]

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ 공정 추가"):
            next_group = len(st.session_state.rows) + 1
            st.session_state.rows.append({
                "name": f"신규공정{next_group}",
                "axis": "X",
                "dist": 0.0,
                "delay": 0.0,
                "is_takeout": False,
                "group": next_group
            })

    with col_btn2:
        if st.button("🗑 마지막 공정 삭제") and len(st.session_state.rows) > 1:
            st.session_state.rows.pop()

    input_rows = []
    axis_options = list(specs.keys())

    st.markdown("### 공정 시퀀스")
    for i, row in enumerate(st.session_state.rows):
        cols = st.columns([2.2, 1, 1.1, 1, 0.8, 0.8])
        name = cols[0].text_input(f"공정명 #{i+1}", value=row["name"], key=f"name_{i}")
        axis = cols[1].selectbox(
            f"축 #{i+1}",
            axis_options,
            index=axis_options.index(row["axis"]) if row["axis"] in axis_options else 0,
            key=f"axis_{i}"
        )
        dist = cols[2].number_input(f"이동거리(mm) #{i+1}", min_value=0.0, value=float(row["dist"]), step=10.0, key=f"dist_{i}")
        delay = cols[3].number_input(f"딜레이(s) #{i+1}", min_value=0.0, value=float(row["delay"]), step=0.01, key=f"delay_{i}")
        is_takeout = cols[4].checkbox(f"취출 #{i+1}", value=row["is_takeout"], key=f"takeout_{i}")
        group = cols[5].number_input(f"그룹 #{i+1}", min_value=1, value=int(row["group"]), step=1, key=f"group_{i}")

        input_rows.append({
            "name": name,
            "axis": axis,
            "dist": dist,
            "delay": delay,
            "is_takeout": is_takeout,
            "group": group
        })

    st.session_state.rows = input_rows

    if st.button("📊 계산 실행", type="primary"):
        try:
            result = calculate_sequence(input_rows, specs)

            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("⏱ 예상 취출 시간", f"{result['takeout_time']:.3f} s")
            c2.metric("🔄 전체 사이클 타임", f"{result['total_time']:.3f} s")

            st.markdown("### 공정별 결과")
            df_rows = pd.DataFrame(result["rows"])
            df_rows = df_rows.rename(columns={
                "idx": "No",
                "name": "공정명",
                "axis": "축",
                "dist": "이동거리(mm)",
                "delay": "딜레이(s)",
                "is_takeout": "취출여부",
                "group": "동시이동그룹",
                "move_time": "이동시간(s)",
                "step_time": "총시간(s)"
            })
            st.dataframe(df_rows, use_container_width=True)

            st.markdown("### 그룹별 결과")
            df_groups = pd.DataFrame(result["groups"])
            df_groups = df_groups.rename(columns={
                "group": "그룹",
                "count": "공정수",
                "group_time": "그룹총시간(s)",
                "takeout_group_time": "취출그룹시간(s)"
            })
            st.dataframe(df_groups, use_container_width=True)

            csv = df_rows.to_csv(index=False).encode("utf-8-sig")
            st.download_button("결과 CSV 다운로드", data=csv, file_name="cycle_time_result.csv", mime="text/csv")

        except Exception as e:
            st.error(f"계산 중 오류 발생: {e}")


# ---------------------------
# 탭 2: 기종 사양 관리
# ---------------------------
with tab2:
    st.subheader("기종 백데이터 관리")

    manage_model = st.selectbox("수정할 기종", list(robot_db.keys()), key="manage_model")
    model_data = robot_db[manage_model]

    edited = {}

    for axis_name, axis_spec in model_data.items():
        st.markdown(f"#### 축 {axis_name}")
        c1, c2, c3 = st.columns(3)
        acc = c1.number_input(f"{axis_name} 가속도", min_value=0.0, value=float(axis_spec["acc"]), key=f"{manage_model}_{axis_name}_acc")
        dec = c2.number_input(f"{axis_name} 감속도", min_value=0.0, value=float(axis_spec["dec"]), key=f"{manage_model}_{axis_name}_dec")
        vel = c3.number_input(f"{axis_name} 속도", min_value=0.0, value=float(axis_spec["vel"]), key=f"{manage_model}_{axis_name}_vel")
        edited[axis_name] = {"acc": acc, "dec": dec, "vel": vel}

    if st.button("사양 저장"):
        robot_db[manage_model] = edited
        save_data(robot_db)
        st.success("기종 사양이 저장되었습니다.")

    st.divider()
    st.markdown("### 신규 기종 추가")
    new_model_name = st.text_input("신규 기종명")
    if st.button("신규 기종 생성"):
        if not new_model_name.strip():
            st.warning("기종명을 입력하세요.")
        elif new_model_name in robot_db:
            st.warning("이미 존재하는 기종명입니다.")
        else:
            robot_db[new_model_name] = {
                "X": {"acc": 3000, "dec": 3000, "vel": 1500},
                "Y": {"acc": 3000, "dec": 3000, "vel": 1500},
                "Z": {"acc": 3000, "dec": 3000, "vel": 1500},
                "R": {"acc": 1000, "dec": 1000, "vel": 800},
                "S": {"acc": 1000, "dec": 1000, "vel": 800}
            }
            save_data(robot_db)
            st.success(f"{new_model_name} 기종이 생성되었습니다.")


# ---------------------------
# 탭 3: 결과 분석 안내
# ---------------------------
with tab3:
    st.subheader("분석 포인트")
    st.markdown("""
    - 취출시간: 취출구간으로 체크된 공정만 합산
    - 전체시간: 전체 그룹 기준 합산
    - 같은 그룹 번호는 동시 이동으로 처리되어 가장 오래 걸리는 공정 시간이 반영됨
    - 실제 설비와 차이가 있다면 아래 항목 추가 보정 필요:
      - 금형 개폐 시간
      - 파지/탈착 시간
      - 진공 응답 시간
      - 에어블로우 시간
      - 안전 보정 시간
      - 컨트롤러 응답 지연
    """)
