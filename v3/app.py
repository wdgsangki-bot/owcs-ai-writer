import re
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st

from data_loader import (
    load_database,
    load_matches,
    load_assets,
    get_available_stages,
    get_current_stage,
    get_team_logo_path_v33d,
    aggregate_player_stats_with_roles,
    make_daily_research_document_v35,
    make_storyline_match_packet,
)


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="OWCS Broadcast Review",
    layout="wide",
)

st.title("OWCS Broadcast Intelligence")
st.caption("V4.1 Internal Review Web · Daily Research 검수용")


# ==================================================
# PATHS / REVIEW STORAGE
# ==================================================

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
REVIEW_FILE = DATA_DIR / "review_notes.csv"

REVIEW_COLUMNS = [
    "saved_at",
    "event_name",
    "broadcast_date",
    "stage",
    "match_no",
    "team_a",
    "team_b",
    "status",
    "reviewer",
    "comment",
]

STATUS_OPTIONS = ["초안", "검수중", "수정 필요", "확정"]


# ==================================================
# CACHE LAYER
# ==================================================

@st.cache_data(ttl=300, show_spinner=False)
def cached_load_database():
    return load_database()


@st.cache_data(ttl=300, show_spinner=False)
def cached_load_matches():
    db = load_database()
    return load_matches(db)


@st.cache_data(ttl=300, show_spinner=False)
def cached_load_assets():
    db = load_database()
    return load_assets(db)


@st.cache_data(ttl=300, show_spinner=False)
def cached_available_stages():
    db = load_database()
    return get_available_stages(db)


@st.cache_data(ttl=300, show_spinner=False)
def cached_current_stage():
    db = load_database()
    return get_current_stage(db)


@st.cache_data(ttl=300, show_spinner=False)
def cached_player_stats(stage):
    return aggregate_player_stats_with_roles(stage=stage)


@st.cache_data(ttl=300, show_spinner=False)
def cached_daily_doc(event_name, broadcast_date, stage, match_inputs_tuple, opening_note=""):
    db = load_database()
    return make_daily_research_document_v35(
        event_name=event_name,
        broadcast_date=str(broadcast_date),
        stage=stage,
        match_inputs_tuple=match_inputs_tuple,
        opening_note=opening_note,
        db=db,
    )


@st.cache_data(ttl=300, show_spinner=False)
def cached_match_packet(match_no, team_a, team_b, stage):
    db = load_database()
    return make_storyline_match_packet(
        team_a,
        team_b,
        stage=stage,
        match_no=match_no,
        db=db,
    )


# ==================================================
# HELPERS
# ==================================================

def normalize_key(value):
    if pd.isna(value):
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(value).strip().upper())


def get_data_source_label(db):
    if not isinstance(db, dict):
        return "NO_DB_DICT"

    meta = db.get("_DB_FILE")
    if meta is None or getattr(meta, "empty", True):
        return "NO_DB_FILE_META"

    if "source" in meta.columns:
        value = str(meta.iloc[0].get("source", "")).strip()
        return value if value else "EMPTY_SOURCE"

    return "UNKNOWN_SOURCE"


def get_team_options(matches, assets, player_stats=None):
    teams = set()

    if matches is not None and not matches.empty:
        for col in ["team_a", "team_b"]:
            if col in matches.columns:
                teams.update(matches[col].dropna().astype(str).tolist())

    if assets is not None and not assets.empty and "entity_id" in assets.columns:
        teams.update(assets["entity_id"].dropna().astype(str).tolist())

    if player_stats is not None and not player_stats.empty and "Team" in player_stats.columns:
        teams.update(player_stats["Team"].dropna().astype(str).tolist())

    return sorted([t for t in teams if t and normalize_key(t) != "UNKNOWN"])


def show_team_logo(team_id, db, width=80):
    logo_path = get_team_logo_path_v33d(team_id, db)
    if logo_path:
        st.image(str(logo_path), width=width)
    else:
        st.caption("No Logo")


def split_daily_doc_sections(doc):
    if not doc:
        return "", []

    marker = "==================================================\nMATCH "
    parts = doc.split(marker)
    intro = parts[0].strip()
    matches = []

    for part in parts[1:]:
        text = marker + part
        m = re.search(r"MATCH\s+(\d+)\s*\n(.+?)\n=+", text)
        if m:
            match_no = int(m.group(1))
            title = m.group(2).strip()
        else:
            match_no = len(matches) + 1
            title = f"MATCH {match_no}"

        matches.append(
            {
                "match_no": match_no,
                "title": title,
                "text": text.strip(),
            }
        )

    return intro, matches


def read_review_notes():
    if not REVIEW_FILE.exists():
        return pd.DataFrame(columns=REVIEW_COLUMNS)

    try:
        df = pd.read_csv(REVIEW_FILE)
    except Exception:
        return pd.DataFrame(columns=REVIEW_COLUMNS)

    for col in REVIEW_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[REVIEW_COLUMNS].copy()


def append_review_note(row):
    df = read_review_notes()
    new_df = pd.DataFrame([row])
    out = pd.concat([df, new_df], ignore_index=True)
    out.to_csv(REVIEW_FILE, index=False)


