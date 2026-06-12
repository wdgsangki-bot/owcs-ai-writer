import json
import re
import requests
from bs4 import BeautifulSoup

URLS = [
    {
        "tournament": "2026_KR_STAGE1",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_1/Korea"
    },
    {
        "tournament": "2026_KR_STAGE2",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_2/Korea"
    },
]

TEAM_ALIASES = {
    "CR": "Crazy Raccoon",
    "FLC": "Team Falcons",
    "ZETA": "ZETA DIVISION",
    "OSG": "ONSIDE GAMING",
    "PF": "Poker Face",
    "CB": "Cheeseburger",
    "ZAN": "ZAN Esports",
    "GEN": "Gen.G Esports",
    "T1": "T1",
    "VAR": "VARREL",
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

pattern = re.compile(
    r"([A-Za-z0-9]{2,6})\s+(\d+)\s*:\s*(\d+)\s+\(Bo(\d+)\)\s+([A-Za-z0-9]{2,6})"
)


def normalize_team(short_name):
    return TEAM_ALIASES.get(short_name, short_name)


def decide_phase(score_a, score_b, bo):
    bo = int(bo)

    if bo >= 7 or score_a == 4 or score_b == 4:
        return "PLAYOFF_GRAND_FINAL"

    if bo == 5:
        return "SEEDING_DECIDER_OR_PLAYOFF"

    if bo == 3:
        return "LCQ_OR_LOWER_BRACKET"

    return "UNKNOWN_PHASE"


def scrape_playoff_matches(tournament, url):
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    found_matches = pattern.findall(text)

    matches = []

    for team_a_short, score_a, score_b, bo, team_b_short in found_matches:
        score_a = int(score_a)
        score_b = int(score_b)
        bo = int(bo)

        team_a = normalize_team(team_a_short)
        team_b = normalize_team(team_b_short)

        # 0-0 미진행 경기 제외
        if score_a == 0 and score_b == 0:
            continue

        phase = decide_phase(score_a, score_b, bo)

        matches.append({
            "tournament": tournament,
            "phase": phase,
            "date": "",
            "team_a": team_a,
            "team_b": team_b,
            "score_a": score_a,
            "score_b": score_b,
            "format": f"BO{bo}",
            "source_url": url,
            "source": "owcs_playoff_scraper_text_pattern"
        })

    return matches


def make_key(match):
    teams = sorted([match.get("team_a", ""), match.get("team_b", "")])

    return (
        match.get("tournament"),
        match.get("phase"),
        teams[0],
        teams[1],
        match.get("score_a"),
        match.get("score_b"),
        match.get("format"),
    )


all_new_matches = []

for item in URLS:
    print(f"{item['tournament']} playoff/phase 경기 수집 중...")
    new_matches = scrape_playoff_matches(item["tournament"], item["url"])
    all_new_matches.extend(new_matches)

print("\n추출 경기")
for m in all_new_matches:
    print(
        f"{m['tournament']} | {m['phase']} | "
        f"{m['team_a']} {m['score_a']} - {m['score_b']} {m['team_b']} | {m['format']}"
    )

with open("matches.json", "r", encoding="utf-8") as f:
    existing_matches = json.load(f)

existing_keys = set(make_key(m) for m in existing_matches)

added = 0

for m in all_new_matches:
    key = make_key(m)

    if key not in existing_keys:
        existing_matches.append(m)
        existing_keys.add(key)
        added += 1

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(existing_matches, f, ensure_ascii=False, indent=2)

print("\n========================")
print("저장 완료")
print("========================")
print("추가된 경기 수:", added)
print("matches.json 총 경기 수:", len(existing_matches))