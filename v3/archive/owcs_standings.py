import json
from collections import defaultdict

MATCHES_PATH = "matches.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_standings(tournament_filter=None):
    matches = load_json(MATCHES_PATH)

    table = defaultdict(lambda: {
        "team": "",
        "w": 0,
        "l": 0,
        "map_diff": 0,
    })

    for match in matches:
        tournament = match.get("tournament", "")

        if tournament_filter and tournament_filter not in tournament:
            continue

        team_a = match.get("team_a")
        team_b = match.get("team_b")
        score_a = match.get("score_a", 0)
        score_b = match.get("score_b", 0)

        if not team_a or not team_b:
            continue

        if score_a == 0 and score_b == 0:
            continue

        table[team_a]["team"] = team_a
        table[team_b]["team"] = team_b

        table[team_a]["map_diff"] += score_a - score_b
        table[team_b]["map_diff"] += score_b - score_a

        if score_a > score_b:
            table[team_a]["w"] += 1
            table[team_b]["l"] += 1
        elif score_b > score_a:
            table[team_b]["w"] += 1
            table[team_a]["l"] += 1

    standings = list(table.values())

    standings.sort(
        key=lambda x: (x["w"], x["map_diff"]),
        reverse=True
    )

    result = []
    for i, row in enumerate(standings, start=1):
        diff = row["map_diff"]
        result.append({
            "rank": i,
            "team": row["team"],
            "w": row["w"],
            "l": row["l"],
            "diff": f"+{diff}" if diff > 0 else str(diff),
        })

    return result


if __name__ == "__main__":
    standings = get_standings("2026_KR_STAGE2")

    for s in standings:
        print(s)