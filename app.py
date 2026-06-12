import json
from datetime import date

import pandas as pd
import streamlit as st

from owcs_briefing_writer import write_briefing
from owcs_day_script_writer import generate_day_script
from owcs_standings import get_standings


SHEET_ID = "1H_05K75EinAgt1HmLQ3-in3R6N0wAI3vNfFITp1zDcA"

SCHEDULE_GID = "1213279406"
ROSTER_GID = "1750053340"


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default if default is not None else []


@st.cache_data(ttl=60)
def load_google_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    return pd.read_csv(url)


def get_team_names():
    teams = load_json("teams.json", [])
    names = []

    if isinstance(teams, dict):
        teams = teams.get("teams", [])

    for team in teams:
        if isinstance(team, dict):
            name = team.get("official_name") or team.get("name") or team.get("team")
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


def make_result(team_a, score_a, score_b, team_b):
    return {
        "team_a": team_a,
        "score_a": score_a,
        "score_b": score_b,
        "team_b": team_b,
    }


def prepare_schedule_df(df):
    df = df.copy()

    required_columns = [
        "date",
        "day",
        "day_label",
        "event_name",
        "match_no",
        "time",
        "team_a",
        "team_b",
        "tournament_filter",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"09_DAY_SCHEDULE 시트에 컬럼이 없습니다: {missing}")
        st.stop()

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["match_no"] = df["match_no"].astype(int)

    return df


