import streamlit as st
import json
from owcs_briefing_writer import write_briefing


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_team_name(team):
    if isinstance(team, dict):
        return team.get("official_name") or team.get("name") or ""
    return str(team)


teams = load_json("teams.json")

team_names = [get_team_name(team) for team in teams]
team_names = [name for name in team_names if name]

st.set_page_config(page_title="OWCS AI Writer", layout="wide")

st.title("OWCS 방송작가 AI")
st.caption("팀을 선택하면 방송 브리프를 자동 생성합니다.")

col1, col2 = st.columns(2)

with col1:
    team_a = st.selectbox("팀 A", team_names)

with col2:
    team_b = st.selectbox(
        "팀 B",
        team_names,
        index=1 if len(team_names) > 1 else 0
    )

if st.button("브리프 생성"):
    if team_a == team_b:
        st.warning("서로 다른 팀을 선택해주세요.")
    else:
        briefing = write_briefing(team_a, team_b)

        st.subheader("방송 브리프")
        st.text_area("결과", briefing, height=600)

        st.download_button(
            label="TXT 다운로드",
            data=briefing,
            file_name=f"{team_a}_vs_{team_b}_briefing.txt",
            mime="text/plain"
        )