def get_latest_review(event_name, broadcast_date, stage, match_no, team_a, team_b):
    df = read_review_notes()
    if df.empty:
        return None

    mask = (
        (df["event_name"].astype(str) == str(event_name))
        & (df["broadcast_date"].astype(str) == str(broadcast_date))
        & (df["stage"].astype(str) == str(stage))
        & (df["match_no"].astype(str) == str(match_no))
        & (df["team_a"].astype(str) == str(team_a))
        & (df["team_b"].astype(str) == str(team_b))
    )

    sub = df[mask].copy()
    if sub.empty:
        return None

    return sub.iloc[-1].to_dict()


def status_badge(status):
    if status == "확정":
        return "✅ 확정"
    if status == "수정 필요":
        return "🔴 수정 필요"
    if status == "검수중":
        return "🟡 검수중"
    return "⚪ 초안"


# ==================================================
# LOAD CORE DATA
# ==================================================

db = cached_load_database()
matches = cached_load_matches()
assets = cached_load_assets()
available_stages = cached_available_stages()
current_stage = cached_current_stage()

stage_options = ["ALL"] + available_stages
default_stage_index = stage_options.index(current_stage) if current_stage in stage_options else 0

try:
    player_stats_for_options, _, _ = cached_player_stats(current_stage)
except Exception:
    player_stats_for_options = pd.DataFrame()

team_options = get_team_options(matches, assets, player_stats_for_options)


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Review Control")
st.sidebar.caption(f"Data Source: {get_data_source_label(db)}")

selected_stage = st.sidebar.selectbox(
    "Stage",
    stage_options,
    index=default_stage_index,
)

reviewer = st.sidebar.text_input(
    "Reviewer",
    value="",
    placeholder="이름 입력",
)

if st.sidebar.button("Refresh Google Sheet / Cache"):
    st.cache_data.clear()
    st.rerun()

with st.sidebar.expander("Data Source Debug"):
    if isinstance(db, dict) and "_DB_FILE" in db:
        st.dataframe(db["_DB_FILE"], use_container_width=True, hide_index=True)
    if isinstance(db, dict) and "_LOAD_ERRORS" in db and not db["_LOAD_ERRORS"].empty:
        st.warning("Google Sheet load errors")
        st.dataframe(db["_LOAD_ERRORS"], use_container_width=True, hide_index=True)


# ==================================================
# INPUT AREA
# ==================================================

st.subheader("Daily Research 생성")

if not team_options:
    st.warning("팀 데이터가 없습니다. Google Sheet / 01_TEAMS / 04_MATCHES / 14_ASSETS를 확인해주세요.")
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    event_name = st.text_input("Event Name", value="OWCS KOREA Stage 2")

with col2:
    broadcast_date = st.date_input("Broadcast Date", value=date.today())

with col3:
    match_count = st.selectbox("Match Count", [1, 2, 3, 4], index=2)

opening_note = st.text_area(
    "Opening Notes",
    value="",
    height=80,
    placeholder="오프닝에서 짚을 내용이 있으면 입력",
)

match_inputs = []

st.subheader("Today Matches")

for i in range(match_count):
    c1, c2, c3 = st.columns([2, 1, 2])

    with c1:
        team_a = st.selectbox(
            f"Match {i + 1} Team A",
            team_options,
            index=0,
            key=f"review_team_a_{i}",
        )
        show_team_logo(team_a, db, 70)

    with c2:
        st.markdown("### VS")

    with c3:
        team_b = st.selectbox(
            f"Match {i + 1} Team B",
            team_options,
            index=1 if len(team_options) > 1 else 0,
            key=f"review_team_b_{i}",
        )
        show_team_logo(team_b, db, 70)

    match_inputs.append((team_a, team_b))

st.divider()

invalid_matches = [idx + 1 for idx, (a, b) in enumerate(match_inputs) if a == b]

if invalid_matches:
    st.error(f"같은 팀이 선택된 매치가 있습니다: {invalid_matches}")
    st.stop()


# ==================================================
# GENERATE / SESSION STATE
# ==================================================

if "review_daily_doc" not in st.session_state:
    st.session_state["review_daily_doc"] = ""

if "review_match_inputs" not in st.session_state:
    st.session_state["review_match_inputs"] = tuple()

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn1:
    generate_clicked = st.button("Generate Review Pack", type="primary")

with col_btn2:
    clear_clicked = st.button("Clear")

with col_btn3:
    regenerate_each_clicked = st.button("Regenerate Match Packets")

if clear_clicked:
    st.session_state["review_daily_doc"] = ""
    st.session_state["review_match_inputs"] = tuple()
    st.rerun()

if generate_clicked:
    with st.spinner("Generating Daily Research..."):
        doc = cached_daily_doc(
            event_name=event_name,
            broadcast_date=str(broadcast_date),
            stage=selected_stage,
            match_inputs_tuple=tuple(match_inputs),
            opening_note=opening_note,
        )

    st.session_state["review_daily_doc"] = doc
    st.session_state["review_match_inputs"] = tuple(match_inputs)

