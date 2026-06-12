import json
import requests
from bs4 import BeautifulSoup
import re

URL = "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_2/Korea/Regular_Season"
PLAYERS_JSON = "players.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TEAM_ALIASES = {
    "CR": "Crazy Raccoon",
    "FLC": "Team Falcons",
    "ZETA": "ZETA DIVISION",
    "T1": "T1",
    "O2B": "O2 Blast",
    "PF": "Poker Face",
    "CB": "Cheeseburger",
    "SBAD": "SuperBad",
    "ZSG": "ZANSIDE GAMING",
}

TEAM_NAMES = list(TEAM_ALIASES.values())

BANNED = {
    "Page", "Talk", "Edit", "History", "Pending changes", "Random page",
    "Stream Page", "What links here", "Related changes", "Special pages",
    "Permanent link", "Page information", "What links here globally",
    "OWWC 2026 Americas Qualifier", "OWWC 2026 Asia Qualifier",
    "Notability Guidelines", "Head to Head", "Liquipedia", "Overwatch",
    "Korea", "Japan", "China", "Asia", "Stage", "Series", "World Finals",
    "Champions Clash", "Regular Season", "Playoffs", "Standings",
    "Match Awards", "Upcoming Matches", "WDG", "Blizzard Entertainment"
}

def normalize_team(name):
    name = name.strip()
    return TEAM_ALIASES.get(name, name)

def is_player_name(name):
    name = name.strip()

    if not name:
        return False

    if name in BANNED:
        return False

    if len(name) < 2 or len(name) > 24:
        return False

    if re.fullmatch(r"\d+", name):
        return False

    if name.lower() in [t.lower() for t in TEAM_NAMES]:
        return False

    if any(word.lower() in name.lower() for word in [
        "overwatch", "liquipedia", "stage", "series", "qualifier",
        "tournament", "match", "standings", "results", "schedule",
        "world cup", "champions", "twitter", "youtube", "twitch"
    ]):
        return False

    return True

def extract_team_blocks(soup):
    """
    Stage 페이지 안에서 팀명 근처의 선수 링크를 찾는 방식.
    완전 자동 로스터 파싱 전 단계.
    """
    text = soup.get_text("\n", strip=True)

    team_blocks = {}

    for short, full in TEAM_ALIASES.items():
        positions = []

        for m in re.finditer(re.escape(short), text):
            positions.append(m.start())

        for m in re.finditer(re.escape(full), text):
            positions.append(m.start())

        if not positions:
            continue

        start = min(positions)
        end = start + 2500

        team_blocks[full] = text[start:end]

    return team_blocks

def extract_players_from_block(block, team_name):
    players = []

    lines = block.split("\n")

    for line in lines:
        line = line.strip()

        if not is_player_name(line):
            continue

        if line == team_name:
            continue

        if line in TEAM_ALIASES:
            continue

        if line not in players:
            players.append(line)

    return players[:12]

def scrape_players():
    print("수집 시작")
    print(URL)

    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    team_blocks = extract_team_blocks(soup)

    players_db = {
        "season": "2026_KR_STAGE2",
        "source_url": URL,
        "teams": {}
    }

    for team_name in TEAM_NAMES:
        print("\n========================")
        print(team_name)
        print("========================")

        block = team_blocks.get(team_name, "")

        if not block:
            print("팀 블록 없음")
            players_db["teams"][team_name] = []
            continue

        players = extract_players_from_block(block, team_name)

        if not players:
            print("선수 후보 없음")
        else:
            for i, p in enumerate(players, start=1):
                print(f"{i}. {p}")

        players_db["teams"][team_name] = players

    with open(PLAYERS_JSON, "w", encoding="utf-8") as f:
        json.dump(players_db, f, ensure_ascii=False, indent=2)

    print("\n========================")
    print("players.json 저장 완료")
    print("========================")

if __name__ == "__main__":
    scrape_players()