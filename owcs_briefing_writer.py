import json
from collections import defaultdict

MATCHES_PATH = "matches.json"
MAPS_PATH = "maps.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


matches = load_json(MATCHES_PATH)
maps = load_json(MAPS_PATH)


def norm(name):
    return str(name).strip().lower()


def is_same_team(a, b):
    return norm(a) == norm(b)


def get_match_score(match, team):
    if is_same_team(match.get("team_a"), team):
        return match.get("score_a", 0)

    if is_same_team(match.get("team_b"), team):
        return match.get("score_b", 0)

    return 0


def get_match_winner(match):
    score_a = match.get("score_a", 0)
    score_b = match.get("score_b", 0)

    if score_a > score_b:
        return match.get("team_a")
    elif score_b > score_a:
        return match.get("team_b")
    else:
        return "Draw"


def get_h2h(team_a, team_b):
    h2h = []

    for match in matches:
        match_team_a = match.get("team_a")
        match_team_b = match.get("team_b")

        same_order = (
            is_same_team(match_team_a, team_a)
            and is_same_team(match_team_b, team_b)
        )

        reverse_order = (
            is_same_team(match_team_a, team_b)
            and is_same_team(match_team_b, team_a)
        )

        if not same_order and not reverse_order:
            continue

        score_a = match.get("score_a", 0)
        score_b = match.get("score_b", 0)

        # 0-0 미진행 경기 제외
        if score_a == 0 and score_b == 0:
            continue

        h2h.append(match)

    return h2h


def summarize_h2h(team_a, team_b):
    h2h = get_h2h(team_a, team_b)

    win_a = 0
    win_b = 0
    draw = 0

    for match in h2h:
        score_a = get_match_score(match, team_a)
        score_b = get_match_score(match, team_b)

        if score_a > score_b:
            win_a += 1
        elif score_b > score_a:
            win_b += 1
        else:
            draw += 1

    return {
        "total": len(h2h),
        "win_a": win_a,
        "win_b": win_b,
        "draw": draw,
        "matches": h2h,
    }


def get_recent_h2h(team_a, team_b, limit=5):
    return get_h2h(team_a, team_b)[-limit:]


def get_map_name(item):
    return item.get("map") or item.get("map_name") or item.get("name")


def get_map_score(item):
    return item.get("score") or item.get("map_score") or item.get("result")


def get_map_winner(item):
    return item.get("winner") or item.get("winning_team")


def get_map_teams(item):
    return (
        item.get("team_a") or item.get("team1"),
        item.get("team_b") or item.get("team2"),
    )


def is_zero_zero_score(score):
    if score is None:
        return False

    s = str(score).replace(" ", "")
    return s in ["0-0", "0:0"]


def get_map_h2h(team_a, team_b):
    records = defaultdict(lambda: {
        "team_a_win": 0,
        "team_b_win": 0,
        "draw": 0,
        "total": 0,
    })

    for match in maps:
        match_team_a = match.get("team_a")
        match_team_b = match.get("team_b")

        same_order = (
            is_same_team(match_team_a, team_a)
            and is_same_team(match_team_b, team_b)
        )

        reverse_order = (
            is_same_team(match_team_a, team_b)
            and is_same_team(match_team_b, team_a)
        )

        if not same_order and not reverse_order:
            continue

        # 경기 자체가 0-0이면 제외
        if match.get("score_a", 0) == 0 and match.get("score_b", 0) == 0:
            continue

        for map_item in match.get("maps", []):
            map_name = map_item.get("map")
            if not map_name:
                continue

            map_score_a = map_item.get("score_a", 0)
            map_score_b = map_item.get("score_b", 0)

            # 맵 0-0 제외
            if map_score_a == 0 and map_score_b == 0:
                continue

            winner = map_item.get("winner")

            records[map_name]["total"] += 1

            if is_same_team(winner, team_a):
                records[map_name]["team_a_win"] += 1
            elif is_same_team(winner, team_b):
                records[map_name]["team_b_win"] += 1
            else:
                records[map_name]["draw"] += 1

    return records

def generate_map_points(team_a, team_b):
    records = get_map_h2h(team_a, team_b)

    if not records:
        return ["맵별 맞대결 데이터가 없습니다."]

    points = []

    for map_name, r in records.items():
        a_win = r["team_a_win"]
        b_win = r["team_b_win"]
        draw = r["draw"]
        total = r["total"]

        if a_win > b_win:
            comment = f"{team_a} 우세"
        elif b_win > a_win:
            comment = f"{team_b} 우세"
        else:
            comment = "팽팽한 맵"

        points.append(
            f"{map_name}: {comment} / "
            f"{team_a} {a_win}승, {team_b} {b_win}승, 무승부 {draw}회 / 총 {total}맵"
        )

    return points


def generate_comment(team_a, team_b, summary):
    if summary["total"] == 0:
        return f"오늘 {team_a}와 {team_b}는 공식 맞대결 데이터가 부족한 매치업입니다."

    if summary["win_a"] > summary["win_b"]:
        leader = team_a
    elif summary["win_b"] > summary["win_a"]:
        leader = team_b
    else:
        leader = None

    if leader:
        return (
            f"오늘 {team_a}와 {team_b}의 맞대결은 "
            f"최근 전적상 {leader}가 앞서고 있습니다. "
            f"다만 양 팀 모두 상위권 전력인 만큼 첫 세트 흐름이 중요합니다."
        )

    return (
        f"오늘 {team_a}와 {team_b}의 맞대결은 전적상 매우 팽팽합니다. "
        f"초반 교전과 첫 맵 흐름이 승부의 핵심이 될 수 있습니다."
    )


def write_briefing(team_a, team_b):
    summary = summarize_h2h(team_a, team_b)
    recent = get_recent_h2h(team_a, team_b)
    map_points = generate_map_points(team_a, team_b)
    comment = generate_comment(team_a, team_b, summary)

    lines = []

    lines.append("========================")
    lines.append("OWCS 방송 브리프")
    lines.append("========================")
    lines.append(f"{team_a} vs {team_b}")
    lines.append("")

    lines.append("[전체 전적]")
    lines.append(
        f"{team_a} {summary['win_a']}승 "
        f"{team_b} {summary['win_b']}승 "
        f"{summary['draw']}무 "
        f"(총 {summary['total']}경기)"
    )
    lines.append("")

    lines.append("[최근 맞대결]")
    if recent:
        for match in recent:
            tournament = match.get("tournament", "Unknown")
            score_a = get_match_score(match, team_a)
            score_b = get_match_score(match, team_b)
            winner = get_match_winner(match)

            lines.append(
                f"{tournament} | {team_a} {score_a} - {score_b} {team_b} | winner: {winner}"
            )
    else:
        lines.append("최근 맞대결 데이터가 없습니다.")
    lines.append("")

    lines.append("[맵 포인트]")
    for point in map_points:
        lines.append(f"- {point}")
    lines.append("")

    lines.append("[방송용 멘트]")
    lines.append(comment)

    return "\n".join(lines)


if __name__ == "__main__":
    team_a = input("팀 A: ").strip()
    team_b = input("팀 B: ").strip()

    print()
    print(write_briefing(team_a, team_b))