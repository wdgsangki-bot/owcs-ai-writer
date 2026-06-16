import json

with open("matches.json", "r", encoding="utf-8") as f:
    matches = json.load(f)

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

def is_completed(match):
    return not (match["score_a"] == 0 and match["score_b"] == 0)

def get_phase(match):
    return match.get("phase", "Regular Season")

def get_match_label(match):
    tournament = match.get("tournament", "UNKNOWN")
    phase = match.get("phase", "Regular Season")
    date = match.get("date", "")

    if date:
        return f"{tournament} | {phase} | {date}"
    else:
        return f"{tournament} | {phase}"

def get_series_format(match):
    if match["score_a"] == 4 or match["score_b"] == 4:
        return "FT4"
    return "FT3"

def get_josa(word, josa_type):
    ga_words = [
        "Team Falcons",
        "T1",
        "ZETA DIVISION",
        "O2 Blast",
        "Poker Face",
        "SuperBad",
        "VEC",
        "WAY",
        "WAE"
    ]

    eun_words = [
        "Crazy Raccoon",
        "Cheeseburger",
        "ONSIDE GAMING",
        "ZAN Esports",
        "ZANSIDE GAMING",
        "Old Ocean",
        "All Gamers Global",
        "From The Gamer",
        "New Era",
        "Mir Gaming"
    ]

    if josa_type == "이/가":
        if word in ga_words:
            return "가"
        return "이"

    if josa_type == "을/를":
        if word in ga_words:
            return "를"
        return "을"

    if josa_type == "은/는":
        if word in ga_words:
            return "는"
        return "은"

    return ""

def get_team_score(match, team):
    if match["team_a"] == team:
        return match["score_a"], match["score_b"]
    if match["team_b"] == team:
        return match["score_b"], match["score_a"]
    return None

def get_winner_loser(match):
    if match["score_a"] > match["score_b"]:
        return match["team_a"], match["team_b"], match["score_a"], match["score_b"]
    else:
        return match["team_b"], match["team_a"], match["score_b"], match["score_a"]

def calculate_h2h(team1, team2, phase_filter=None):
    team1 = normalize_team(team1)
    team2 = normalize_team(team2)

    team1_wins = 0
    team2_wins = 0
    team1_sets = 0
    team2_sets = 0
    games = []

    for m in matches:
        if not is_completed(m):
            continue

        if phase_filter and get_phase(m) != phase_filter:
            continue

        if {m["team_a"], m["team_b"]} == {team1, team2}:
            score1, score2 = get_team_score(m, team1)

            team1_sets += score1
            team2_sets += score2

            if score1 > score2:
                team1_wins += 1
            else:
                team2_wins += 1

            games.append(m)

    return {
        "team1": team1,
        "team2": team2,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "team1_sets": team1_sets,
        "team2_sets": team2_sets,
        "games": games,
    }

def calculate_h2h_by_phase(team1, team2):
    phase_results = {}
    phases = sorted(set(get_phase(m) for m in matches))

    for phase in phases:
        result = calculate_h2h(team1, team2, phase_filter=phase)
        if result["games"]:
            phase_results[phase] = result

    return phase_results

def team_record(team):
    team = normalize_team(team)

    wins = 0
    losses = 0
    set_wins = 0
    set_losses = 0
    played = []

    for m in matches:
        if not is_completed(m):
            continue

        if team not in [m["team_a"], m["team_b"]]:
            continue

        score_for, score_against = get_team_score(m, team)

        set_wins += score_for
        set_losses += score_against

        if score_for > score_against:
            wins += 1
        else:
            losses += 1

        played.append(m)

    return wins, losses, set_wins, set_losses, played

def print_match_list(games):
    if not games:
        print("완료된 경기가 없습니다.")
        return

    for g in games:
        label = get_match_label(g)
        series_format = get_series_format(g)

        print(
            f"{label} | "
            f"{series_format} | "
            f"{g['team_a']} {g['score_a']} - {g['score_b']} {g['team_b']}"
        )

def print_h2h_result(title, result):
    print(f"\n[{title}]")
    print(f"{result['team1']} 기준 {result['team1_wins']}승 {result['team2_wins']}패")
    print(f"세트스코어: {result['team1_sets']}-{result['team2_sets']}")
    print_match_list(result["games"])

def print_team_summary(team):
    team = normalize_team(team)
    wins, losses, set_wins, set_losses, played = team_record(team)

    print("\n========================")
    print(f"{team} 팀 요약")
    print("========================")
    print(f"전체 전적: {wins}승 {losses}패")
    print(f"세트 득실: {set_wins}-{set_losses}")

    print("\n최근 경기")
    print_match_list(played[-5:])

