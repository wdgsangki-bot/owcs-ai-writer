import re
from pathlib import Path
import pandas as pd
import requests
from urllib.parse import quote
from io import StringIO


DATA_DIR = Path(__file__).parent / "data"

PLAYER_FILES = [
    DATA_DIR / "OWCS KR S1 players data.xlsx",
    DATA_DIR / "OWCS KR S2 players data.xlsx",
]

# ==================================================
# V4.0 GOOGLE SHEET CONFIG
# ==================================================

GOOGLE_SHEET_ID = "1H_05K75EinAgt1HmLQ3-in3R6N0wAI3vNfFITp1zDcA"

GOOGLE_SHEET_NAMES = [
    "01_TEAMS",
    "02_PLAYERS",
    "03_ROSTERS",
    "04_MATCHES",
    "05_MAPS",
    "06_STANDINGS",
    "07_STORYLINES",
    "08_BRACKETS",
    "09_DAY_SCHEDULE",
    "10_DAILY_ROSTER",
    "11_ALIASES",
    "13_MAP_TYPES",
    "14_ASSETS",
]

USE_GOOGLE_SHEETS_DEFAULT = True



# ==================================================
# V4.0 GOOGLE SHEET LOADERS
# ==================================================

def _read_google_sheet_csv(sheet_id, sheet_name, timeout=20):
    encoded_sheet = quote(str(sheet_name), safe="")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    from io import StringIO
    df = pd.read_csv(StringIO(response.text))
    df.columns = [str(c).strip() for c in df.columns]

    # Drop fully empty rows/columns caused by sheet formatting.
    df = df.dropna(how="all").copy()
    df = df.dropna(axis=1, how="all").copy()

    return df


