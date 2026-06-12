import json

PLAYERS_JSON = "players.json"

with open(PLAYERS_JSON, "r", encoding="utf-8") as f:
    players_db = json.load(f)

def normalize(text):
    return str(text).strip().lower()

def find_player(player_name):
    target = normalize(player_name)
    results = []

    for season, teams in players_db.items():
        for team, data in teams.items():

            for player in data.get("players", []):
                if normalize(player) == target:
                    results.append({
                        "season": season,
                        "team": team,
                        "name": player,
                        "type": "Player"
                    })

            for staff in data.get("staff", []):
                if normalize(staff) == target:
                    results.append({
                        "season": season,
                        "team": team,
                        "name": staff,
                        "type": "Staff"
                    })

    return results

def find_team(team_name):
    target = normalize(team_name)
    results = {}

    for season, teams in players_db.items():
        for team, data in teams.items():
            if normalize(team) == target:
                results[season] = data

    return results

def print_player_results(player_name, results):
    print("\n========================")
    print("선수 조회")
    print("========================")
    print(player_name)
    print("------------------------")

    if not results:
        print("해당 선수를 찾을 수 없습니다.")
        return

    for r in results:
        print(f"{r['season']} | {r['team']} | {r['name']} | {r['type']}")

def print_team_results(team_name, results):
    print("\n========================")
    print("팀 로스터 조회")
    print("========================")
    print(team_name)
    print("------------------------")

    if not results:
        print("해당 팀을 찾을 수 없습니다.")
        return

    for season, data in results.items():
        print(f"\n[{season}]")

        print("Players")
        for p in data.get("players", []):
            print(f"- {p}")

        print("Staff")
        for s in data.get("staff", []):
            print(f"- {s}")

mode = input("조회 방식 (player/team): ").strip().lower()

if mode == "player":
    player_name = input("선수명: ")
    results = find_player(player_name)
    print_player_results(player_name, results)

elif mode == "team":
    team_name = input("팀명: ")
    results = find_team(team_name)
    print_team_results(team_name, results)

else:
    print("player 또는 team 중 하나를 입력해주세요.")