def generate_brief(team1, team2):
    team1 = normalize_team(team1)
    team2 = normalize_team(team2)

    total = calculate_h2h(team1, team2)
    by_phase = calculate_h2h_by_phase(team1, team2)

    t1_wins, t1_losses, t1_set_wins, t1_set_losses, t1_games = team_record(team1)
    t2_wins, t2_losses, t2_set_wins, t2_set_losses, t2_games = team_record(team2)

    print("\n========================")
    print("방송 브리프")
    print("========================")
    print(f"오늘의 매치업은 {team1} 대 {team2}입니다.\n")

    print(
        f"{team1}{get_josa(team1, '은/는')} 수집된 OWCS Korea 기준 "
        f"{t1_wins}승 {t1_losses}패, 세트 득실 {t1_set_wins}-{t1_set_losses}를 기록 중입니다."
    )

    print(
        f"{team2}{get_josa(team2, '은/는')} 수집된 OWCS Korea 기준 "
        f"{t2_wins}승 {t2_losses}패, 세트 득실 {t2_set_wins}-{t2_set_losses}를 기록 중입니다.\n"
    )

    print(f"전체 맞대결 전적은 {team1} 기준 {total['team1_wins']}승 {total['team2_wins']}패입니다.")
    print(f"세트 스코어 합산은 {total['team1_sets']}-{total['team2_sets']}입니다.\n")

    if total["games"]:
        last_game = total["games"][-1]
        winner, loser, win_score, lose_score = get_winner_loser(last_game)
        label = get_match_label(last_game)
        series_format = get_series_format(last_game)

        print(
            f"가장 최근 맞대결은 {label} 경기였고, "
            f"{winner}{get_josa(winner, '이/가')} {loser}{get_josa(loser, '을/를')} "
            f"{series_format} 시리즈에서 {win_score}-{lose_score}로 꺾었습니다.\n"
        )

    print("[Phase별 맞대결]")
    if not by_phase:
        print("완료된 맞대결이 없습니다.")
    else:
        for phase, result in by_phase.items():
            print(
                f"- {phase}: "
                f"{team1} 기준 {result['team1_wins']}승 {result['team2_wins']}패 "
                f"(세트 {result['team1_sets']}-{result['team2_sets']})"
            )

    print("\n[관전 포인트]")

    points = []

    regular = by_phase.get("Regular Season")

    if regular and regular["team1_wins"] > regular["team2_wins"]:
        points.append(
            f"정규리그 기준으로는 {team1}{get_josa(team1, '이/가')} "
            f"{team2}{get_josa(team2, '을/를')} 상대로 강한 흐름을 보여왔습니다."
        )
    elif regular and regular["team2_wins"] > regular["team1_wins"]:
        points.append(
            f"정규리그 기준으로는 {team2}{get_josa(team2, '이/가')} "
            f"{team1}{get_josa(team1, '을/를')} 상대로 우위를 보였습니다."
        )

    non_regular_games = [
        g for g in total["games"]
        if get_phase(g) != "Regular Season"
    ]

    if non_regular_games:
        last_non_regular = non_regular_games[-1]
        winner, loser, win_score, lose_score = get_winner_loser(last_non_regular)
        series_format = get_series_format(last_non_regular)

        points.append(
            f"하지만 토너먼트 단계에서는 {winner}{get_josa(winner, '이/가')} "
            f"{loser}{get_josa(loser, '을/를')} "
            f"{series_format} 시리즈에서 {win_score}-{lose_score}로 꺾은 최근 사례가 있습니다."
        )

    if total["team1_wins"] > total["team2_wins"]:
        points.append(
            f"전체 상대전적에서는 {team1}{get_josa(team1, '이/가')} 앞서지만, "
            f"최근 중요한 무대의 결과가 변수입니다."
        )
    elif total["team2_wins"] > total["team1_wins"]:
        points.append(
            f"전체 상대전적에서는 {team2}{get_josa(team2, '이/가')} 앞서고 있습니다."
        )

    if not points:
        points.append("양 팀의 맞대결 데이터가 아직 적어, 이번 경기가 향후 서사의 기준점이 될 수 있습니다.")

    for i, point in enumerate(points, start=1):
        print(f"{i}. {point}")

team1 = input("팀1: ")
team2 = input("팀2: ")

total = calculate_h2h(team1, team2)
by_phase = calculate_h2h_by_phase(team1, team2)

print("\n========================")
print(f"{total['team1']} vs {total['team2']}")
print("========================")

print_h2h_result("전체 상대전적", total)

for phase, result in by_phase.items():
    print_h2h_result(phase, result)

print_team_summary(team1)
print_team_summary(team2)

generate_brief(team1, team2)