if regenerate_each_clicked:
    lines = [
        "OWCS BROADCAST DAILY RESEARCH",
        "Version: V4.1 Internal Review Regenerated Match Packets",
        "",
        f"Event: {event_name}",
        f"Date: {broadcast_date}",
        f"Stage: {selected_stage}",
        f"Matches: {len(match_inputs)}",
        "",
        "[Today Match Order]",
    ]

    for idx, (team_a, team_b) in enumerate(match_inputs, start=1):
        lines.append(f"{idx}. {team_a} vs {team_b}")

    lines.append("")

    with st.spinner("Regenerating match packets..."):
        for idx, (team_a, team_b) in enumerate(match_inputs, start=1):
            lines.append(cached_match_packet(idx, team_a, team_b, selected_stage))
            lines.append("")

    lines += [
        "==================================================",
        "END OF DAILY RESEARCH",
        "==================================================",
    ]

    st.session_state["review_daily_doc"] = "\n".join(lines)
    st.session_state["review_match_inputs"] = tuple(match_inputs)


# ==================================================
# OUTPUT / REVIEW UI
# ==================================================

daily_doc = st.session_state.get("review_daily_doc", "")

if not daily_doc:
    st.info("Generate Review Pack 버튼을 누르면 내부 검수 화면이 생성됩니다.")
    st.stop()

intro_text, match_sections = split_daily_doc_sections(daily_doc)
saved_match_inputs = st.session_state.get("review_match_inputs", tuple(match_inputs))

st.divider()
st.header("Internal Review")

# Summary status board
review_rows = []
for idx, (team_a, team_b) in enumerate(saved_match_inputs, start=1):
    latest = get_latest_review(
        event_name,
        str(broadcast_date),
        selected_stage,
        idx,
        team_a,
        team_b,
    )
    review_rows.append(
        {
            "Match": idx,
            "Teams": f"{team_a} vs {team_b}",
            "Status": status_badge(latest.get("status", "초안") if latest else "초안"),
            "Reviewer": latest.get("reviewer", "") if latest else "",
            "Last Comment": latest.get("comment", "") if latest else "",
        }
    )

st.subheader("검수 현황")
st.dataframe(pd.DataFrame(review_rows), use_container_width=True, hide_index=True)

st.subheader("Today Overview")
with st.expander("TODAY STORYLINES / MATCH ORDER", expanded=True):
    st.text_area(
        "Overview",
        value=intro_text,
        height=360,
        key="overview_text_area",
    )

# Match cards
st.subheader("Match별 검수")

for idx, section in enumerate(match_sections, start=1):
    if idx <= len(saved_match_inputs):
        team_a, team_b = saved_match_inputs[idx - 1]
    else:
        team_a, team_b = "", ""

    latest = get_latest_review(
        event_name,
        str(broadcast_date),
        selected_stage,
        idx,
        team_a,
        team_b,
    )

    current_status = latest.get("status", "초안") if latest else "초안"
    current_comment = latest.get("comment", "") if latest else ""

    with st.expander(f"{status_badge(current_status)} · MATCH {idx} · {team_a} vs {team_b}", expanded=(idx == 1)):
        h1, h2, h3 = st.columns([2, 1, 2])
        with h1:
            show_team_logo(team_a, db, 90)
            st.markdown(f"### {team_a}")
        with h2:
            st.markdown("# VS")
        with h3:
            show_team_logo(team_b, db, 90)
            st.markdown(f"### {team_b}")

        st.text_area(
            f"MATCH {idx} Research",
            value=section["text"],
            height=700,
            key=f"match_text_{idx}",
        )

        r1, r2 = st.columns([1, 3])
        with r1:
            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0,
                key=f"status_{idx}",
            )
        with r2:
            comment = st.text_area(
                "Review Comment",
                value=current_comment,
                height=120,
                placeholder="수정 요청 / 확인 코멘트 입력",
                key=f"comment_{idx}",
            )

        save_clicked = st.button("Save Review", key=f"save_review_{idx}")

        if save_clicked:
            append_review_note(
                {
                    "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "event_name": event_name,
                    "broadcast_date": str(broadcast_date),
                    "stage": selected_stage,
                    "match_no": idx,
                    "team_a": team_a,
                    "team_b": team_b,
                    "status": status,
                    "reviewer": reviewer.strip(),
                    "comment": comment.strip(),
                }
            )
            st.success("검수 내용 저장 완료")
            st.rerun()

st.divider()

st.subheader("전체본 다운로드")
st.download_button(
    "Daily Research TXT 다운로드",
    data=daily_doc,
    file_name=f"{event_name}_{broadcast_date}_{selected_stage}_daily_research.txt",
    mime="text/plain",
)

notes_df = read_review_notes()
if not notes_df.empty:
    st.download_button(
        "Review Notes CSV 다운로드",
        data=notes_df.to_csv(index=False),
        file_name=f"{event_name}_{broadcast_date}_{selected_stage}_review_notes.csv",
        mime="text/csv",
    )

    with st.expander("Review Notes History"):
        st.dataframe(notes_df.sort_values("saved_at", ascending=False), use_container_width=True, hide_index=True)
