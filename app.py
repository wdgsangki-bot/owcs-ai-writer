import json
import streamlit as st

from owcs_briefing_writer import write_briefing
from owcs_day_script_writer import generate_day_script


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_team_names():
    teams = load_json("teams.json")
    names = []

    for team in teams:
        if isinstance(team, dict):
            name = team.get("official_name") or team.get("name")
        else:
            name = str(team)

        if name:
            names.append(name)

    return sorted(list(set(names)))


def make_match(match_no, time, team_a, team_b):
    return {
        "match_no": match_no,
        "time": time,
        "team_a": team_a,
        "team_b": team_b,
    }


st.set_page_config(
    page_title="OWCS AI Writer",
    layout="wide",
)

st.title("OWCS 방송작가 AI")

mode = st.radio(
    "생성 유형",
    ["브리프 생성", "DAY 대본 생성"],
    horizontal=True,
)

team_names = get_team_names()


if mode == "브리프 생성":
    st.subheader("매치 브리프 생성")

    col1, col2 = st.columns(2)

    with col1:
        team_a = st.selectbox("팀 A", team_names, index=0)

    with col2:
        team_b = st.selectbox("팀 B", team_names, index=1)

    if st.button("브리프 생성"):
        if team_a == team_b:
            st.warning("서로 다른 팀을 선택해주세요.")
        else:
            briefing = write_briefing(team_a, team_b)

            st.text_area(
                "방송 브리프",
                briefing,
                height=700,
            )

            st.download_button(
                "TXT 다운로드",
                data=briefing,
                file_name=f"{team_a}_vs_{team_b}_briefing.txt",
                mime="text/plain",
            )


if mode == "DAY 대본 생성":
    st.subheader("DAY 전체 대본 생성")

    col1, col2, col3 = st.columns(3)

    with col1:
        event_name = st.text_input(
            "대회명",
            "2026 OWCS KOREA STAGE 2",
        )
        day_label = st.text_input("DAY", "DAY 4")

    with col2:
        date_text = st.text_input(
            "날짜",
            "2026년 6월 12일 (금)",
        )
        start_time = st.text_input("시작 시간", "17시")

    with col3:
        caster = st.text_input("캐스터", "박한얼")
        analyst = st.text_input("해설", "장지수")

    st.divider()

    st.subheader("지난 경기 결과")

    previous_results = []

    for i in range(1, 4):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 3])

        with c1:
            prev_team_a = st.selectbox(
                f"지난 경기 {i} 팀 A",
                team_names,
                key=f"prev_team_a_{i}",
            )

        with c2:
            prev_score_a = st.number_input(
                f"A 점수 {i}",
                min_value=0,
                max_value=10,
                value=3,
                key=f"prev_score_a_{i}",
            )

        with c3:
            prev_score_b = st.number_input(
                f"B 점수 {i}",
                min_value=0,
                max_value=10,
                value=0,
                key=f"prev_score_b_{i}",
            )

        with c4:
            prev_team_b = st.selectbox(
                f"지난 경기 {i} 팀 B",
                team_names,
                index=min(i, len(team_names) - 1),
                key=f"prev_team_b_{i}",
            )

        previous_results.append(
            {
                "team_a": prev_team_a,
                "score_a": prev_score_a,
                "score_b": prev_score_b,
                "team_b": prev_team_b,
            }
        )

    st.divider()

    st.subheader("스탠딩")

    standings = []

    for i in range(1, 10):
        c1, c2, c3, c4, c5 = st.columns([1, 4, 1, 1, 2])

        with c1:
            rank = st.number_input(
                f"순위 {i}",
                min_value=1,
                max_value=20,
                value=i,
                key=f"rank_{i}",
            )

        with c2:
            team = st.selectbox(
                f"팀 {i}",
                team_names,
                index=min(i - 1, len(team_names) - 1),
                key=f"standing_team_{i}",
            )

        with c3:
            w = st.number_input(
                f"W {i}",
                min_value=0,
                max_value=20,
                value=0,
                key=f"standing_w_{i}",
            )

        with c4:
            l = st.number_input(
                f"L {i}",
                min_value=0,
                max_value=20,
                value=0,
                key=f"standing_l_{i}",
            )

        with c5:
            diff = st.text_input(
                f"+/- {i}",
                "0",
                key=f"standing_diff_{i}",
            )

        standings.append(
            {
                "rank": rank,
                "team": team,
                "w": w,
                "l": l,
                "diff": diff,
            }
        )

    st.divider()

    st.subheader("오늘의 매치업")

    today_matches = []

    for i in range(1, 4):
        c1, c2, c3, c4 = st.columns([1, 2, 4, 4])

        with c1:
            match_no = st.number_input(
                f"MATCH {i} 번호",
                min_value=1,
                max_value=100,
                value=i,
                key=f"today_match_no_{i}",
            )

        with c2:
            match_time = st.text_input(
                f"MATCH {i} 시간",
                f"{15 + (i - 1) * 2}:00",
                key=f"today_match_time_{i}",
            )

        with c3:
            team_a = st.selectbox(
                f"MATCH {i} 팀 A",
                team_names,
                index=min(i - 1, len(team_names) - 1),
                key=f"today_team_a_{i}",
            )

        with c4:
            team_b = st.selectbox(
                f"MATCH {i} 팀 B",
                team_names,
                index=min(i, len(team_names) - 1),
                key=f"today_team_b_{i}",
            )

        today_matches.append(
            make_match(match_no, match_time, team_a, team_b)
        )

    st.divider()

    st.subheader("다음 매치업")

    next_matches = []

    for i in range(1, 4):
        c1, c2, c3, c4 = st.columns([1, 2, 4, 4])

        with c1:
            match_no = st.number_input(
                f"NEXT MATCH {i} 번호",
                min_value=1,
                max_value=100,
                value=i + 3,
                key=f"next_match_no_{i}",
            )

        with c2:
            match_time = st.text_input(
                f"NEXT MATCH {i} 시간",
                f"{15 + (i - 1) * 2}:00",
                key=f"next_match_time_{i}",
            )

        with c3:
            team_a = st.selectbox(
                f"NEXT MATCH {i} 팀 A",
                team_names,
                index=min(i + 1, len(team_names) - 1),
                key=f"next_team_a_{i}",
            )

        with c4:
            team_b = st.selectbox(
                f"NEXT MATCH {i} 팀 B",
                team_names,
                index=min(i + 2, len(team_names) - 1),
                key=f"next_team_b_{i}",
            )

        next_matches.append(
            make_match(match_no, match_time, team_a, team_b)
        )

    st.divider()

    if st.button("전체 DAY 대본 생성"):
        script = generate_day_script(
            event_name=event_name,
            day_label=day_label,
            date_text=date_text,
            start_time=start_time,
            caster=caster,
            analyst=analyst,
            previous_results=previous_results,
            standings=standings,
            today_matches=today_matches,
            next_matches=next_matches,
        )

        st.text_area(
            "전체 DAY 대본",
            script,
            height=1000,
        )

        st.download_button(
            "TXT 다운로드",
            data=script,
            file_name=f"{event_name}_{day_label}_script.txt",
            mime="text/plain",
        )