def load_google_database(sheet_id=GOOGLE_SHEET_ID, sheet_names=None):
    if sheet_names is None:
        sheet_names = GOOGLE_SHEET_NAMES

    db = {}
    errors = []

    for sheet_name in sheet_names:
        try:
            df = _read_google_sheet_csv(sheet_id, sheet_name)
            db[sheet_name] = df
        except Exception as e:
            errors.append({"sheet": sheet_name, "error": str(e)})
            db[sheet_name] = pd.DataFrame()

    db["_DB_FILE"] = pd.DataFrame(
        {
            "source": ["GOOGLE_SHEET"],
            "sheet_id": [sheet_id],
            "url": [f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"],
        }
    )

    db["_LOAD_ERRORS"] = pd.DataFrame(errors)

    return db


def is_google_db_available(db):
    if not db:
        return False

    meta = db.get("_DB_FILE", pd.DataFrame())

    if meta.empty or "source" not in meta.columns:
        return False

    return str(meta.iloc[0].get("source", "")).upper() == "GOOGLE_SHEET"


def load_local_excel_database():
    db_file = find_database_file()

    if not db_file.exists():
        return {}

    xls = pd.ExcelFile(db_file)
    db = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(db_file, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        db[sheet] = df

    db["_DB_FILE"] = pd.DataFrame(
        {
            "source": ["LOCAL_XLSX"],
            "path": [str(db_file)],
        }
    )
    return db



# ==================================================
# V4.0B GOOGLE SHEET LOADERS
# ==================================================

def _read_google_sheet_csv(sheet_id, sheet_name, timeout=20):
    encoded_sheet = quote(str(sheet_name), safe="")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = [str(c).strip() for c in df.columns]

    df = df.dropna(how="all").copy()
    df = df.dropna(axis=1, how="all").copy()

    return df


def load_google_database(sheet_id=GOOGLE_SHEET_ID, sheet_names=None):
    if sheet_names is None:
        sheet_names = GOOGLE_SHEET_NAMES

    db = {}
    errors = []

    for sheet_name in sheet_names:
        try:
            df = _read_google_sheet_csv(sheet_id, sheet_name)
            db[sheet_name] = df
        except Exception as e:
            errors.append({"sheet": sheet_name, "error": str(e)})
            db[sheet_name] = pd.DataFrame()

    db["_DB_FILE"] = pd.DataFrame(
        {
            "source": ["GOOGLE_SHEET"],
            "sheet_id": [sheet_id],
            "url": [f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"],
        }
    )

    db["_LOAD_ERRORS"] = pd.DataFrame(errors)

    return db


def load_local_excel_database():
    db_file = find_database_file()

    if not db_file.exists():
        return {}

    xls = pd.ExcelFile(db_file)
    db = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(db_file, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        db[sheet] = df

    db["_DB_FILE"] = pd.DataFrame(
        {
            "source": ["LOCAL_XLSX"],
            "path": [str(db_file)],
        }
    )

    db["_LOAD_ERRORS"] = pd.DataFrame()

    return db

def find_database_file():
    files = list(DATA_DIR.glob("OWCS_AI_DATABASE*.xlsx"))
    if not files:
        return DATA_DIR / "OWCS_AI_DATABASE.xlsx"
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def clean_key(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", value)


def normalize_name(value):
    return clean_key(value)


def normalize_team(value):
    return clean_key(value)


def normalize_map(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().upper()
    value = value.replace("’", "'")
    return re.sub(r"[^A-Z0-9]", "", value)


def normalize_stage(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = text.replace(" ", "_")
    text = re.sub(r"[^A-Z0-9_]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def stage_sort_key(stage):
    text = normalize_stage(stage)
    year = 0
    stage_no = 0

    m_year = re.search(r"(20[0-9]{2})", text)
    if m_year:
        year = int(m_year.group(1))

    m_stage = re.search(r"STAGE_?([0-9]+)", text)
    if m_stage:
        stage_no = int(m_stage.group(1))

    return year * 100 + stage_no


def stage_filter_df(df, stage):
    if df.empty:
        return df

    if not stage or stage == "ALL":
        return df

    if "Stage" not in df.columns:
        return df

    stage_key = normalize_stage(stage)

    return df[
        df["Stage"].astype(str).str.contains(stage_key, case=False, na=False)
    ].copy()


def parse_score(value):
    if pd.isna(value):
        return None
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None


def parse_minutes(value):
    """
    OWCS 원본 Time 기준:
    07:09:00 -> 7분 9초 -> 7.15분
    """
    if pd.isna(value):
        return 0.0

    if hasattr(value, "hour") and hasattr(value, "minute") and hasattr(value, "second"):
        try:
            return float(value.hour) + float(value.minute) / 60 + float(value.second) / 3600
        except Exception:
            return 0.0

    text = str(value).strip()

    if text == "":
        return 0.0

    if ":" in text:
        parts = text.split(":")
        try:
            nums = [float(x) for x in parts]

            if len(nums) == 3:
                return nums[0] + nums[1] / 60 + nums[2] / 3600

            if len(nums) == 2:
                return nums[0] + nums[1] / 60
        except Exception:
            return 0.0

    try:
        return float(text)
    except Exception:
        return 0.0


def detect_stage_from_source(file_name, sheet_name=""):
    text = f"{file_name} {sheet_name}".upper()

    m = re.search(r"(20[0-9]{2})[_\s-]*KR[_\s-]*STAGE[_\s-]*([0-9]+)", text)
    if m:
        return f"{m.group(1)}_KR_STAGE{m.group(2)}"

    if "S1" in text or "STAGE1" in text or "STAGE 1" in text:
        return "2026_KR_STAGE1"

    if "S2" in text or "STAGE2" in text or "STAGE 2" in text:
        return "2026_KR_STAGE2"

    if "S3" in text or "STAGE3" in text or "STAGE 3" in text:
        return "2026_KR_STAGE3"

    return ""



def load_database(use_google=USE_GOOGLE_SHEETS_DEFAULT, sheet_id=GOOGLE_SHEET_ID):
    """
    V4.0B canonical database loader.
    Google Sheet first, local XLSX fallback second.
    The returned db must always contain _DB_FILE.source.
    """
    if use_google:
        try:
            db = load_google_database(sheet_id=sheet_id)

            loaded_count = len(
                [
                    k for k, v in db.items()
                    if not str(k).startswith("_")
                    and v is not None
                    and not v.empty
                ]
            )

            core_ok = (
                "01_TEAMS" in db and not db["01_TEAMS"].empty
                and "04_MATCHES" in db and not db["04_MATCHES"].empty
            )

            if core_ok or loaded_count >= 3:
                return db

        except Exception as e:
            # Keep fallback safe.
            pass

    db = load_local_excel_database()

    if "_DB_FILE" not in db or db["_DB_FILE"].empty:
        db["_DB_FILE"] = pd.DataFrame({"source": ["EMPTY_DB"]})
    elif "source" not in db["_DB_FILE"].columns:
        db["_DB_FILE"]["source"] = "LOCAL_XLSX"

    if "_LOAD_ERRORS" not in db:
        db["_LOAD_ERRORS"] = pd.DataFrame()

    return db

def get_sheet(db, sheet_name):
    return db.get(sheet_name, pd.DataFrame()).copy()


def load_alias_map(db):
    aliases = get_sheet(db, "11_ALIASES")

    if aliases.empty:
        return {}

    if "raw_name" not in aliases.columns or "canonical_name" not in aliases.columns:
        return {}

    alias_map = {}

    for _, row in aliases.iterrows():
        raw = normalize_name(row.get("raw_name"))
        canonical = normalize_name(row.get("canonical_name"))

        if raw and canonical:
            alias_map[raw] = canonical

    return alias_map


def apply_alias(value, alias_map):
    key = normalize_name(value)
    return alias_map.get(key, key)


def get_team_lookup(db):
    teams = get_sheet(db, "01_TEAMS")

    if teams.empty or "team_id" not in teams.columns:
        return pd.DataFrame(columns=["team_id_key", "Team", "official_name", "region"])

    team = teams.copy()
    team["team_id_key"] = team["team_id"].apply(normalize_team)

    if "short_name" in team.columns:
        team["Team"] = team["short_name"]
    elif "official_name" in team.columns:
        team["Team"] = team["official_name"]
    else:
        team["Team"] = team["team_id"]

    if "official_name" not in team.columns:
        team["official_name"] = team["Team"]

    if "region" not in team.columns:
        team["region"] = ""

    return team[["team_id_key", "Team", "official_name", "region"]].drop_duplicates()


def get_player_role_lookup(db):
    players = get_sheet(db, "02_PLAYERS")
    alias_map = load_alias_map(db)

    if players.empty or "player_id" not in players.columns:
        return pd.DataFrame(columns=["Player_Normalized", "role", "nationality"])

    p = players.copy()
    p["Player_Normalized"] = p["player_id"].apply(lambda x: apply_alias(x, alias_map))

    if "role" not in p.columns:
        p["role"] = ""

    if "nationality" not in p.columns:
        p["nationality"] = ""

    return p[["Player_Normalized", "role", "nationality"]].drop_duplicates()


def get_roster_history(db):
    rosters = get_sheet(db, "03_ROSTERS")
    alias_map = load_alias_map(db)

    if rosters.empty or "player_id" not in rosters.columns or "team_id" not in rosters.columns:
        return pd.DataFrame(
            columns=[
                "Stage",
                "Stage_Order",
                "season",
                "Player_Normalized",
                "player_id",
                "team_id",
                "Team",
                "role",
                "nationality",
            ]
        )

    r = rosters.copy()

    if "season" not in r.columns:
        r["season"] = ""

    r["Stage"] = r["season"].apply(normalize_stage)
    r["Player_Normalized"] = r["player_id"].apply(lambda x: apply_alias(x, alias_map))
    r["team_id_key"] = r["team_id"].apply(normalize_team)

    team_lookup = get_team_lookup(db)
    r = r.merge(team_lookup, on="team_id_key", how="left")

    if "Team" not in r.columns:
        r["Team"] = r["team_id"]

    r["Team"] = r["Team"].fillna(r["team_id"])

    role_lookup = get_player_role_lookup(db)
    r = r.merge(role_lookup, on="Player_Normalized", how="left")

    if "role" not in r.columns:
        r["role"] = ""

    if "nationality" not in r.columns:
        r["nationality"] = ""

    r["Stage_Order"] = r["Stage"].apply(stage_sort_key)

    return r[
        [
            "Stage",
            "Stage_Order",
            "season",
            "Player_Normalized",
            "player_id",
            "team_id",
            "Team",
            "role",
            "nationality",
        ]
    ].drop_duplicates()


def get_current_stage(db=None):
    if db is None:
        db = load_database()

    roster = get_roster_history(db)

    if roster.empty:
        return "2026_KR_STAGE2"

    kr = roster[
        roster["Stage"].str.contains("KR", case=False, na=False)
        &
        roster["Stage"].str.contains("2026", case=False, na=False)
    ].copy()

    if kr.empty:
        kr = roster.copy()

    kr = kr.sort_values("Stage_Order", ascending=False)

    if kr.empty:
        return "2026_KR_STAGE2"

    return kr.iloc[0]["Stage"]


def get_available_stages(db=None, include_raw=True):
    if db is None:
        db = load_database()

    stages = set()

    roster = get_roster_history(db)
    if not roster.empty:
        stages.update(roster["Stage"].dropna().astype(str).tolist())

    if include_raw:
        raw = load_raw_player_stats(db)
        if not raw.empty and "Stage" in raw.columns:
            stages.update(raw["Stage"].dropna().astype(str).tolist())

    stages = [s for s in stages if s]
    stages = sorted(stages, key=stage_sort_key)

    return stages


def load_raw_player_stats(db=None):
    if db is None:
        db = load_database()

    alias_map = load_alias_map(db)
    frames = []

    for file in PLAYER_FILES:
        if not file.exists():
            continue

        xls = pd.ExcelFile(file)

        for sheet in xls.sheet_names:
            raw = pd.read_excel(file, sheet_name=sheet)

            if raw.empty:
                continue

            raw.columns = [str(c).strip() for c in raw.columns]

            if "Player" not in raw.columns:
                continue

            raw["Source File"] = file.name
            raw["Source Sheet"] = sheet
            raw["Stage"] = detect_stage_from_source(file.name, sheet)
            raw["Stage"] = raw["Stage"].apply(normalize_stage)
            raw["Player_Normalized"] = raw["Player"].apply(lambda x: apply_alias(x, alias_map))
            raw["Minutes_Row"] = raw["Time"].apply(parse_minutes) if "Time" in raw.columns else 0.0

            for col in ["E", "A", "D", "DMG", "H", "MIT"]:
                if col not in raw.columns:
                    raw[col] = 0
                raw[col] = pd.to_numeric(raw[col], errors="coerce").fillna(0)

            frames.append(raw)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def load_players_with_team(db):
    roster = get_roster_history(db)

    if roster.empty:
        return pd.DataFrame(columns=["Player_Normalized", "Stage", "Roster_Team", "season", "team_id"])

    result = roster.copy()
    result = result.rename(columns={"Team": "Roster_Team"})

    return result[
        [
            "Player_Normalized",
            "Stage",
            "Roster_Team",
            "season",
            "team_id",
            "role",
            "nationality",
        ]
    ].drop_duplicates()


def add_per10_columns(grouped):
    grouped["Elims Per10"] = grouped.apply(
        lambda r: r["Elims"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )
    grouped["Assists Per10"] = grouped.apply(
        lambda r: r["Assists"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )
    grouped["Deaths Per10"] = grouped.apply(
        lambda r: r["Deaths"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )
    grouped["Damage Per10"] = grouped.apply(
        lambda r: r["Damage"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )
    grouped["Healing Per10"] = grouped.apply(
        lambda r: r["Healing"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )
    grouped["Mitigation Per10"] = grouped.apply(
        lambda r: r["Mitigation"] / r["Minutes"] * 10 if r["Minutes"] > 0 else 0,
        axis=1,
    )

    return grouped


def aggregate_player_stats(stage=None):
    db = load_database()
    raw = load_raw_player_stats(db)
    player_master = load_players_with_team(db)

    if raw.empty:
        return pd.DataFrame(), raw, player_master

    joined = raw.merge(
        player_master[
            [
                "Player_Normalized",
                "Stage",
                "Roster_Team",
                "season",
                "team_id",
                "role",
                "nationality",
            ]
        ],
        on=["Player_Normalized", "Stage"],
        how="left",
    )

    joined["Team"] = joined["Roster_Team"].fillna("UNKNOWN")
    joined["Join Status"] = joined["Roster_Team"].apply(
        lambda x: "MATCHED" if pd.notna(x) and str(x).strip() != "" else "UNKNOWN"
    )

    if "Roster_Team" in joined.columns:
        joined = joined.drop(columns=["Roster_Team"])

    joined = stage_filter_df(joined, stage)

    map_col = "Map" if "Map" in joined.columns else "Source Sheet"

    grouped = (
        joined.groupby(["Stage", "Player_Normalized", "Player", "Team"], as_index=False)
        .agg(
            Maps=(map_col, "nunique"),
            Minutes=("Minutes_Row", "sum"),
            Elims=("E", "sum"),
            Assists=("A", "sum"),
            Deaths=("D", "sum"),
            Damage=("DMG", "sum"),
            Healing=("H", "sum"),
            Mitigation=("MIT", "sum"),
        )
    )

    grouped = add_per10_columns(grouped)
    grouped = grouped.sort_values(["Stage", "Team", "Minutes"], ascending=[True, True, False])

    return grouped, joined, player_master


def get_player_movement_history(player_name=None, db=None):
    if db is None:
        db = load_database()

    roster = get_roster_history(db)

    if roster.empty:
        return pd.DataFrame(columns=["Player", "Movement", "Stages", "Current Team", "Team Count"])

    df = roster.copy()
    df = df[df["Stage"].str.contains("KR", case=False, na=False)].copy()
    df = df.sort_values(["Player_Normalized", "Stage_Order"])

    if player_name:
        key = normalize_name(player_name)
        df = df[df["Player_Normalized"] == key].copy()

    rows = []

    for player, g in df.groupby("Player_Normalized"):
        g = g.sort_values("Stage_Order")

        teams = []
        stages = []
        last_team = None

        for _, row in g.iterrows():
            team = row["Team"]
            stage = row["Stage"]

            if team != last_team:
                teams.append(team)
                stages.append(stage)
                last_team = team

        if not teams:
            continue

        rows.append(
            {
                "Player": player,
                "Movement": " → ".join(teams),
                "Stages": " / ".join(stages),
                "Current Team": teams[-1],
                "Team Count": len(set(teams)),
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    return result.sort_values(["Team Count", "Player"], ascending=[False, True])


def load_matches(db=None):
    if db is None:
        db = load_database()

    matches = get_sheet(db, "04_MATCHES")

    if matches.empty:
        return pd.DataFrame()

    for col in ["team_a", "team_b", "score_a", "score_b"]:
        if col not in matches.columns:
            matches[col] = None

    matches["team_a_key"] = matches["team_a"].apply(normalize_team)
    matches["team_b_key"] = matches["team_b"].apply(normalize_team)
    matches["score_a_num"] = matches["score_a"].apply(parse_score)
    matches["score_b_num"] = matches["score_b"].apply(parse_score)

    if "date" in matches.columns:
        matches["date"] = pd.to_datetime(matches["date"], errors="coerce")
    else:
        matches["date"] = pd.NaT

    if "tournament" in matches.columns:
        matches["Stage"] = matches["tournament"].apply(normalize_stage)
    else:
        matches["Stage"] = ""

    matches = matches.dropna(subset=["score_a_num", "score_b_num"]).copy()
    matches = matches[(matches["score_a_num"] + matches["score_b_num"]) > 0].copy()
    matches = matches[matches["score_a_num"] != matches["score_b_num"]].copy()

    matches["winner"] = matches.apply(
        lambda r: r["team_a"] if r["score_a_num"] > r["score_b_num"] else r["team_b"],
        axis=1,
    )
    matches["winner_key"] = matches["winner"].apply(normalize_team)

    return matches


def make_h2h_storyline(team_a, team_b, summary):
    if not summary:
        return f"{team_a}와 {team_b}의 상대 전적 데이터가 부족합니다."

    a_all = summary["team_a_wins"]
    b_all = summary["team_b_wins"]
    a_2026 = summary["team_a_wins_2026"]
    b_2026 = summary["team_b_wins_2026"]

    if a_all > b_all and a_2026 < b_2026:
        return (
            f"{team_a}는 통산 상대 전적에서는 {a_all}승 {b_all}패로 앞서 있지만, "
            f"2026년 맞대결에서는 {team_b}가 {b_2026}승 {a_2026}패로 흐름을 가져가고 있습니다. "
            f"오늘 경기는 {team_a}가 과거의 우위를 되찾을 수 있을지, "
            f"{team_b}가 최근 상대전적 우위를 이어갈지가 핵심입니다."
        )

    if b_all > a_all and b_2026 < a_2026:
        return (
            f"{team_b}는 통산 상대 전적에서는 {b_all}승 {a_all}패로 앞서 있지만, "
            f"2026년 맞대결에서는 {team_a}가 {a_2026}승 {b_2026}패로 반격하고 있습니다. "
            f"오늘 경기는 최근 흐름과 통산 우위가 충돌하는 매치업입니다."
        )

    leader = team_a if a_all > b_all else team_b if b_all > a_all else None

    if leader:
        return (
            f"{leader}가 통산 상대 전적에서 우위를 가지고 있습니다. "
            f"최근 맞대결 승자는 {summary['latest_winner']}이며, "
            f"현재 {summary['streak_team']}가 이 매치업에서 {summary['streak_count']}연승 중입니다."
        )

    return (
        f"두 팀의 통산 상대 전적은 팽팽합니다. "
        f"최근 승자는 {summary['latest_winner']}이며, "
        f"오늘 경기가 매치업 흐름을 바꿀 수 있는 분기점입니다."
    )


def get_h2h(team_a, team_b):
    db = load_database()
    matches = load_matches(db)

    if matches.empty:
        return {
            "matches": pd.DataFrame(),
            "recent5": pd.DataFrame(),
            "matches_2026": pd.DataFrame(),
            "summary": {},
            "storyline": "H2H 데이터가 없습니다.",
        }

    a_key = normalize_team(team_a)
    b_key = normalize_team(team_b)

    h2h = matches[
        ((matches["team_a_key"] == a_key) & (matches["team_b_key"] == b_key))
        |
        ((matches["team_a_key"] == b_key) & (matches["team_b_key"] == a_key))
    ].copy()

    if h2h.empty:
        return {
            "matches": h2h,
            "recent5": pd.DataFrame(),
            "matches_2026": pd.DataFrame(),
            "summary": {},
            "storyline": f"{team_a}와 {team_b}의 상대 전적 데이터가 없습니다.",
        }

    h2h = h2h.sort_values("date", ascending=False)

    a_wins = int((h2h["winner_key"] == a_key).sum())
    b_wins = int((h2h["winner_key"] == b_key).sum())

    h2h_2026 = h2h[h2h["date"].dt.year == 2026].copy()
    a_wins_2026 = int((h2h_2026["winner_key"] == a_key).sum())
    b_wins_2026 = int((h2h_2026["winner_key"] == b_key).sum())

    latest = h2h.iloc[0]
    latest_winner = latest["winner"]
    latest_winner_key = latest["winner_key"]

    streak_count = 0
    for _, row in h2h.iterrows():
        if row["winner_key"] == latest_winner_key:
            streak_count += 1
        else:
            break

    summary = {
        "team_a": team_a,
        "team_b": team_b,
        "team_a_wins": a_wins,
        "team_b_wins": b_wins,
        "total_matches": len(h2h),
        "team_a_wins_2026": a_wins_2026,
        "team_b_wins_2026": b_wins_2026,
        "total_matches_2026": len(h2h_2026),
        "latest_winner": latest_winner,
        "streak_team": latest_winner,
        "streak_count": streak_count,
    }

    return {
        "matches": h2h,
        "recent5": h2h.head(5).copy(),
        "matches_2026": h2h_2026,
        "summary": summary,
        "storyline": make_h2h_storyline(team_a, team_b, summary),
    }


def load_standings(db=None):
    if db is None:
        db = load_database()

    standings = get_sheet(db, "06_STANDINGS")

    if standings.empty:
        return pd.DataFrame()

    if "team_id" in standings.columns:
        standings["Team"] = standings["team_id"]
        standings["team_key"] = standings["team_id"].apply(normalize_team)
    else:
        standings["Team"] = ""
        standings["team_key"] = ""

    if "tournament" in standings.columns:
        standings["Stage"] = standings["tournament"].apply(normalize_stage)
        standings["Stage_Order"] = standings["Stage"].apply(stage_sort_key)
    else:
        standings["Stage"] = ""
        standings["Stage_Order"] = 0

    return standings


def get_team_standing(team_name, stage=None):
    db = load_database()
    standings = load_standings(db)

    if standings.empty:
        return None

    row = standings[standings["team_key"] == normalize_team(team_name)].copy()
    row = stage_filter_df(row, stage)

    if row.empty:
        return None

    row = row.sort_values("Stage_Order")
    return row.iloc[-1].to_dict()


def load_map_types(db=None):
    if db is None:
        db = load_database()

    mt = get_sheet(db, "13_MAP_TYPES")

    if mt.empty:
        return pd.DataFrame(columns=["map_name", "map_type", "map_key"])

    mt.columns = [str(c).strip() for c in mt.columns]

    if "map_name" not in mt.columns:
        return pd.DataFrame(columns=["map_name", "map_type", "map_key"])

    if "map_type" not in mt.columns:
        mt["map_type"] = "Unknown"

    mt["map_key"] = mt["map_name"].apply(normalize_map)

    return mt[["map_name", "map_type", "map_key"]].drop_duplicates()


def load_maps_with_match_info(db=None):
    if db is None:
        db = load_database()

    maps = get_sheet(db, "05_MAPS")
    matches = load_matches(db)
    map_types = load_map_types(db)

    if maps.empty:
        return pd.DataFrame()

    maps.columns = [str(c).strip() for c in maps.columns]

    for col in ["match_id", "map_name", "winner", "score_a", "score_b"]:
        if col not in maps.columns:
            maps[col] = None

    maps["map_key"] = maps["map_name"].apply(normalize_map)
    maps["winner_key"] = maps["winner"].apply(normalize_team)
    maps["score_a_num"] = maps["score_a"].apply(parse_score)
    maps["score_b_num"] = maps["score_b"].apply(parse_score)

    if not matches.empty and "match_id" in matches.columns:
        match_cols = [
            c for c in [
                "match_id",
                "date",
                "tournament",
                "Stage",
                "team_a",
                "team_b",
                "team_a_key",
                "team_b_key",
            ]
            if c in matches.columns
        ]
        maps = maps.merge(matches[match_cols], on="match_id", how="left")

    if not map_types.empty:
        maps = maps.merge(map_types[["map_key", "map_type"]], on="map_key", how="left")

    if "map_type" not in maps.columns:
        maps["map_type"] = "Unknown"

    maps["map_type"] = maps["map_type"].fillna("Unknown")

    maps = maps.dropna(subset=["winner"])
    maps = maps[maps["winner"].astype(str).str.strip() != ""].copy()

    if "date" in maps.columns:
        maps["date"] = pd.to_datetime(maps["date"], errors="coerce")
    else:
        maps["date"] = pd.NaT

    return maps


def _team_map_rows(team_name, maps_df):
    key = normalize_team(team_name)

    if maps_df.empty:
        return pd.DataFrame()

    return maps_df[
        (maps_df["team_a_key"] == key)
        |
        (maps_df["team_b_key"] == key)
    ].copy()


def get_team_map_stats(team_name, stage=None, db=None):
    if db is None:
        db = load_database()

    maps = load_maps_with_match_info(db)
    key = normalize_team(team_name)

    if maps.empty:
        empty = pd.DataFrame()
        return {"map_stats": empty, "type_stats": empty, "raw": empty}

    maps = stage_filter_df(maps, stage)

    team_maps = _team_map_rows(team_name, maps)

    if team_maps.empty:
        empty = pd.DataFrame()
        return {"map_stats": empty, "type_stats": empty, "raw": empty}

    team_maps["Result"] = team_maps["winner_key"].apply(lambda x: "W" if x == key else "L")
    map_count_col = "map_id" if "map_id" in team_maps.columns else "match_id"

    map_stats = (
        team_maps.groupby(["map_name", "map_type"], as_index=False)
        .agg(
            Maps=(map_count_col, "count"),
            Wins=("Result", lambda x: int((x == "W").sum())),
            Losses=("Result", lambda x: int((x == "L").sum())),
        )
    )

    map_stats["Win Rate"] = map_stats.apply(
        lambda r: r["Wins"] / r["Maps"] * 100 if r["Maps"] > 0 else 0,
        axis=1,
    )

    type_stats = (
        team_maps.groupby(["map_type"], as_index=False)
        .agg(
            Maps=(map_count_col, "count"),
            Wins=("Result", lambda x: int((x == "W").sum())),
            Losses=("Result", lambda x: int((x == "L").sum())),
        )
    )

    type_stats["Win Rate"] = type_stats.apply(
        lambda r: r["Wins"] / r["Maps"] * 100 if r["Maps"] > 0 else 0,
        axis=1,
    )

    map_stats = map_stats.sort_values(["Win Rate", "Maps"], ascending=[False, False])
    type_stats = type_stats.sort_values(["Win Rate", "Maps"], ascending=[False, False])

    return {
        "map_stats": map_stats,
        "type_stats": type_stats,
        "raw": team_maps,
    }


def get_map_h2h(team_a, team_b, stage=None, db=None):
    if db is None:
        db = load_database()

    maps = load_maps_with_match_info(db)

    if maps.empty:
        return pd.DataFrame(), pd.DataFrame()

    maps = stage_filter_df(maps, stage)

    a_key = normalize_team(team_a)
    b_key = normalize_team(team_b)

    h2h = maps[
        ((maps["team_a_key"] == a_key) & (maps["team_b_key"] == b_key))
        |
        ((maps["team_a_key"] == b_key) & (maps["team_b_key"] == a_key))
    ].copy()

    if h2h.empty:
        return h2h, pd.DataFrame()

    h2h["A_Result"] = h2h["winner_key"].apply(lambda x: "W" if x == a_key else "L")
    h2h["B_Result"] = h2h["winner_key"].apply(lambda x: "W" if x == b_key else "L")

    map_count_col = "map_id" if "map_id" in h2h.columns else "match_id"

    summary = (
        h2h.groupby(["map_name", "map_type"], as_index=False)
        .agg(
            Maps=(map_count_col, "count"),
            Team_A_Wins=("A_Result", lambda x: int((x == "W").sum())),
            Team_B_Wins=("B_Result", lambda x: int((x == "W").sum())),
        )
    )

    summary["Team_A_Win_Rate"] = summary.apply(
        lambda r: r["Team_A_Wins"] / r["Maps"] * 100 if r["Maps"] > 0 else 0,
        axis=1,
    )

    summary = summary.sort_values(["Maps", "Team_A_Win_Rate"], ascending=[False, False])

    return h2h.sort_values("date", ascending=False), summary


def get_current_map_streaks(team_name, stage=None, db=None):
    if db is None:
        db = load_database()

    maps = load_maps_with_match_info(db)
    key = normalize_team(team_name)

    if maps.empty:
        return pd.DataFrame()

    maps = stage_filter_df(maps, stage)

    team_maps = _team_map_rows(team_name, maps)

    if team_maps.empty:
        return pd.DataFrame()

    rows = []

    for map_name, g in team_maps.groupby("map_name"):
        g = g.sort_values("date", ascending=False)
        if g.empty:
            continue

        first_result = "W" if g.iloc[0]["winner_key"] == key else "L"
        streak = 0

        for _, row in g.iterrows():
            result = "W" if row["winner_key"] == key else "L"
            if result == first_result:
                streak += 1
            else:
                break

        rows.append(
            {
                "map_name": map_name,
                "map_type": g.iloc[0].get("map_type", "Unknown"),
                "Current Streak": f"{streak}{first_result}",
                "Streak Count": streak,
                "Streak Result": first_result,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    return result.sort_values(["Streak Count", "map_name"], ascending=[False, True])


def _format_type_stats(team_name, df):
    if df.empty:
        return f"{team_name}: 맵 타입 데이터 없음"

    lines = [f"{team_name}"]

    for _, r in df.head(5).iterrows():
        lines.append(
            f"- {r['map_type']}: {int(r['Wins'])}승 {int(r['Losses'])}패 / {r['Win Rate']:.1f}%"
        )

    return "\n".join(lines)


def _format_best_worst_maps(team_name, df):
    if df.empty:
        return f"{team_name}: 맵 데이터 없음"

    total_wins = int(df["Wins"].sum()) if "Wins" in df.columns else 0

    lines = [f"{team_name}"]

    if total_wins == 0:
        lines.append("Most Played / Struggle Maps")
        struggle = df.sort_values(["Maps", "Win Rate"], ascending=[False, True]).head(3)
        for _, r in struggle.iterrows():
            lines.append(
                f"- {r['map_name']} ({r['map_type']}): {int(r['Wins'])}승 {int(r['Losses'])}패 / {r['Win Rate']:.1f}%"
            )
        return "\n".join(lines)

    best = df[df["Wins"] > 0].sort_values(["Win Rate", "Maps"], ascending=[False, False]).head(3)
    worst = df.sort_values(["Win Rate", "Maps"], ascending=[True, False]).head(3)

    lines.append("Best Maps")
    for _, r in best.iterrows():
        lines.append(
            f"- {r['map_name']} ({r['map_type']}): {int(r['Wins'])}승 {int(r['Losses'])}패 / {r['Win Rate']:.1f}%"
        )

    lines.append("Worst Maps")
    for _, r in worst.iterrows():
        lines.append(
            f"- {r['map_name']} ({r['map_type']}): {int(r['Wins'])}승 {int(r['Losses'])}패 / {r['Win Rate']:.1f}%"
        )

    return "\n".join(lines)


def make_map_broadcast_note(team_a, team_b, a_stats, b_stats, h2h_summary):
    a_type = a_stats["type_stats"]
    b_type = b_stats["type_stats"]

    if a_type.empty or b_type.empty:
        return "맵 타입 데이터가 부족하므로 맵별 전적보다는 전체 상대전적 중심으로 풀어가는 것이 좋습니다."

    a_best = a_type.iloc[0]
    b_best = b_type.iloc[0]

    note = (
        f"{team_a}는 {a_best['map_type']}에서 {a_best['Win Rate']:.1f}% 승률, "
        f"{team_b}는 {b_best['map_type']}에서 {b_best['Win Rate']:.1f}% 승률이 가장 높습니다. "
    )

    if int(a_best["Wins"]) == 0:
        note = f"{team_a}는 아직 해당 스테이지에서 승리 맵이 없어 맵 선택 부담이 큽니다. " + note

    if int(b_best["Wins"]) == 0:
        note += f"{team_b}도 아직 승리 맵이 없어 초반 맵 결과가 중요합니다. "

    if not h2h_summary.empty:
        top = h2h_summary.iloc[0]
        note += (
            f"양 팀이 가장 자주 만난 맵은 {top['map_name']}이며, "
            f"이 맵에서는 {team_a} {int(top['Team_A_Wins'])}승, "
            f"{team_b} {int(top['Team_B_Wins'])}승 구도입니다. "
        )

    note += "맵 밴/픽 단계에서 어떤 맵 타입을 피하고 가져가느냐가 경기 흐름을 결정할 수 있습니다."

    return note


def make_map_factoids(team_a, team_b, stage=None):
    db = load_database()
    stage_text = normalize_stage(stage) if stage and stage != "ALL" else "ALL"

    a_stats = get_team_map_stats(team_a, stage, db)
    b_stats = get_team_map_stats(team_b, stage, db)

    h2h_raw, h2h_summary = get_map_h2h(team_a, team_b, stage, db)

    a_streaks = get_current_map_streaks(team_a, stage, db)
    b_streaks = get_current_map_streaks(team_b, stage, db)

    lines = [
        "MAP FACTOIDS",
        "",
        f"Stage: {stage_text}",
        f"{team_a} vs {team_b}",
        "",
        "[Map Type Win Rate]",
        _format_type_stats(team_a, a_stats["type_stats"]),
        "",
        _format_type_stats(team_b, b_stats["type_stats"]),
        "",
        "[Best / Worst Maps]",
        _format_best_worst_maps(team_a, a_stats["map_stats"]),
        "",
        _format_best_worst_maps(team_b, b_stats["map_stats"]),
        "",
        "[Head-to-Head Maps]",
    ]

    if h2h_summary.empty:
        lines.append("맵별 맞대결 데이터 없음")
    else:
        for _, r in h2h_summary.head(8).iterrows():
            lines.append(
                f"- {r['map_name']} ({r['map_type']}): "
                f"{team_a} {int(r['Team_A_Wins'])}승 / "
                f"{team_b} {int(r['Team_B_Wins'])}승 "
                f"(총 {int(r['Maps'])}맵)"
            )

    lines += ["", "[Current Map Streaks]"]

    if a_streaks.empty:
        lines.append(f"{team_a}: 연승/연패 데이터 없음")
    else:
        lines.append(f"{team_a}")
        for _, r in a_streaks.head(5).iterrows():
            result_text = "연승" if r["Streak Result"] == "W" else "연패"
            lines.append(f"- {r['map_name']} ({r['map_type']}): {int(r['Streak Count'])}{result_text}")

    if b_streaks.empty:
        lines.append(f"{team_b}: 연승/연패 데이터 없음")
    else:
        lines.append(f"{team_b}")
        for _, r in b_streaks.head(5).iterrows():
            result_text = "연승" if r["Streak Result"] == "W" else "연패"
            lines.append(f"- {r['map_name']} ({r['map_type']}): {int(r['Streak Count'])}{result_text}")

    lines += [
        "",
        "[Broadcast Notes]",
        make_map_broadcast_note(team_a, team_b, a_stats, b_stats, h2h_summary),
    ]

    return "\n".join(lines)


def get_top_players_for_team(team_name, stage=None, limit=3):
    player_stats, _, _ = aggregate_player_stats(stage=stage)

    if player_stats.empty:
        return pd.DataFrame()

    df = player_stats[
        player_stats["Team"].apply(normalize_team) == normalize_team(team_name)
    ].copy()

    if df.empty:
        return df

    return df.sort_values("Minutes", ascending=False).head(limit)


def format_standing_line(row):
    parts = []

    if "rank" in row and pd.notna(row["rank"]):
        parts.append(f"{int(row['rank'])}위")

    if "wins" in row and pd.notna(row["wins"]):
        parts.append(f"{int(row['wins'])}승")

    if "losses" in row and pd.notna(row["losses"]):
        parts.append(f"{int(row['losses'])}패")

    if "map_diff" in row and pd.notna(row["map_diff"]):
        parts.append(f"득실 {int(row['map_diff'])}")

    return " / ".join(parts) if parts else "순위 데이터 표시 컬럼 확인 필요"


def format_top_players(team_name, df):
    if df.empty:
        return f"{team_name}: 선수 스탯 데이터 없음"

    names = []

    for _, r in df.iterrows():
        names.append(
            f"{r['Player']} "
            f"({r['Minutes']:.1f}분, "
            f"E/10 {r['Elims Per10']:.1f}, "
            f"D/10 {r['Deaths Per10']:.1f})"
        )

    return f"{team_name}: " + " / ".join(names)


def make_broadcast_note(team_a, team_b, summary):
    if not summary:
        return f"{team_a}와 {team_b}의 직접 상대 전적이 부족하므로 순위와 최근 선수 지표 중심으로 풀어가는 것이 좋습니다."

    return make_h2h_storyline(team_a, team_b, summary)


def make_match_overview(team_a, team_b, stage=None):
    h2h = get_h2h(team_a, team_b)
    summary = h2h.get("summary", {})

    standing_a = get_team_standing(team_a, stage)
    standing_b = get_team_standing(team_b, stage)

    top_a = get_top_players_for_team(team_a, stage, 3)
    top_b = get_top_players_for_team(team_b, stage, 3)

    stage_text = normalize_stage(stage) if stage and stage != "ALL" else "ALL"

    lines = [
        "MATCH OVERVIEW",
        "",
        f"Stage: {stage_text}",
        f"{team_a} vs {team_b}",
        "",
    ]

    if summary:
        lines += [
            "[전체 상대 전적]",
            f"{team_a}: {summary['team_a_wins']}승",
            f"{team_b}: {summary['team_b_wins']}승",
            f"총 {summary['total_matches']}경기",
            "",
            "[2026 상대 전적]",
            f"{team_a}: {summary['team_a_wins_2026']}승",
            f"{team_b}: {summary['team_b_wins_2026']}승",
            f"총 {summary['total_matches_2026']}경기",
            "",
            "[최근 흐름]",
            f"최근 승자: {summary['latest_winner']}",
            f"현재 연승: {summary['streak_team']} {summary['streak_count']}연승",
            "",
        ]

    lines += [
        "[현재 순위]",
        f"{team_a}: {format_standing_line(standing_a) if standing_a else '순위 데이터 없음'}",
        f"{team_b}: {format_standing_line(standing_b) if standing_b else '순위 데이터 없음'}",
        "",
        "[Player To Watch]",
        format_top_players(team_a, top_a),
        format_top_players(team_b, top_b),
        "",
        "[Key Storyline]",
        h2h.get("storyline", "스토리라인 데이터 없음"),
        "",
        "[Broadcast Notes]",
        make_broadcast_note(team_a, team_b, summary),
    ]

    return "\n".join(lines)


def load_assets(db=None):
    if db is None:
        db = load_database()

    assets = get_sheet(db, "14_ASSETS")

    if assets.empty:
        return pd.DataFrame(columns=["entity_id", "logo_file", "entity_key"])

    assets.columns = [str(c).strip() for c in assets.columns]

    if "entity_id" not in assets.columns or "logo_file" not in assets.columns:
        return pd.DataFrame(columns=["entity_id", "logo_file", "entity_key"])

    assets["entity_key"] = assets["entity_id"].apply(normalize_team)

    return assets


def get_team_logo_path(team_id, db=None):
    if db is None:
        db = load_database()

    assets = load_assets(db)

    if assets.empty:
        return None

    team_key = normalize_team(team_id)

    row = assets[assets["entity_key"] == team_key]

    if row.empty:
        return None

    logo_file = str(row.iloc[0]["logo_file"]).strip()

    if not logo_file:
        return None

    logo_path = DATA_DIR.parent / "assets" / "teams" / logo_file

    if not logo_path.exists():
        return None

    return logo_path

# ==================================================
# V3.3D ADDITIVE HELPERS
# Existing functions above are intentionally untouched.
# ==================================================

def safe_get_col(row, col, default=""):
    try:
        if col in row and pd.notna(row[col]):
            return row[col]
    except Exception:
        pass
    return default


def resolve_logo_path_candidates(logo_file):
    if pd.isna(logo_file):
        return []

    logo_file = str(logo_file).strip()

    if not logo_file:
        return []

    candidates = []

    raw_path = Path(logo_file)

    if raw_path.is_absolute():
        candidates.append(raw_path)

    candidates += [
        DATA_DIR.parent / "assets" / "teams" / logo_file,
        DATA_DIR.parent / "assets" / logo_file,
        DATA_DIR / "assets" / "teams" / logo_file,
        DATA_DIR / "assets" / logo_file,
    ]

    # Case-insensitive fallback for macOS/Linux mismatch.
    expanded = []

    for path in candidates:
        expanded.append(path)

        parent = path.parent
        if parent.exists():
            try:
                target_name = path.name.lower()
                for p in parent.iterdir():
                    if p.name.lower() == target_name:
                        expanded.append(p)
            except Exception:
                pass

    deduped = []
    seen = set()

    for path in expanded:
        key = str(path)
        if key not in seen:
            deduped.append(path)
            seen.add(key)

    return deduped


def get_team_logo_path_v33d(team_id, db=None):
    if db is None:
        db = load_database()

    assets = load_assets(db)

    if assets.empty:
        return None

    team_key = normalize_team(team_id)

    row = assets[assets["entity_key"] == team_key]

    if row.empty:
        # Fallback: compare raw entity_id and normalized short/official names.
        if "entity_id" in assets.columns:
            row = assets[assets["entity_id"].apply(normalize_team) == team_key]

    if row.empty:
        return None

    logo_file = str(row.iloc[0]["logo_file"]).strip()

    for candidate in resolve_logo_path_candidates(logo_file):
        if candidate.exists():
            return candidate

    return None


def get_logo_debug_table(db=None):
    if db is None:
        db = load_database()

    assets = load_assets(db)

    if assets.empty:
        return pd.DataFrame(
            columns=[
                "entity_id",
                "entity_key",
                "logo_file",
                "resolved_path",
                "exists",
                "checked_paths",
            ]
        )

    rows = []

    for _, row in assets.iterrows():
        logo_file = str(row.get("logo_file", "")).strip()
        candidates = resolve_logo_path_candidates(logo_file)
        existing = [p for p in candidates if p.exists()]
        resolved = existing[0] if existing else None

        rows.append(
            {
                "entity_id": row.get("entity_id", ""),
                "entity_key": row.get("entity_key", ""),
                "logo_file": logo_file,
                "resolved_path": str(resolved) if resolved else "",
                "exists": bool(resolved),
                "checked_paths": " | ".join(str(p) for p in candidates),
            }
        )

    return pd.DataFrame(rows)


def aggregate_player_stats_with_roles(stage=None, db=None):
    # Additive wrapper: keep aggregate_player_stats() untouched.
    player_stats, joined_raw, player_master = aggregate_player_stats(stage=stage)

    if player_stats.empty:
        return player_stats, joined_raw, player_master

    result = player_stats.copy()

    if player_master is not None and not player_master.empty:
        role_cols = [
            c for c in ["Player_Normalized", "role", "nationality", "team_id", "season"]
            if c in player_master.columns
        ]

        if "Player_Normalized" in role_cols:
            role_map = player_master[role_cols].drop_duplicates(subset=["Player_Normalized"]).copy()
            merge_cols = [c for c in role_map.columns if c != "Stage"]

            result = result.merge(
                role_map[merge_cols],
                on="Player_Normalized",
                how="left",
                suffixes=("", "_master"),
            )

    if "role" not in result.columns:
        result["role"] = ""

    if "nationality" not in result.columns:
        result["nationality"] = ""

    result["Role"] = result["role"].fillna("").astype(str).str.upper().str.strip()
    result["Role"] = result["Role"].replace(
        {
            "DAMAGE": "DPS",
            "DMG": "DPS",
            "SUPPORT": "SUP",
            "HEALER": "SUP",
        }
    )

    return result, joined_raw, player_master


def get_role_based_players_to_watch(team_name, stage=None, db=None):
    player_stats, _, _ = aggregate_player_stats_with_roles(stage=stage, db=db)

    if player_stats.empty:
        return pd.DataFrame()

    df = player_stats[
        player_stats["Team"].apply(normalize_team) == normalize_team(team_name)
    ].copy()

    if df.empty:
        return df

    role_order = {"TANK": 1, "DPS": 2, "SUP": 3}
    rows = []

    for role in ["TANK", "DPS", "SUP"]:
        role_df = df[df["Role"] == role].copy()

        if role_df.empty:
            continue

        # Role-aware basic score.
        # TANK: survival + mitigation + minutes
        # DPS: elims/damage + low deaths + minutes
        # SUP: healing + assists + low deaths + minutes
        if role == "TANK":
            role_df["Watch Score"] = (
                role_df.get("Mitigation Per10", 0) * 0.001
                + role_df.get("Elims Per10", 0) * 1.0
                - role_df.get("Deaths Per10", 0) * 0.6
                + role_df.get("Minutes", 0) * 0.03
            )
        elif role == "DPS":
            role_df["Watch Score"] = (
                role_df.get("Elims Per10", 0) * 1.4
                + role_df.get("Damage Per10", 0) * 0.001
                - role_df.get("Deaths Per10", 0) * 0.7
                + role_df.get("Minutes", 0) * 0.03
            )
        else:
            role_df["Watch Score"] = (
                role_df.get("Healing Per10", 0) * 0.001
                + role_df.get("Assists Per10", 0) * 1.0
                - role_df.get("Deaths Per10", 0) * 0.8
                + role_df.get("Minutes", 0) * 0.03
            )

        role_df["Role Order"] = role_order.get(role, 99)
        rows.append(role_df.sort_values(["Watch Score", "Minutes"], ascending=[False, False]).head(1))

    if not rows:
        df["Watch Score"] = df.get("Minutes", 0)
        df["Role Order"] = 99
        return df.sort_values("Minutes", ascending=False).head(3)

    result = pd.concat(rows, ignore_index=True)
    result = result.sort_values(["Role Order", "Watch Score"], ascending=[True, False])

    return result


def format_role_based_players_to_watch(team_name, stage=None, db=None):
    df = get_role_based_players_to_watch(team_name, stage=stage, db=db)

    if df.empty:
        return f"{team_name}: 선수 데이터 없음"

    lines = [f"{team_name}"]

    for _, r in df.iterrows():
        role = str(r.get("Role", "")).strip() or "ROLE?"
        player = r.get("Player", r.get("Player_Normalized", "UNKNOWN"))

        lines.append(
            f"- [{role}] {player}: "
            f"{r.get('Minutes', 0):.1f}분, "
            f"E/10 {r.get('Elims Per10', 0):.1f}, "
            f"D/10 {r.get('Deaths Per10', 0):.1f}, "
            f"DMG/10 {r.get('Damage Per10', 0):.0f}, "
            f"H/10 {r.get('Healing Per10', 0):.0f}"
        )

    return "\n".join(lines)

# ==================================================
# V3.4A STORYLINE ENGINE HELPERS
# Existing functions above are intentionally untouched.
# ==================================================

MIN_PLAYER_MINUTES = 30


def _safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def get_role_rankings(stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    player_stats, _, _ = aggregate_player_stats_with_roles(stage=stage, db=db)

    if player_stats.empty:
        return pd.DataFrame()

    df = player_stats.copy()
    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce").fillna(0)
    df = df[df["Minutes"] >= min_minutes].copy()

    if df.empty:
        return df

    if "Role" not in df.columns:
        df["Role"] = df.get("role", "").fillna("").astype(str).str.upper()

    df["Role"] = df["Role"].fillna("").astype(str).str.upper().replace(
        {
            "DAMAGE": "DPS",
            "DMG": "DPS",
            "SUPPORT": "SUP",
            "HEALER": "SUP",
        }
    )

    rank_specs = [
        ("Elims Per10", False, "Elims Rank"),
        ("Deaths Per10", True, "Survival Rank"),
        ("Damage Per10", False, "Damage Rank"),
        ("Healing Per10", False, "Healing Rank"),
        ("Mitigation Per10", False, "Mitigation Rank"),
        ("Assists Per10", False, "Assists Rank"),
    ]

    for metric, ascending, rank_col in rank_specs:
        if metric not in df.columns:
            df[metric] = 0

        df[rank_col] = (
            df.groupby("Role")[metric]
            .rank(method="min", ascending=ascending)
            .fillna(999)
            .astype(int)
        )

    return df


def get_player_rank_context(player_name, team_name=None, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    rankings = get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)

    if rankings.empty:
        return {}

    player_key = normalize_name(player_name)

    row = rankings[rankings["Player_Normalized"] == player_key].copy()

    if row.empty and "Player" in rankings.columns:
        row = rankings[rankings["Player"].apply(normalize_name) == player_key].copy()

    if team_name and not row.empty:
        team_filtered = row[row["Team"].apply(normalize_team) == normalize_team(team_name)].copy()
        if not team_filtered.empty:
            row = team_filtered

    if row.empty:
        return {}

    r = row.sort_values("Minutes", ascending=False).iloc[0]
    role = str(r.get("Role", "")).upper().strip()

    role_total = int((rankings["Role"] == role).sum()) if role else len(rankings)

    return {
        "Player": r.get("Player", player_name),
        "Team": r.get("Team", team_name or ""),
        "Role": role,
        "Role Total": role_total,
        "Minutes": _safe_float(r.get("Minutes", 0)),
        "Elims Per10": _safe_float(r.get("Elims Per10", 0)),
        "Deaths Per10": _safe_float(r.get("Deaths Per10", 0)),
        "Damage Per10": _safe_float(r.get("Damage Per10", 0)),
        "Healing Per10": _safe_float(r.get("Healing Per10", 0)),
        "Mitigation Per10": _safe_float(r.get("Mitigation Per10", 0)),
        "Assists Per10": _safe_float(r.get("Assists Per10", 0)),
        "Elims Rank": _safe_int(r.get("Elims Rank", 999)),
        "Survival Rank": _safe_int(r.get("Survival Rank", 999)),
        "Damage Rank": _safe_int(r.get("Damage Rank", 999)),
        "Healing Rank": _safe_int(r.get("Healing Rank", 999)),
        "Mitigation Rank": _safe_int(r.get("Mitigation Rank", 999)),
        "Assists Rank": _safe_int(r.get("Assists Rank", 999)),
    }


def get_role_based_players_to_watch_v34(team_name, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    rankings = get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)

    if rankings.empty:
        # Fallback to old function if sample filter removes everything.
        return get_role_based_players_to_watch(team_name, stage=stage, db=db)

    df = rankings[
        rankings["Team"].apply(normalize_team) == normalize_team(team_name)
    ].copy()

    if df.empty:
        return df

    role_order = {"TANK": 1, "DPS": 2, "SUP": 3}
    rows = []

    for role in ["TANK", "DPS", "SUP"]:
        role_df = df[df["Role"] == role].copy()

        if role_df.empty:
            continue

        if role == "TANK":
            role_df["Watch Score"] = (
                role_df.get("Mitigation Per10", 0) * 0.001
                + role_df.get("Elims Per10", 0) * 1.0
                - role_df.get("Deaths Per10", 0) * 0.8
                + role_df.get("Minutes", 0) * 0.02
            )
        elif role == "DPS":
            role_df["Watch Score"] = (
                role_df.get("Elims Per10", 0) * 1.5
                + role_df.get("Damage Per10", 0) * 0.001
                - role_df.get("Deaths Per10", 0) * 0.7
                + role_df.get("Minutes", 0) * 0.02
            )
        else:
            role_df["Watch Score"] = (
                role_df.get("Healing Per10", 0) * 0.001
                + role_df.get("Assists Per10", 0) * 1.2
                - role_df.get("Deaths Per10", 0) * 0.8
                + role_df.get("Minutes", 0) * 0.02
            )

        role_df["Role Order"] = role_order.get(role, 99)
        rows.append(role_df.sort_values(["Watch Score", "Minutes"], ascending=[False, False]).head(1))

    if not rows:
        return pd.DataFrame()

    result = pd.concat(rows, ignore_index=True)
    result = result.sort_values(["Role Order", "Watch Score"], ascending=[True, False])

    return result


def format_role_based_players_to_watch_v34(team_name, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    df = get_role_based_players_to_watch_v34(team_name, stage=stage, min_minutes=min_minutes, db=db)

    if df.empty:
        return f"{team_name}: 선수 데이터 없음 또는 최소 출전시간 {min_minutes}분 이상 선수 없음"

    lines = [f"{team_name}"]

    for _, r in df.iterrows():
        role = str(r.get("Role", "")).strip() or "ROLE?"
        player = r.get("Player", r.get("Player_Normalized", "UNKNOWN"))
        role_total = int((get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)["Role"] == role).sum())

        if role == "TANK":
            rank_text = (
                f"생존력 {int(r.get('Survival Rank', 999))}/{role_total}, "
                f"MIT/10 {r.get('Mitigation Per10', 0):.0f}"
            )
        elif role == "DPS":
            rank_text = (
                f"화력 {int(r.get('Damage Rank', 999))}/{role_total}, "
                f"E/10 {r.get('Elims Per10', 0):.1f}"
            )
        elif role == "SUP":
            rank_text = (
                f"힐량 {int(r.get('Healing Rank', 999))}/{role_total}, "
                f"A/10 {r.get('Assists Per10', 0):.1f}"
            )
        else:
            rank_text = f"E/10 {r.get('Elims Per10', 0):.1f}"

        lines.append(
            f"- [{role}] {player}: "
            f"{r.get('Minutes', 0):.1f}분, "
            f"{rank_text}, "
            f"D/10 {r.get('Deaths Per10', 0):.1f}"
        )

    return "\n".join(lines)


def make_player_storyline(team_name, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    watch = get_role_based_players_to_watch_v34(team_name, stage=stage, min_minutes=min_minutes, db=db)

    if watch.empty:
        return f"{team_name}: 최소 출전시간 {min_minutes}분 이상 기준 Player Storyline 데이터 없음"

    lines = [f"{team_name} Player Storylines"]

    for _, r in watch.iterrows():
        role = str(r.get("Role", "")).upper()
        player = r.get("Player", r.get("Player_Normalized", "UNKNOWN"))
        role_total = int((get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)["Role"] == role).sum())

        if role == "TANK":
            lines.append(
                f"- {player}: {team_name}의 탱커 핵심. "
                f"Deaths/10 {r.get('Deaths Per10', 0):.1f}, 생존력 순위 {int(r.get('Survival Rank', 999))}/{role_total}. "
                f"탱커 싸움에서 먼저 무너지지 않는지가 핵심입니다."
            )
        elif role == "DPS":
            lines.append(
                f"- {player}: {team_name}의 주요 화력 포인트. "
                f"E/10 {r.get('Elims Per10', 0):.1f}, DMG/10 {r.get('Damage Per10', 0):.0f}. "
                f"첫 교전 킬 생산력이 경기 템포를 좌우할 수 있습니다."
            )
        elif role == "SUP":
            lines.append(
                f"- {player}: 서포트 안정성의 중심. "
                f"H/10 {r.get('Healing Per10', 0):.0f}, D/10 {r.get('Deaths Per10', 0):.1f}. "
                f"후방 생존과 유지력이 장기전의 관전 포인트입니다."
            )
        else:
            lines.append(
                f"- {player}: {r.get('Minutes', 0):.1f}분 출전, E/10 {r.get('Elims Per10', 0):.1f}."
            )

    return "\n".join(lines)


def get_match_importance(team_a, team_b, stage=None, db=None):
    h2h = get_h2h(team_a, team_b)
    summary = h2h.get("summary", {})

    standing_a = get_team_standing(team_a, stage)
    standing_b = get_team_standing(team_b, stage)

    score = 0
    reasons = []

    if summary:
        total = int(summary.get("total_matches", 0))
        a_w = int(summary.get("team_a_wins", 0))
        b_w = int(summary.get("team_b_wins", 0))

        if total >= 5:
            score += 2
            reasons.append(f"상대전적 표본 {total}경기")

        if abs(a_w - b_w) <= 1 and total >= 3:
            score += 3
            reasons.append(f"상대전적 접전 구도({team_a} {a_w}승 / {team_b} {b_w}승)")

        if int(summary.get("streak_count", 0)) >= 2:
            score += 1
            reasons.append(f"{summary.get('streak_team')} {summary.get('streak_count')}연승 흐름")

        if int(summary.get("total_matches_2026", 0)) >= 2:
            score += 1
            reasons.append("2026 시즌 맞대결 데이터 존재")
    else:
        reasons.append("공식 맞대결 데이터 부족")

    for team, standing in [(team_a, standing_a), (team_b, standing_b)]:
        if standing:
            rank = standing.get("rank")
            wins = standing.get("wins")
            if pd.notna(rank):
                rank_int = _safe_int(rank, 99)
                if rank_int <= 3:
                    score += 2
                    reasons.append(f"{team} 상위권 순위({rank_int}위)")
                elif rank_int <= 6:
                    score += 1
                    reasons.append(f"{team} 중위권 경쟁({rank_int}위)")
            if pd.notna(wins) and _safe_int(wins, 0) >= 3:
                score += 1
                reasons.append(f"{team} 누적 {int(wins)}승")

    if score >= 8:
        label = "MATCH OF THE DAY"
    elif score >= 5:
        label = "HIGH"
    elif score >= 3:
        label = "MEDIUM"
    else:
        label = "LOW"

    return {
        "label": label,
        "score": score,
        "reasons": reasons[:5],
        "summary": summary,
    }


def format_match_importance(team_a, team_b, stage=None, db=None):
    importance = get_match_importance(team_a, team_b, stage=stage, db=db)

    lines = [
        "[Match Importance]",
        f"- Grade: {importance['label']}",
        f"- Score: {importance['score']}",
    ]

    if importance["reasons"]:
        lines.append("- Reasons:")
        for reason in importance["reasons"]:
            lines.append(f"  · {reason}")

    return "\n".join(lines)


def make_match_talking_points(team_a, team_b, stage=None, db=None):
    h2h = get_h2h(team_a, team_b)
    summary = h2h.get("summary", {})
    importance = get_match_importance(team_a, team_b, stage=stage, db=db)

    points = []

    if summary:
        points.append(
            f"상대전적은 {team_a} {summary['team_a_wins']}승 / {team_b} {summary['team_b_wins']}승 구도."
        )
        points.append(
            f"최근 맞대결 승자는 {summary['latest_winner']}, 현재 {summary['streak_team']} {summary['streak_count']}연승."
        )
    else:
        points.append("공식 맞대결 데이터가 부족해 순위, 최근 폼, 선수 지표 중심으로 풀어갈 경기.")

    points.append(f"경기 중요도는 {importance['label']} 등급.")

    for team in [team_a, team_b]:
        watch = get_role_based_players_to_watch_v34(team, stage=stage, db=db)
        if not watch.empty:
            names = []
            for _, r in watch.iterrows():
                names.append(f"{r.get('Player')}({r.get('Role')})")
            points.append(f"{team} 체크 포인트: " + ", ".join(names))

    points = points[:6]

    lines = ["[Talking Points]"]
    for idx, point in enumerate(points, start=1):
        lines.append(f"{idx}. {point}")

    return "\n".join(lines)


def make_today_storylines(match_inputs, stage=None, db=None):
    rows = []

    for idx, item in enumerate(match_inputs):
        team_a, team_b = item
        if not team_a or not team_b or team_a == team_b:
            continue

        importance = get_match_importance(team_a, team_b, stage=stage, db=db)
        summary = importance.get("summary", {})

        if summary:
            if importance["label"] in ["MATCH OF THE DAY", "HIGH"]:
                title = f"{team_a} vs {team_b} 핵심 매치업"
            elif abs(summary.get("team_a_wins", 0) - summary.get("team_b_wins", 0)) <= 1:
                title = f"{team_a}-{team_b} 접전 구도"
            else:
                title = f"{team_a} vs {team_b} 흐름 체크"
            body = (
                f"상대전적 {team_a} {summary.get('team_a_wins', 0)}승 / "
                f"{team_b} {summary.get('team_b_wins', 0)}승. "
                f"최근 승자는 {summary.get('latest_winner')}이며, "
                f"오늘 결과가 매치업 흐름을 바꿀 수 있습니다."
            )
        else:
            title = f"{team_a} vs {team_b} 첫 구도 확인"
            body = (
                "직접 상대전적 데이터가 부족한 경기입니다. "
                "순위, 최근 폼, 역할별 핵심 선수 지표를 중심으로 풀어가는 것이 좋습니다."
            )

        rows.append(
            {
                "match_no": idx + 1,
                "team_a": team_a,
                "team_b": team_b,
                "importance": importance["label"],
                "score": importance["score"],
                "title": title,
                "body": body,
                "reasons": importance["reasons"],
            }
        )

    rows = sorted(rows, key=lambda x: x["score"], reverse=True)

    lines = [
        "==================================================",
        "TODAY STORYLINES",
        "==================================================",
        "",
    ]

    if not rows:
        lines.append("오늘의 스토리라인 생성 데이터 없음")
        return "\n".join(lines)

    for idx, row in enumerate(rows[:5], start=1):
        lines.append(f"{idx}. {row['title']}")
        lines.append(f"- Match {row['match_no']}: {row['team_a']} vs {row['team_b']}")
        lines.append(f"- Importance: {row['importance']}")
        lines.append(f"- {row['body']}")
        if row["reasons"]:
            lines.append("- 근거: " + " / ".join(row["reasons"][:3]))
        lines.append("")

    return "\n".join(lines)


def make_storyline_match_packet(team_a, team_b, stage=None, match_no=None, db=None):
    header_no = f"MATCH {match_no}" if match_no is not None else "MATCH"

    h2h = get_h2h(team_a, team_b)
    h2h_summary = h2h.get("summary", {})

    lines = [
        "==================================================",
        header_no,
        f"{team_a} vs {team_b}",
        "==================================================",
        "",
        format_match_importance(team_a, team_b, stage=stage, db=db),
        "",
    ]

    if h2h_summary:
        lines += [
            "[H2H Summary]",
            f"- 전체 상대 전적: {team_a} {h2h_summary['team_a_wins']}승 / {team_b} {h2h_summary['team_b_wins']}승",
            f"- 2026 상대 전적: {team_a} {h2h_summary['team_a_wins_2026']}승 / {team_b} {h2h_summary['team_b_wins_2026']}승",
            f"- 최근 승자: {h2h_summary['latest_winner']}",
            f"- 현재 흐름: {h2h_summary['streak_team']} {h2h_summary['streak_count']}연승",
            "",
        ]
    else:
        lines += [
            "[H2H Summary]",
            h2h.get("storyline", "H2H 데이터 없음"),
            "",
        ]

    lines += [
        "[Player Storylines]",
        make_player_storyline(team_a, stage=stage, db=db),
        "",
        make_player_storyline(team_b, stage=stage, db=db),
        "",
        "[Role-Based Player To Watch]",
        format_role_based_players_to_watch_v34(team_a, stage=stage, db=db),
        "",
        format_role_based_players_to_watch_v34(team_b, stage=stage, db=db),
        "",
        make_match_talking_points(team_a, team_b, stage=stage, db=db),
        "",
    ]

    try:
        map_factoids = make_map_factoids(team_a, team_b, stage=stage)
        map_note = ""
        if "[Broadcast Notes]" in map_factoids:
            map_note = map_factoids.split("[Broadcast Notes]", 1)[-1].strip()
        lines += [
            "[Map Storyline]",
            map_note if map_note else "맵 스토리라인 데이터 없음",
            "",
        ]
    except Exception as e:
        lines += [
            "[Map Storyline]",
            f"맵 스토리라인 생성 실패: {e}",
            "",
        ]

    return "\n".join(lines)

# ==================================================
# V3.4B FAST STORYLINE HELPERS
# Existing functions above are intentionally untouched.
# ==================================================

def get_role_based_players_to_watch_fast(team_name, rankings_df=None, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)

    if rankings_df is None or rankings_df.empty:
        return pd.DataFrame()

    df = rankings_df[
        rankings_df["Team"].apply(normalize_team) == normalize_team(team_name)
    ].copy()

    if df.empty:
        return df

    role_order = {"TANK": 1, "DPS": 2, "SUP": 3}
    rows = []

    for role in ["TANK", "DPS", "SUP"]:
        role_df = df[df["Role"] == role].copy()

        if role_df.empty:
            continue

        if role == "TANK":
            role_df["Watch Score"] = (
                role_df.get("Mitigation Per10", 0) * 0.001
                + role_df.get("Elims Per10", 0) * 1.0
                - role_df.get("Deaths Per10", 0) * 0.8
                + role_df.get("Minutes", 0) * 0.02
            )
        elif role == "DPS":
            role_df["Watch Score"] = (
                role_df.get("Elims Per10", 0) * 1.5
                + role_df.get("Damage Per10", 0) * 0.001
                - role_df.get("Deaths Per10", 0) * 0.7
                + role_df.get("Minutes", 0) * 0.02
            )
        else:
            role_df["Watch Score"] = (
                role_df.get("Healing Per10", 0) * 0.001
                + role_df.get("Assists Per10", 0) * 1.2
                - role_df.get("Deaths Per10", 0) * 0.8
                + role_df.get("Minutes", 0) * 0.02
            )

        role_df["Role Order"] = role_order.get(role, 99)
        rows.append(role_df.sort_values(["Watch Score", "Minutes"], ascending=[False, False]).head(1))

    if not rows:
        return pd.DataFrame()

    result = pd.concat(rows, ignore_index=True)
    return result.sort_values(["Role Order", "Watch Score"], ascending=[True, False])


def format_role_based_players_to_watch_fast(team_name, rankings_df=None, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)

    df = get_role_based_players_to_watch_fast(
        team_name,
        rankings_df=rankings_df,
        stage=stage,
        min_minutes=min_minutes,
        db=db,
    )

    if df.empty:
        return f"{team_name}: 선수 데이터 없음 또는 최소 출전시간 {min_minutes}분 이상 선수 없음"

    role_totals = rankings_df.groupby("Role").size().to_dict() if rankings_df is not None and not rankings_df.empty else {}

    lines = [f"{team_name}"]

    for _, r in df.iterrows():
        role = str(r.get("Role", "")).strip() or "ROLE?"
        player = r.get("Player", r.get("Player_Normalized", "UNKNOWN"))
        role_total = int(role_totals.get(role, 0)) if role else 0

        if role == "TANK":
            rank_text = (
                f"생존력 {int(r.get('Survival Rank', 999))}/{role_total}, "
                f"MIT/10 {r.get('Mitigation Per10', 0):.0f}"
            )
        elif role == "DPS":
            rank_text = (
                f"화력 {int(r.get('Damage Rank', 999))}/{role_total}, "
                f"E/10 {r.get('Elims Per10', 0):.1f}"
            )
        elif role == "SUP":
            rank_text = (
                f"힐량 {int(r.get('Healing Rank', 999))}/{role_total}, "
                f"A/10 {r.get('Assists Per10', 0):.1f}"
            )
        else:
            rank_text = f"E/10 {r.get('Elims Per10', 0):.1f}"

        lines.append(
            f"- [{role}] {player}: "
            f"{r.get('Minutes', 0):.1f}분, "
            f"{rank_text}, "
            f"D/10 {r.get('Deaths Per10', 0):.1f}"
        )

    return "\n".join(lines)


def make_player_storyline_fast(team_name, rankings_df=None, stage=None, min_minutes=MIN_PLAYER_MINUTES, db=None):
    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=min_minutes, db=db)

    watch = get_role_based_players_to_watch_fast(
        team_name,
        rankings_df=rankings_df,
        stage=stage,
        min_minutes=min_minutes,
        db=db,
    )

    if watch.empty:
        return f"{team_name}: 최소 출전시간 {min_minutes}분 이상 기준 Player Storyline 데이터 없음"

    role_totals = rankings_df.groupby("Role").size().to_dict() if rankings_df is not None and not rankings_df.empty else {}

    lines = [f"{team_name} Player Storylines"]

    for _, r in watch.iterrows():
        role = str(r.get("Role", "")).upper()
        player = r.get("Player", r.get("Player_Normalized", "UNKNOWN"))
        role_total = int(role_totals.get(role, 0)) if role else 0

        if role == "TANK":
            lines.append(
                f"- {player}: {team_name}의 탱커 핵심. "
                f"Deaths/10 {r.get('Deaths Per10', 0):.1f}, 생존력 순위 {int(r.get('Survival Rank', 999))}/{role_total}. "
                f"탱커 싸움에서 먼저 무너지지 않는지가 핵심입니다."
            )
        elif role == "DPS":
            lines.append(
                f"- {player}: {team_name}의 주요 화력 포인트. "
                f"E/10 {r.get('Elims Per10', 0):.1f}, DMG/10 {r.get('Damage Per10', 0):.0f}. "
                f"첫 교전 킬 생산력이 경기 템포를 좌우할 수 있습니다."
            )
        elif role == "SUP":
            lines.append(
                f"- {player}: 서포트 안정성의 중심. "
                f"H/10 {r.get('Healing Per10', 0):.0f}, D/10 {r.get('Deaths Per10', 0):.1f}. "
                f"후방 생존과 유지력이 장기전의 관전 포인트입니다."
            )
        else:
            lines.append(
                f"- {player}: {r.get('Minutes', 0):.1f}분 출전, E/10 {r.get('Elims Per10', 0):.1f}."
            )

    return "\n".join(lines)


def make_match_talking_points_fast(team_a, team_b, stage=None, rankings_df=None, db=None):
    h2h = get_h2h(team_a, team_b)
    summary = h2h.get("summary", {})
    importance = get_match_importance(team_a, team_b, stage=stage, db=db)

    points = []

    if summary:
        points.append(
            f"상대전적은 {team_a} {summary['team_a_wins']}승 / {team_b} {summary['team_b_wins']}승 구도."
        )
        points.append(
            f"최근 맞대결 승자는 {summary['latest_winner']}, 현재 {summary['streak_team']} {summary['streak_count']}연승."
        )
    else:
        points.append("공식 맞대결 데이터가 부족해 순위, 최근 폼, 선수 지표 중심으로 풀어갈 경기.")

    points.append(f"경기 중요도는 {importance['label']} 등급.")

    for team in [team_a, team_b]:
        watch = get_role_based_players_to_watch_fast(team, rankings_df=rankings_df, stage=stage, db=db)
        if not watch.empty:
            names = []
            for _, r in watch.iterrows():
                names.append(f"{r.get('Player')}({r.get('Role')})")
            points.append(f"{team} 체크 포인트: " + ", ".join(names))

    points = points[:6]

    lines = ["[Talking Points]"]
    for idx, point in enumerate(points, start=1):
        lines.append(f"{idx}. {point}")

    return "\n".join(lines)


def make_storyline_match_packet_fast(team_a, team_b, stage=None, match_no=None, rankings_df=None, db=None, include_map=True):
    header_no = f"MATCH {match_no}" if match_no is not None else "MATCH"

    h2h = get_h2h(team_a, team_b)
    h2h_summary = h2h.get("summary", {})

    lines = [
        "==================================================",
        header_no,
        f"{team_a} vs {team_b}",
        "==================================================",
        "",
        format_match_importance(team_a, team_b, stage=stage, db=db),
        "",
    ]

    if h2h_summary:
        lines += [
            "[H2H Summary]",
            f"- 전체 상대 전적: {team_a} {h2h_summary['team_a_wins']}승 / {team_b} {h2h_summary['team_b_wins']}승",
            f"- 2026 상대 전적: {team_a} {h2h_summary['team_a_wins_2026']}승 / {team_b} {h2h_summary['team_b_wins_2026']}승",
            f"- 최근 승자: {h2h_summary['latest_winner']}",
            f"- 현재 흐름: {h2h_summary['streak_team']} {h2h_summary['streak_count']}연승",
            "",
        ]
    else:
        lines += [
            "[H2H Summary]",
            h2h.get("storyline", "H2H 데이터 없음"),
            "",
        ]

    lines += [
        "[Player Storylines]",
        make_player_storyline_fast(team_a, rankings_df=rankings_df, stage=stage, db=db),
        "",
        make_player_storyline_fast(team_b, rankings_df=rankings_df, stage=stage, db=db),
        "",
        "[Role-Based Player To Watch]",
        format_role_based_players_to_watch_fast(team_a, rankings_df=rankings_df, stage=stage, db=db),
        "",
        format_role_based_players_to_watch_fast(team_b, rankings_df=rankings_df, stage=stage, db=db),
        "",
        make_match_talking_points_fast(team_a, team_b, stage=stage, rankings_df=rankings_df, db=db),
        "",
    ]

    if include_map:
        try:
            map_factoids = make_map_factoids(team_a, team_b, stage=stage)
            map_note = ""
            if "[Broadcast Notes]" in map_factoids:
                map_note = map_factoids.split("[Broadcast Notes]", 1)[-1].strip()
            lines += [
                "[Map Storyline]",
                map_note if map_note else "맵 스토리라인 데이터 없음",
                "",
            ]
        except Exception as e:
            lines += [
                "[Map Storyline]",
                f"맵 스토리라인 생성 실패: {e}",
                "",
            ]

    return "\n".join(lines)


def make_daily_research_document_fast(event_name, broadcast_date, stage, match_inputs_tuple, opening_note="", db=None):
    if db is None:
        db = load_database()

    valid_matches = []

    for idx, m in enumerate(match_inputs_tuple):
        team_a, team_b = m
        if team_a and team_b and team_a != team_b:
            valid_matches.append((idx + 1, team_a, team_b))

    rankings = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    lines = [
        "OWCS BROADCAST DAILY RESEARCH",
        "Version: V3.5B Starting Lineup Engine",
        "",
        f"Event: {event_name}",
        f"Date: {broadcast_date}",
        f"Stage: {stage}",
        f"Matches: {len(valid_matches)}",
        "",
    ]

    if opening_note.strip():
        lines += [
            "[Opening Notes]",
            opening_note.strip(),
            "",
        ]

    storyline_inputs = tuple((team_a, team_b) for _, team_a, team_b in valid_matches)
    lines.append(make_today_storylines(storyline_inputs, stage=stage, db=db))
    lines.append("")

    lines.append("[Today Match Order]")
    for match_no, team_a, team_b in valid_matches:
        lines.append(f"{match_no}. {team_a} vs {team_b}")
    lines.append("")

    for match_no, team_a, team_b in valid_matches:
        lines.append(
            make_storyline_match_packet_fast(
                team_a,
                team_b,
                stage=stage,
                match_no=match_no,
                rankings_df=rankings,
                db=db,
                include_map=True,
            )
        )

    lines += [
        "",
        "==================================================",
        "END OF DAILY RESEARCH",
        "==================================================",
    ]

    return "\n".join(lines)

# ==================================================
# V3.5A STARTING LINEUP + KEY MATCHUP ENGINE
# Existing functions above are intentionally untouched.
# ==================================================


def find_starting_lineup_sheet_name(db=None):
    if db is None:
        db = load_database()

    if "10_DAILY_ROSTER" in db and db["10_DAILY_ROSTER"] is not None and not db["10_DAILY_ROSTER"].empty:
        return "10_DAILY_ROSTER"

    required = {"date", "team", "player1", "player2", "player3", "player4", "player5"}

    for sheet_name, df in db.items():
        if str(sheet_name).startswith("_"):
            continue

        if df is None or df.empty:
            continue

        cols = {str(c).strip().lower() for c in df.columns}

        if required.issubset(cols):
            return sheet_name

    for sheet_name in db.keys():
        name = str(sheet_name).upper()
        if name.startswith("10") and ("LINEUP" in name or "START" in name or "ROSTER" in name or "DAILY" in name):
            return sheet_name

    return ""

def load_starting_lineups(db=None):
    if db is None:
        db = load_database()

    sheet_name = find_starting_lineup_sheet_name(db)

    if not sheet_name:
        return pd.DataFrame(
            columns=[
                "date",
                "team",
                "team_key",
                "player1",
                "player2",
                "player3",
                "player4",
                "player5",
                "dps1",
                "dps2",
                "tank",
                "sup1",
                "sup2",
                "lineup_key",
                "Source Sheet",
            ]
        )

    df = get_sheet(db, sheet_name)

    if df.empty:
        return pd.DataFrame()

    rename_map = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in ["date", "team", "player1", "player2", "player3", "player4", "player5"]:
            rename_map[col] = key

    df = df.rename(columns=rename_map).copy()

    for col in ["date", "team", "player1", "player2", "player3", "player4", "player5"]:
        if col not in df.columns:
            df[col] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["team"] = df["team"].astype(str).str.strip()
    df["team_key"] = df["team"].apply(normalize_team)

    for col in ["player1", "player2", "player3", "player4", "player5"]:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": "", "NaN": "", "None": ""})

    # Current sheet convention:
    # player1/player2 = DPS, player3 = TANK, player4/player5 = SUPPORT
    df["dps1"] = df["player1"]
    df["dps2"] = df["player2"]
    df["tank"] = df["player3"]
    df["sup1"] = df["player4"]
    df["sup2"] = df["player5"]

    df["lineup_key"] = df[
        ["player1", "player2", "player3", "player4", "player5"]
    ].apply(lambda r: "|".join([normalize_name(x) for x in r if str(x).strip()]), axis=1)

    df["Source Sheet"] = sheet_name

    df = df[df["team_key"] != ""].copy()

    return df.sort_values(["date", "team"]).reset_index(drop=True)


def get_lineup_rows_for_team(team_name, start_date=None, end_date=None, db=None):
    lineups = load_starting_lineups(db)

    if lineups.empty:
        return lineups

    team_key = normalize_team(team_name)
    df = lineups[lineups["team_key"] == team_key].copy()

    if start_date is not None:
        start_date = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start_date):
            df = df[df["date"] >= start_date].copy()

    if end_date is not None:
        end_date = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end_date):
            df = df[df["date"] <= end_date].copy()

    return df.sort_values("date", ascending=False)


def get_latest_starting_lineup(team_name, target_date=None, db=None):
    lineups = get_lineup_rows_for_team(team_name, db=db)

    if lineups.empty:
        return {}

    if target_date is not None:
        target_date = pd.to_datetime(target_date, errors="coerce")
        if pd.notna(target_date):
            before = lineups[lineups["date"] <= target_date].copy()
            if not before.empty:
                lineups = before

    row = lineups.sort_values("date", ascending=False).iloc[0]

    return {
        "date": row.get("date"),
        "team": row.get("team", team_name),
        "dps1": row.get("dps1", ""),
        "dps2": row.get("dps2", ""),
        "tank": row.get("tank", ""),
        "sup1": row.get("sup1", ""),
        "sup2": row.get("sup2", ""),
        "players": [
            row.get("dps1", ""),
            row.get("dps2", ""),
            row.get("tank", ""),
            row.get("sup1", ""),
            row.get("sup2", ""),
        ],
        "lineup_key": row.get("lineup_key", ""),
    }


def get_lineup_player_frequency(team_name, recent_n=5, target_date=None, db=None):
    rows = get_lineup_rows_for_team(team_name, db=db)

    if rows.empty:
        return pd.DataFrame(columns=["Player", "Role Slot", "Appearances", "Total Lineups", "Start Rate"])

    if target_date is not None:
        target_date = pd.to_datetime(target_date, errors="coerce")
        if pd.notna(target_date):
            rows = rows[rows["date"] <= target_date].copy()

    rows = rows.sort_values("date", ascending=False).head(recent_n).copy()

    total = len(rows)

    if total == 0:
        return pd.DataFrame(columns=["Player", "Role Slot", "Appearances", "Total Lineups", "Start Rate"])

    records = []

    slot_map = {
        "dps1": "DPS",
        "dps2": "DPS",
        "tank": "TANK",
        "sup1": "SUP",
        "sup2": "SUP",
    }

    for _, row in rows.iterrows():
        for col, role in slot_map.items():
            player = str(row.get(col, "")).strip()
            if player:
                records.append(
                    {
                        "Player": player,
                        "Player_Normalized": normalize_name(player),
                        "Role Slot": role,
                    }
                )

    if not records:
        return pd.DataFrame(columns=["Player", "Role Slot", "Appearances", "Total Lineups", "Start Rate"])

    df = pd.DataFrame(records)

    freq = (
        df.groupby(["Player_Normalized", "Role Slot"], as_index=False)
        .agg(
            Player=("Player", "last"),
            Appearances=("Player", "count"),
        )
    )

    freq["Total Lineups"] = total
    freq["Start Rate"] = freq["Appearances"] / total * 100
    freq = freq.sort_values(["Role Slot", "Start Rate", "Appearances"], ascending=[True, False, False])

    return freq[["Player", "Player_Normalized", "Role Slot", "Appearances", "Total Lineups", "Start Rate"]]


def get_lineup_stability(team_name, recent_n=5, target_date=None, db=None):
    rows = get_lineup_rows_for_team(team_name, db=db)

    if rows.empty:
        return {
            "team": team_name,
            "total": 0,
            "stability": 0,
            "unique_lineups": 0,
            "label": "UNKNOWN",
            "latest_changed": False,
            "change_note": "라인업 데이터 없음",
        }

    if target_date is not None:
        target_date = pd.to_datetime(target_date, errors="coerce")
        if pd.notna(target_date):
            rows = rows[rows["date"] <= target_date].copy()

    rows = rows.sort_values("date", ascending=False).head(recent_n).copy()
    total = len(rows)

    if total == 0:
        return {
            "team": team_name,
            "total": 0,
            "stability": 0,
            "unique_lineups": 0,
            "label": "UNKNOWN",
            "latest_changed": False,
            "change_note": "라인업 데이터 없음",
        }

    latest_key = rows.iloc[0]["lineup_key"]
    latest_same_count = int((rows["lineup_key"] == latest_key).sum())
    stability = latest_same_count / total * 100
    unique_lineups = int(rows["lineup_key"].nunique())

    if stability >= 80:
        label = "HIGH"
    elif stability >= 50:
        label = "MEDIUM"
    else:
        label = "LOW"

    latest_changed = False
    change_note = "최근 라인업 변화 없음"

    if total >= 2:
        latest = rows.iloc[0]
        previous = rows.iloc[1]

        if latest["lineup_key"] != previous["lineup_key"]:
            latest_changed = True

            latest_players = set([normalize_name(latest[c]) for c in ["player1", "player2", "player3", "player4", "player5"] if str(latest[c]).strip()])
            previous_players = set([normalize_name(previous[c]) for c in ["player1", "player2", "player3", "player4", "player5"] if str(previous[c]).strip()])

            added_keys = latest_players - previous_players
            removed_keys = previous_players - latest_players

            def _names_from_keys(row, keys):
                names = []
                for c in ["player1", "player2", "player3", "player4", "player5"]:
                    val = str(row[c]).strip()
                    if normalize_name(val) in keys:
                        names.append(val)
                return names

            added = _names_from_keys(latest, added_keys)
            removed = _names_from_keys(previous, removed_keys)

            if added or removed:
                change_note = f"라인업 변화: IN {', '.join(added) if added else '-'} / OUT {', '.join(removed) if removed else '-'}"
            else:
                change_note = "최근 경기에서 라인업 조합 변화"

    return {
        "team": team_name,
        "total": total,
        "stability": stability,
        "unique_lineups": unique_lineups,
        "label": label,
        "latest_changed": latest_changed,
        "change_note": change_note,
    }


def format_expected_lineup(team_name, target_date=None, recent_n=5, db=None):
    lineup = get_latest_starting_lineup(team_name, target_date=target_date, db=db)
    freq = get_lineup_player_frequency(team_name, recent_n=recent_n, target_date=target_date, db=db)
    stability = get_lineup_stability(team_name, recent_n=recent_n, target_date=target_date, db=db)

    if not lineup:
        return f"{team_name}: Starting Lineup 데이터 없음"

    freq_map = {}
    if freq is not None and not freq.empty:
        for _, r in freq.iterrows():
            freq_map[normalize_name(r["Player"])] = r

    def _rate_text(player):
        key = normalize_name(player)
        if key in freq_map:
            r = freq_map[key]
            return f"{int(r['Appearances'])}/{int(r['Total Lineups'])}, {r['Start Rate']:.0f}%"
        return "표본 없음"

    date_text = ""
    if pd.notna(lineup.get("date")):
        try:
            date_text = pd.to_datetime(lineup["date"]).strftime("%Y-%m-%d")
        except Exception:
            date_text = str(lineup.get("date"))

    lines = [
        f"{team_name} Expected Starting Lineup",
        f"- 기준 경기일: {date_text if date_text else '최근 데이터'}",
        f"- Lineup Stability: {stability['label']} ({stability['stability']:.0f}%, 최근 {stability['total']}회)",
        f"- {stability['change_note']}",
        f"- DPS: {lineup['dps1']} / {lineup['dps2']} ({_rate_text(lineup['dps1'])} / {_rate_text(lineup['dps2'])})",
        f"- TANK: {lineup['tank']} ({_rate_text(lineup['tank'])})",
        f"- SUP: {lineup['sup1']} / {lineup['sup2']} ({_rate_text(lineup['sup1'])} / {_rate_text(lineup['sup2'])})",
    ]

    return "\n".join(lines)


def _find_player_rank_row(player_name, rankings_df):
    if rankings_df is None or rankings_df.empty:
        return None

    key = normalize_name(player_name)

    row = rankings_df[rankings_df["Player_Normalized"] == key].copy()

    if row.empty and "Player" in rankings_df.columns:
        row = rankings_df[rankings_df["Player"].apply(normalize_name) == key].copy()

    if row.empty:
        return None

    return row.sort_values("Minutes", ascending=False).iloc[0]


def _format_player_metric_summary(player_name, role, rankings_df):
    row = _find_player_rank_row(player_name, rankings_df)

    if row is None:
        return f"{player_name}: 스탯 표본 부족"

    role = str(role).upper()

    role_total = 0
    if "Role" in rankings_df.columns:
        role_total = int((rankings_df["Role"] == role).sum())

    if role == "TANK":
        return (
            f"{player_name}: 생존력 {int(row.get('Survival Rank', 999))}/{role_total}, "
            f"D/10 {row.get('Deaths Per10', 0):.1f}, MIT/10 {row.get('Mitigation Per10', 0):.0f}"
        )

    if role == "DPS":
        return (
            f"{player_name}: 화력 {int(row.get('Damage Rank', 999))}/{role_total}, "
            f"E/10 {row.get('Elims Per10', 0):.1f}, DMG/10 {row.get('Damage Per10', 0):.0f}"
        )

    if role == "SUP":
        return (
            f"{player_name}: 힐량 {int(row.get('Healing Rank', 999))}/{role_total}, "
            f"A/10 {row.get('Assists Per10', 0):.1f}, H/10 {row.get('Healing Per10', 0):.0f}"
        )

    return f"{player_name}: E/10 {row.get('Elims Per10', 0):.1f}"


def make_key_matchups(team_a, team_b, stage=None, target_date=None, rankings_df=None, db=None):
    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    a = get_latest_starting_lineup(team_a, target_date=target_date, db=db)
    b = get_latest_starting_lineup(team_b, target_date=target_date, db=db)

    if not a or not b:
        return "[Key Matchups]\nStarting Lineup 데이터 부족으로 Key Matchup 생성 불가"

    lines = ["[Key Matchups]"]

    matchup_specs = [
        ("TANK", [a.get("tank", "")], [b.get("tank", "")]),
        ("DPS", [a.get("dps1", ""), a.get("dps2", "")], [b.get("dps1", ""), b.get("dps2", "")]),
        ("SUP", [a.get("sup1", ""), a.get("sup2", "")], [b.get("sup1", ""), b.get("sup2", "")]),
    ]

    for role, a_players, b_players in matchup_specs:
        a_players = [p for p in a_players if str(p).strip()]
        b_players = [p for p in b_players if str(p).strip()]

        if not a_players or not b_players:
            continue

        lines.append("")
        lines.append(f"[{role}]")

        if role == "TANK":
            lines.append(f"{team_a} {a_players[0]} vs {team_b} {b_players[0]}")
            lines.append(f"- {team_a}: {_format_player_metric_summary(a_players[0], role, rankings_df)}")
            lines.append(f"- {team_b}: {_format_player_metric_summary(b_players[0], role, rankings_df)}")
            lines.append("- 관전 포인트: 탱커 생존력과 첫 진입 타이밍이 경기 템포를 좌우할 수 있습니다.")

        elif role == "DPS":
            lines.append(f"{team_a} {' / '.join(a_players)} vs {team_b} {' / '.join(b_players)}")
            for p in a_players[:2]:
                lines.append(f"- {team_a}: {_format_player_metric_summary(p, role, rankings_df)}")
            for p in b_players[:2]:
                lines.append(f"- {team_b}: {_format_player_metric_summary(p, role, rankings_df)}")
            lines.append("- 관전 포인트: 첫 킬 생산력과 딜러 라인의 폭발력이 한타 시작점을 만들 수 있습니다.")

        elif role == "SUP":
            lines.append(f"{team_a} {' / '.join(a_players)} vs {team_b} {' / '.join(b_players)}")
            for p in a_players[:2]:
                lines.append(f"- {team_a}: {_format_player_metric_summary(p, role, rankings_df)}")
            for p in b_players[:2]:
                lines.append(f"- {team_b}: {_format_player_metric_summary(p, role, rankings_df)}")
            lines.append("- 관전 포인트: 장기전에서는 후방 생존과 궁극기 순환 속도가 중요합니다.")

    return "\n".join(lines)


def format_lineup_stability(team_a, team_b, target_date=None, recent_n=5, db=None):
    a = get_lineup_stability(team_a, recent_n=recent_n, target_date=target_date, db=db)
    b = get_lineup_stability(team_b, recent_n=recent_n, target_date=target_date, db=db)

    lines = [
        "[Lineup Stability]",
        f"- {team_a}: {a['label']} ({a['stability']:.0f}%, 최근 {a['total']}회) / {a['change_note']}",
        f"- {team_b}: {b['label']} ({b['stability']:.0f}%, 최근 {b['total']}회) / {b['change_note']}",
    ]

    return "\n".join(lines)


def make_storyline_match_packet_v35(team_a, team_b, stage=None, match_no=None, target_date=None, rankings_df=None, db=None, include_map=True):
    header_no = f"MATCH {match_no}" if match_no is not None else "MATCH"

    h2h = get_h2h(team_a, team_b)
    h2h_summary = h2h.get("summary", {})

    lines = [
        "==================================================",
        header_no,
        f"{team_a} vs {team_b}",
        "==================================================",
        "",
        format_match_importance(team_a, team_b, stage=stage, db=db),
        "",
        "[Expected Starting Lineup]",
        format_expected_lineup(team_a, target_date=target_date, db=db),
        "",
        format_expected_lineup(team_b, target_date=target_date, db=db),
        "",
        format_lineup_stability(team_a, team_b, target_date=target_date, db=db),
        "",
    ]

    if h2h_summary:
        lines += [
            "[H2H Summary]",
            f"- 전체 상대 전적: {team_a} {h2h_summary['team_a_wins']}승 / {team_b} {h2h_summary['team_b_wins']}승",
            f"- 2026 상대 전적: {team_a} {h2h_summary['team_a_wins_2026']}승 / {team_b} {h2h_summary['team_b_wins_2026']}승",
            f"- 최근 승자: {h2h_summary['latest_winner']}",
            f"- 현재 흐름: {h2h_summary['streak_team']} {h2h_summary['streak_count']}연승",
            "",
        ]
    else:
        lines += [
            "[H2H Summary]",
            h2h.get("storyline", "H2H 데이터 없음"),
            "",
        ]

    lines += [
        make_key_matchups(team_a, team_b, stage=stage, target_date=target_date, rankings_df=rankings_df, db=db),
        "",
        "[Player Notes]",
        "※ Player To Watch는 전체 핵심선수 나열 대신, 실제 출전 라인업 기반 Key Matchups 중심으로 축소했습니다.",
        "",
        make_match_talking_points_fast(team_a, team_b, stage=stage, rankings_df=rankings_df, db=db),
        "",
    ]

    if include_map:
        try:
            map_factoids = make_map_factoids(team_a, team_b, stage=stage)
            map_note = ""
            if "[Broadcast Notes]" in map_factoids:
                map_note = map_factoids.split("[Broadcast Notes]", 1)[-1].strip()
            lines += [
                "[Map Storyline]",
                map_note if map_note else "맵 스토리라인 데이터 없음",
                "",
            ]
        except Exception as e:
            lines += [
                "[Map Storyline]",
                f"맵 스토리라인 생성 실패: {e}",
                "",
            ]

    return "\n".join(lines)


def make_daily_research_document_v35(event_name, broadcast_date, stage, match_inputs_tuple, opening_note="", db=None):
    if db is None:
        db = load_database()

    valid_matches = []

    for idx, m in enumerate(match_inputs_tuple):
        team_a, team_b = m
        if team_a and team_b and team_a != team_b:
            valid_matches.append((idx + 1, team_a, team_b))

    rankings = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    lines = [
        "OWCS BROADCAST DAILY RESEARCH",
        "",
        f"Event: {event_name}",
        f"Date: {broadcast_date}",
        f"Stage: {stage}",
        f"Matches: {len(valid_matches)}",
        "",
    ]

    if opening_note.strip():
        lines += [
            "[Opening Notes]",
            opening_note.strip(),
            "",
        ]

    storyline_inputs = tuple((team_a, team_b) for _, team_a, team_b in valid_matches)
    lines.append(make_today_storylines(storyline_inputs, stage=stage, db=db))
    lines.append("")

    lines.append("[Today Match Order]")
    for match_no, team_a, team_b in valid_matches:
        lines.append(f"{match_no}. {team_a} vs {team_b}")
    lines.append("")

    for match_no, team_a, team_b in valid_matches:
        lines.append(
            make_storyline_match_packet_v35(
                team_a,
                team_b,
                stage=stage,
                match_no=match_no,
                target_date=broadcast_date,
                rankings_df=rankings,
                db=db,
                include_map=True,
            )
        )

    lines += [
        "",
        "==================================================",
        "END OF DAILY RESEARCH",
        "==================================================",
    ]

    return "\n".join(lines)

# ==================================================
# V4.0D DAILY ROSTER TALKING POINTS + LOGO RESOLVER
# Existing functions above are intentionally untouched.
# These definitions override earlier functions with the same names.
# ==================================================

def _split_alias_values(value):
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[,/|;]+", text)
    return [p.strip() for p in parts if p and str(p).strip()]


def get_team_alias_keys(team_name, db=None):
    if db is None:
        db = load_database()

    target_key = normalize_team(team_name)
    keys = set([target_key]) if target_key else set()

    teams = get_sheet(db, "01_TEAMS")
    if teams.empty:
        return keys

    teams = teams.copy()
    for col in ["team_id", "short_name", "official_name", "aliases"]:
        if col not in teams.columns:
            teams[col] = ""

    candidate_rows = []
    for _, row in teams.iterrows():
        row_keys = set()
        for col in ["team_id", "short_name", "official_name"]:
            val = row.get(col, "")
            key = normalize_team(val)
            if key:
                row_keys.add(key)

        for alias in _split_alias_values(row.get("aliases", "")):
            key = normalize_team(alias)
            if key:
                row_keys.add(key)

        if target_key in row_keys:
            candidate_rows.append(row)
            keys.update(row_keys)

    return keys


def load_assets(db=None):
    if db is None:
        db = load_database()

    assets = get_sheet(db, "14_ASSETS")

    if assets.empty:
        return pd.DataFrame(columns=["entity_id", "logo_file", "entity_key"])

    assets.columns = [str(c).strip() for c in assets.columns]

    if "entity_id" not in assets.columns or "logo_file" not in assets.columns:
        return pd.DataFrame(columns=["entity_id", "logo_file", "entity_key"])

    assets = assets.copy()
    assets["entity_id"] = assets["entity_id"].astype(str).str.strip()
    assets["logo_file"] = assets["logo_file"].astype(str).str.strip()
    assets["entity_key"] = assets["entity_id"].apply(normalize_team)

    return assets


def get_team_logo_path_v33d(team_id, db=None):
    if db is None:
        db = load_database()

    assets = load_assets(db)

    if assets.empty:
        return None

    team_keys = get_team_alias_keys(team_id, db=db)
    if not team_keys:
        team_keys = {normalize_team(team_id)}

    row = assets[assets["entity_key"].isin(team_keys)].copy()

    if row.empty and "entity_id" in assets.columns:
        row = assets[assets["entity_id"].apply(normalize_team).isin(team_keys)].copy()

    if row.empty:
        return None

    for _, asset_row in row.iterrows():
        logo_file = str(asset_row.get("logo_file", "")).strip()
        if not logo_file:
            continue

        for candidate in resolve_logo_path_candidates(logo_file):
            if candidate.exists():
                return candidate

    return None


def get_logo_debug_table(db=None):
    if db is None:
        db = load_database()

    assets = load_assets(db)

    if assets.empty:
        return pd.DataFrame(
            columns=[
                "entity_id",
                "entity_key",
                "logo_file",
                "resolved_path",
                "exists",
                "checked_paths",
                "alias_keys",
            ]
        )

    rows = []

    for _, row in assets.iterrows():
        logo_file = str(row.get("logo_file", "")).strip()
        candidates = resolve_logo_path_candidates(logo_file)
        existing = [p for p in candidates if p.exists()]
        resolved = existing[0] if existing else None

        alias_keys = get_team_alias_keys(row.get("entity_id", ""), db=db)

        rows.append(
            {
                "entity_id": row.get("entity_id", ""),
                "entity_key": row.get("entity_key", ""),
                "logo_file": logo_file,
                "resolved_path": str(resolved) if resolved else "",
                "exists": bool(resolved),
                "checked_paths": " | ".join(str(p) for p in candidates),
                "alias_keys": " | ".join(sorted(alias_keys)),
            }
        )

    return pd.DataFrame(rows)


def get_lineup_rows_for_team(team_name, start_date=None, end_date=None, db=None):
    lineups = load_starting_lineups(db)

    if lineups.empty:
        return lineups

    team_keys = get_team_alias_keys(team_name, db=db)
    if not team_keys:
        team_keys = {normalize_team(team_name)}

    df = lineups[lineups["team_key"].isin(team_keys)].copy()

    if start_date is not None:
        start_date = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start_date):
            df = df[df["date"] >= start_date].copy()

    if end_date is not None:
        end_date = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end_date):
            df = df[df["date"] <= end_date].copy()

    return df.sort_values("date", ascending=False)


def get_daily_roster_players(team_name, target_date=None, db=None):
    lineup = get_latest_starting_lineup(team_name, target_date=target_date, db=db)

    if not lineup:
        return []

    specs = [
        ("DPS", lineup.get("dps1", "")),
        ("DPS", lineup.get("dps2", "")),
        ("TANK", lineup.get("tank", "")),
        ("SUP", lineup.get("sup1", "")),
        ("SUP", lineup.get("sup2", "")),
    ]

    rows = []
    seen = set()

    for role, player in specs:
        player = str(player).strip()
        key = normalize_name(player)
        if not player or not key or key in seen:
            continue
        rows.append({"Player": player, "Player_Normalized": key, "Role": role})
        seen.add(key)

    return rows


def _find_player_rank_row(player_name, rankings_df):
    if rankings_df is None or rankings_df.empty:
        return None

    key = normalize_name(player_name)

    row = rankings_df[rankings_df["Player_Normalized"] == key].copy()

    if row.empty and "Player" in rankings_df.columns:
        row = rankings_df[rankings_df["Player"].apply(normalize_name) == key].copy()

    if row.empty:
        return None

    return row.sort_values("Minutes", ascending=False).iloc[0]


def _lineup_metric_text(player_name, role, rankings_df):
    row = _find_player_rank_row(player_name, rankings_df)

    if row is None:
        return f"{player_name}({role})"

    role = str(role).upper()
    role_total = int((rankings_df["Role"] == role).sum()) if "Role" in rankings_df.columns else 0

    if role == "TANK":
        return (
            f"{player_name}(TANK, D/10 {row.get('Deaths Per10', 0):.1f}, "
            f"생존 {int(row.get('Survival Rank', 999))}/{role_total})"
        )

    if role == "DPS":
        return (
            f"{player_name}(DPS, E/10 {row.get('Elims Per10', 0):.1f}, "
            f"DMG/10 {row.get('Damage Per10', 0):.0f})"
        )

    if role == "SUP":
        return (
            f"{player_name}(SUP, A/10 {row.get('Assists Per10', 0):.1f}, "
            f"H/10 {row.get('Healing Per10', 0):.0f})"
        )

    return f"{player_name}({role})"


def format_daily_roster_players_to_watch(team_name, stage=None, target_date=None, rankings_df=None, db=None):
    if db is None:
        db = load_database()

    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    lineup_players = get_daily_roster_players(team_name, target_date=target_date, db=db)

    if not lineup_players:
        return f"{team_name}: DAILY_ROSTER 기반 선수 데이터 없음"

    role_order = {"TANK": 1, "DPS": 2, "SUP": 3}
    lineup_players = sorted(lineup_players, key=lambda x: role_order.get(x["Role"], 99))

    lines = [f"{team_name} 체크 포인트"]

    for item in lineup_players:
        lines.append(
            "- " + _lineup_metric_text(
                item["Player"],
                item["Role"],
                rankings_df,
            )
        )

    return "\n".join(lines)


def make_match_talking_points_fast(team_a, team_b, stage=None, rankings_df=None, db=None, target_date=None):
    if db is None:
        db = load_database()

    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    h2h = get_h2h(team_a, team_b)
    summary = h2h.get("summary", {})
    importance = get_match_importance(team_a, team_b, stage=stage, db=db)

    points = []

    if summary:
        points.append(
            f"상대전적은 {team_a} {summary['team_a_wins']}승 / {team_b} {summary['team_b_wins']}승 구도."
        )
        points.append(
            f"최근 맞대결 승자는 {summary['latest_winner']}, 현재 {summary['streak_team']} {summary['streak_count']}연승."
        )
    else:
        points.append("공식 맞대결 데이터가 부족해 순위, 최근 폼, 실제 출전 라인업 중심으로 풀어갈 경기.")

    points.append(f"경기 중요도는 {importance['label']} 등급.")

    for team in [team_a, team_b]:
        lineup_players = get_daily_roster_players(team, target_date=target_date, db=db)

        if lineup_players:
            names = [
                _lineup_metric_text(item["Player"], item["Role"], rankings_df)
                for item in lineup_players
            ]
            points.append(f"{team} 체크 포인트: " + ", ".join(names))
        else:
            watch = get_role_based_players_to_watch_fast(team, rankings_df=rankings_df, stage=stage, db=db)
            if not watch.empty:
                names = []
                for _, r in watch.iterrows():
                    names.append(f"{r.get('Player')}({r.get('Role')})")
                points.append(f"{team} 체크 포인트: " + ", ".join(names) + " ※ DAILY_ROSTER fallback")

    points = points[:6]

    lines = ["[Talking Points / Daily Roster Based]"]
    for idx, point in enumerate(points, start=1):
        lines.append(f"{idx}. {point}")

    return "\n".join(lines)


def make_match_talking_points(team_a, team_b, stage=None, db=None):
    rankings = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)
    return make_match_talking_points_fast(
        team_a,
        team_b,
        stage=stage,
        rankings_df=rankings,
        db=db,
        target_date=None,
    )


def make_storyline_match_packet_v35(team_a, team_b, stage=None, match_no=None, target_date=None, rankings_df=None, db=None, include_map=True):
    if db is None:
        db = load_database()

    if rankings_df is None:
        rankings_df = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    header_no = f"MATCH {match_no}" if match_no is not None else "MATCH"

    h2h = get_h2h(team_a, team_b)
    h2h_summary = h2h.get("summary", {})

    lines = [
        "==================================================",
        header_no,
        f"{team_a} vs {team_b}",
        "==================================================",
        "",
        format_match_importance(team_a, team_b, stage=stage, db=db),
        "",
        "[Expected Starting Lineup]",
        format_expected_lineup(team_a, target_date=target_date, db=db),
        "",
        format_expected_lineup(team_b, target_date=target_date, db=db),
        "",
        format_lineup_stability(team_a, team_b, target_date=target_date, db=db),
        "",
    ]

    if h2h_summary:
        lines += [
            "[H2H Summary]",
            f"- 전체 상대 전적: {team_a} {h2h_summary['team_a_wins']}승 / {team_b} {h2h_summary['team_b_wins']}승",
            f"- 2026 상대 전적: {team_a} {h2h_summary['team_a_wins_2026']}승 / {team_b} {h2h_summary['team_b_wins_2026']}승",
            f"- 최근 승자: {h2h_summary['latest_winner']}",
            f"- 현재 흐름: {h2h_summary['streak_team']} {h2h_summary['streak_count']}연승",
            "",
        ]
    else:
        lines += [
            "[H2H Summary]",
            h2h.get("storyline", "H2H 데이터 없음"),
            "",
        ]

    lines += [
        make_key_matchups(team_a, team_b, stage=stage, target_date=target_date, rankings_df=rankings_df, db=db),
        "",
        "[Daily Roster Player Notes]",
        format_daily_roster_players_to_watch(team_a, stage=stage, target_date=target_date, rankings_df=rankings_df, db=db),
        "",
        format_daily_roster_players_to_watch(team_b, stage=stage, target_date=target_date, rankings_df=rankings_df, db=db),
        "",
        make_match_talking_points_fast(
            team_a,
            team_b,
            stage=stage,
            rankings_df=rankings_df,
            db=db,
            target_date=target_date,
        ),
        "",
    ]

    if include_map:
        try:
            map_factoids = make_map_factoids(team_a, team_b, stage=stage)
            map_note = ""
            if "[Broadcast Notes]" in map_factoids:
                map_note = map_factoids.split("[Broadcast Notes]", 1)[-1].strip()
            lines += [
                "[Map Storyline]",
                map_note if map_note else "맵 스토리라인 데이터 없음",
                "",
            ]
        except Exception as e:
            lines += [
                "[Map Storyline]",
                f"맵 스토리라인 생성 실패: {e}",
                "",
            ]

    return "\n".join(lines)


def make_storyline_match_packet(team_a, team_b, stage=None, match_no=None, db=None):
    rankings = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)
    return make_storyline_match_packet_v35(
        team_a,
        team_b,
        stage=stage,
        match_no=match_no,
        target_date=None,
        rankings_df=rankings,
        db=db,
        include_map=True,
    )


def make_daily_research_document_v35(event_name, broadcast_date, stage, match_inputs_tuple, opening_note="", db=None):
    if db is None:
        db = load_database()

    valid_matches = []

    for idx, m in enumerate(match_inputs_tuple):
        team_a, team_b = m
        if team_a and team_b and team_a != team_b:
            valid_matches.append((idx + 1, team_a, team_b))

    rankings = get_role_rankings(stage=stage, min_minutes=MIN_PLAYER_MINUTES, db=db)

    lines = [
        "OWCS BROADCAST DAILY RESEARCH",
        "Version: V4.0D Daily Roster Talking Points",
        "",
        f"Event: {event_name}",
        f"Date: {broadcast_date}",
        f"Stage: {stage}",
        f"Matches: {len(valid_matches)}",
        "",
    ]

    if str(opening_note).strip():
        lines += [
            "[Opening Notes]",
            str(opening_note).strip(),
            "",
        ]

    storyline_inputs = tuple((team_a, team_b) for _, team_a, team_b in valid_matches)
    lines.append(make_today_storylines(storyline_inputs, stage=stage, db=db))
    lines.append("")

    lines.append("[Today Match Order]")
    for match_no, team_a, team_b in valid_matches:
        lines.append(f"{match_no}. {team_a} vs {team_b}")
    lines.append("")

    for match_no, team_a, team_b in valid_matches:
        lines.append(
            make_storyline_match_packet_v35(
                team_a,
                team_b,
                stage=stage,
                match_no=match_no,
                target_date=broadcast_date,
                rankings_df=rankings,
                db=db,
                include_map=True,
            )
        )

    lines += [
        "",
        "==================================================",
        "END OF DAILY RESEARCH",
        "==================================================",
    ]

    return "\n".join(lines)