def prepare_roster_df(df):
    df = df.copy()

    required_columns = [
        "date",
        "team",
        "player1",
        "player2",
        "player3",
        "player4",
        "player5",
        "sub1",
        "sub2",
        "coach",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.warning(f"10_DAILY_ROSTER 시트에 컬럼이 없습니다: {missing}")
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def get_today_matches(df, selected_date):
    return df[df["date"] == selected_date].sort_values("match_no")


def get_next_matches(df, selected_date):
    future_dates = sorted(df[df["date"] > selected_date]["date"].unique())

    if not future_dates:
        return pd.DataFrame()

    next_date = future_dates[0]
    return df[df["date"] == next_date].sort_values("match_no")


def get_previous_matches(df, selected_date):
    past_dates = sorted(df[df["date"] < selected_date]["date"].unique(), reverse=True)

    if not past_dates:
        return pd.DataFrame()

    previous_date = past_dates[0]
    return df[df["date"] == previous_date].sort_values("match_no")


def get_roster_text(roster_df, selected_date, team):
    if roster_df is None or roster_df.empty:
        return ""

    row = roster_df[
        (roster_df["date"] == selected_date) &
        (roster_df["team"] == team)
    ]

    if row.empty:
        return ""

    row = row.iloc[0]

    columns = [
        "player1",
        "player2",
        "player3",
        "player4",
        "player5",
        "sub1",
        "sub2",
        "coach",
    ]

    names = []

    for col in columns:
        value = row.get(col, "")
        if pd.notna(value) and str(value).strip():
            names.append(str(value).strip())

    return " / ".join(names)


st.set_page_config(
    page_title="WDG DATA",
    layout="wide",
)

st.title("WDG DATA")
st.caption("Esports Broadcast Intelligence Platform")

with st.sidebar:
    st.header("WDG DATA")
    game = st.selectbox(
        "게임 / 리그",
        ["OWCS", "VCT", "LCK CL", "THE FINALS"],
        index=0,
    )

    if game != "OWCS":
        st.info("현재는 OWCS 데이터만 연결되어 있습니다.")

    mode = st.radio(
        "콘텐츠 선택",
        ["DAY 대본 생성", "브리프 생성"],
        index=0,
    )

team_names = get_team_names()

try:
    schedule_df = load_google_sheet(SCHEDULE_GID)
    schedule_df = prepare_schedule_df(schedule_df)
except Exception as e:
    st.error("Google Sheet의 09_DAY_SCHEDULE을 불러오지 못했습니다.")
    st.exception(e)
    st.stop()

try:
    roster_df = load_google_sheet(ROSTER_GID)
    roster_df = prepare_roster_df(roster_df)
except Exception:
    roster_df = pd.DataFrame()


if mode == "DAY 대본 생성":
    st.subheader("DAY 전체 대본 생성")

    language = st.selectbox(
        "언어",
        ["한국어", "일본어"],
    )

    st.divider()
    st.subheader("캘린더")

    schedule_dates = sorted(schedule_df["date"].unique())

    default_date = date.today()
    if default_date not in schedule_dates:
        default_date = schedule_dates[0]

    selected_date = st.date_input(
        "방송 날짜 선택",
        value=default_date,
    )

    today_df = get_today_matches(schedule_df, selected_date)
    next_df = get_next_matches(schedule_df, selected_date)
    previous_df = get_previous_matches(schedule_df, selected_date)

    if today_df.empty:
        st.warning("선택한 날짜에 등록된 경기가 없습니다.")
        st.stop()

    first_row = today_df.iloc[0]

    st.success(
        f"{first_row.get('day_label', '')} / {selected_date} 경기 자동 로드 완료"
    )

    with st.expander("Google Sheet 원본 데이터 확인"):
        st.dataframe(today_df, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        event_name = st.text_input(
            "대회명",
            str(first_row.get("event_name", "2026 OWCS KOREA STAGE 2")),
        )
        day_label = st.text_input(
            "DAY",
            str(first_row.get("day_label", "DAY 1")),
        )

    with col2:
        date_text = st.text_input(
            "날짜",
            selected_date.strftime("%Y년 %m월 %d일"),
        )
        start_time = st.text_input(
            "시작 시간",
            str(first_row.get("time", "17:00")),
        )

    with col3:
        caster = st.text_input("캐스터", "박한얼")
        analyst = st.text_input("해설", "장지수")

    st.divider()
    st.subheader("지난 경기 결과")

    previous_results = []

    if not previous_df.empty:
        st.caption("직전 방송일 매치업을 자동 로드했습니다. 점수는 방송 당일 입력하세요.")

        for i, row in previous_df.reset_index(drop=True).iterrows():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 3])

            with c1:
                prev_team_a = st.text_input(
                    f"지난 경기 {i + 1} 팀 A",
                    str(row.get("team_a", "")),
                    key=f"prev_team_a_{i}",
                    label_visibility="collapsed",
                )

            with c2:
                prev_score_a = st.number_input(
                    f"지난 경기 {i + 1} A 점수",
                    min_value=0,
                    max_value=10,
                    value=0,
                    key=f"prev_score_a_{i}",
                    label_visibility="collapsed",
                )

            with c3:
                prev_score_b = st.number_input(
                    f"지난 경기 {i + 1} B 점수",
                    min_value=0,
                    max_value=10,
                    value=0,
                    key=f"prev_score_b_{i}",
                    label_visibility="collapsed",
                )

            with c4:
                prev_team_b = st.text_input(
                    f"지난 경기 {i + 1} 팀 B",
                    str(row.get("team_b", "")),
                    key=f"prev_team_b_{i}",
                    label_visibility="collapsed",
                )

            previous_results.append(
                make_result(prev_team_a, prev_score_a, prev_score_b, prev_team_b)
            )
    else:
        st.caption("이전 방송일이 없습니다.")

    st.divider()
    st.subheader("스탠딩 자동 계산")

    tournament_filter = st.text_input(
        "스탠딩 기준 대회",
        str(first_row.get("tournament_filter", "2026_KR_STAGE2")),
    )

    standings = get_standings(tournament_filter)

    if standings:
        for s in standings:
            st.write(
                f"{s['rank']}위 | {s['team']} | "
                f"{s['w']}승 {s['l']}패 | {s['diff']}"
            )
    else:
        st.warning("해당 대회 기준 스탠딩 데이터가 없습니다.")

    st.divider()
    st.subheader("오늘의 매치업")

    today_matches = []

    for i, row in today_df.reset_index(drop=True).iterrows():
        c1, c2, c3, c4 = st.columns([0.8, 1.2, 3, 3])

        with c1:
            match_no = st.number_input(
                f"MATCH {i + 1} 번호",
                min_value=1,
                max_value=100,
                value=int(row.get("match_no", i + 1)),
                key=f"today_match_no_{i}",
                label_visibility="collapsed",
            )

        with c2:
            match_time = st.text_input(
                f"MATCH {i + 1} 시간",
                str(row.get("time", "17:00")),
                key=f"today_match_time_{i}",
                label_visibility="collapsed",
            )

        with c3:
            team_a = st.text_input(
                f"MATCH {i + 1} 팀 A",
                str(row.get("team_a", "")),
                key=f"today_team_a_{i}",
                label_visibility="collapsed",
            )

        with c4:
            team_b = st.text_input(
                f"MATCH {i + 1} 팀 B",
                str(row.get("team_b", "")),
                key=f"today_team_b_{i}",
                label_visibility="collapsed",
            )

        today_matches.append(
            make_match(match_no, match_time, team_a, team_b)
        )

    st.divider()
    st.subheader("다음 매치업")

    next_matches = []

    if not next_df.empty:
        for i, row in next_df.reset_index(drop=True).iterrows():
            st.write(
                f"MATCH {row.get('match_no')} | "
                f"{row.get('time')} | "
                f"{row.get('team_a')} vs {row.get('team_b')}"
            )

            next_matches.append(
                make_match(
                    int(row.get("match_no", i + 1)),
                    str(row.get("time", "")),
                    str(row.get("team_a", "")),
                    str(row.get("team_b", "")),
                )
            )
    else:
        st.caption("다음 경기 일정이 없습니다.")

    st.divider()
    st.subheader("당일 로스터")

    rosters = {}

    for m in today_matches:
        for team in [m["team_a"], m["team_b"]]:
            if team and team not in rosters:
                default_roster = get_roster_text(roster_df, selected_date, team)

                rosters[team] = st.text_area(
                    f"{team} 로스터",
                    value=default_roster,
                    placeholder="예: Proper / Stalk3r / Smurf / Chiyo / Fielder",
                    height=100,
                )

    st.divider()

  if st.button("전체 DAY 대본 생성", type="primary"):
    script = generate_day_script(
        language=language,
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
        rosters=rosters,
    )

    st.session_state["day_script"] = script

if "day_script" in st.session_state:
    st.text_area(
        "전체 DAY 대본",
        st.session_state["day_script"],
        height=1000,
    )

    st.download_button(
        "TXT 다운로드",
        data=st.session_state["day_script"],
        file_name=f"{event_name}_{day_label}_{language}_script.txt",
        mime="text/plain",
    )


if mode == "브리프 생성":
    st.subheader("브로드캐스트 브리프")

    col1, col2 = st.columns(2)

    with col1:
        team_a = st.selectbox("팀 A", team_names, index=0)

    with col2:
        team_b = st.selectbox("팀 B", team_names, index=1)

    if st.button("브리프 생성", type="primary"):
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