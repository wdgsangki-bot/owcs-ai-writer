import json

with open("maps.json", "r", encoding="utf-8") as f:
    series_list = json.load(f)

with open("teams.json", "r", encoding="utf-8") as f:
    teams = json.load(f)

def normalize_team(name):
    name = name.strip()

    for standard_name, aliases in teams.items():
        if name.lower() == standard_name.lower():
            return standard_name

        for alias in aliases:
            if name.lower() == alias.lower():
                return standard_name

    return name

def normalize_map(name):
    name = name.strip().lower()

    map_aliases = {
        "lijang": "Lijiang Tower",
        "lijiang": "Lijiang Tower",
        "lijiang tower": "Lijiang Tower",
        "busan": "Busan",
        "runasapi": "Runasapi",
        "blizzard": "Blizzard World",
        "blizzard world": "Blizzard World",
        "havana": "Havana",
        "gibraltar": "Watchpoint: Gibraltar",
        "watchpoint": "Watchpoint: Gibraltar",
        "watchpoint gibraltar": "Watchpoint: Gibraltar",
        "suravasa": "Suravasa",
        "esperanca": "Esperança",
        "esperança": "Esperança",
        "rialto": "Rialto",
        "numbani": "Numbani",
        "aatlis": "Aatlis",
    }

    return map_aliases.get(name, name.title())

def get_team_map_record(team, map_name=None, opponent=None):
    team = normalize_team(team)

    if map_name:
        map_name = normalize_map(map_name)

    if opponent:
        opponent = normalize_team(opponent)

    wins = 0
    losses = 0
    draws = 0
    games = []

    for series in series_list:
        team_a = series["team_a"]
        team_b = series["team_b"]

        if team not in [team_a, team_b]:
            continue

        if opponent and opponent not in [team_a, team_b]:
            continue

        for m in series["maps"]:
            if map_name and m["map"] != map_name:
                continue

            winner = m["winner"]

            if winner == team:
                wins += 1
                result = "W"
            elif winner == "Draw":
                draws += 1
                result = "D"
            else:
                losses += 1
                result = "L"

            games.append({
                "series": series,
                "map": m,
                "result": result
            })

    total = wins + losses + draws
    win_rate = (wins / total * 100) if total > 0 else 0

    return {
        "team": team,
        "map": map_name,
        "opponent": opponent,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "total": total,
        "win_rate": win_rate,
        "games": games
    }

def print_record(record):
    team = record["team"]
    map_name = record["map"]
    opponent = record["opponent"]

    print("\n========================")
    print("맵 전적")
    print("========================")

    title = team

    if opponent:
        title += f" vs {opponent}"

    if map_name:
        title += f" @ {map_name}"

    print(title)
    print("------------------------")

    print(
        f"{record['wins']}승 {record['losses']}패 {record['draws']}무 "
        f"/ 총 {record['total']}맵"
    )

    print(f"승률: {record['win_rate']:.1f}%")

    print("\n상세")
    if not record["games"]:
        print("해당 조건의 맵 데이터가 없습니다.")
        return

    for item in record["games"]:
        series = item["series"]
        m = item["map"]

        print(
            f"{series['tournament']} | "
            f"{series['team_a']} {series['score_a']} - {series['score_b']} {series['team_b']} | "
            f"{m['map']} | winner: {m['winner']} | result: {item['result']}"
        )

team = input("팀: ")
map_name = input("맵 이름 (전체면 엔터): ")
opponent = input("상대팀 (전체면 엔터): ")

map_name = map_name if map_name.strip() else None
opponent = opponent if opponent.strip() else None

record = get_team_map_record(team, map_name, opponent)
print_record(record)