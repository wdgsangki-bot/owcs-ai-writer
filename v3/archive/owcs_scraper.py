import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
import time

TOURNAMENTS = [
    {
        "key": "2024_KR_STAGE1",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2024/Asia/Stage_1/Korea/Regular_Season"
    },
    {
        "key": "2024_KR_STAGE2",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2024/Asia/Stage_2/Korea/Regular_Season"
    },
    {
        "key": "2025_KR_STAGE1",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_1/Korea/Regular_Season"
    },
    {
        "key": "2025_KR_STAGE2",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_2/Korea/Regular_Season"
    },
    {
        "key": "2025_KR_STAGE3",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_3/Korea/Regular_Season"
    },
    {
        "key": "2026_KR_STAGE1",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_1/Korea/Regular_Season"
    },
    {
        "key": "2026_KR_STAGE2",
        "url": "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_2/Korea/Regular_Season"
    }
]

headers = {
    "User-Agent": "Mozilla/5.0"
}

score_pattern = re.compile(
    r"(\d+)-(\d+)\s+([A-Za-z]{3}\s+\d{1,2})"
)

all_matches = []
all_teams = {}

def fetch_html(url):
    response = requests.get(url, headers=headers, timeout=20)

    if response.status_code != 200:
        print(f"페이지 요청 실패: {response.status_code}")
        return None

    return response.text

def extract_team_names(soup):
    tables = soup.find_all("table")

    if len(tables) < 2:
        return []

    table = tables[1]

    team_names = []

    for a in table.find_all("a"):
        title = a.get("title")
        href = a.get("href", "")

        if title and href.startswith("/overwatch/"):
            if title not in team_names:
                team_names.append(title)

    return team_names

def scrape_tournament(tournament):
    key = tournament["key"]
    url = tournament["url"]

    print("\n========================")
    print(f"{key} 읽는 중")
    print("========================")
    print(url)

    html = fetch_html(url)

    if not html:
        print("HTML 없음. 스킵")
        return []

    soup = BeautifulSoup(html, "html.parser")

    team_names = extract_team_names(soup)

    if not team_names:
        print("팀명 추출 실패. 스킵")
        return []

    try:
        pandas_tables = pd.read_html(url)
    except Exception as e:
        print("pandas read_html 실패:", e)
        return []

    if len(pandas_tables) < 2:
        print("pandas 테이블 부족. 스킵")
        return []

    matrix = pandas_tables[1]

    # matrix 크기 기준으로 팀 수 보정
    team_count = min(len(team_names), len(matrix), len(matrix.columns) - 1)

    team_names = team_names[:team_count]

    print("팀 목록:")
    for i, team in enumerate(team_names):
        print(i, team)
        all_teams.setdefault(team, [team])

    matches = []

    for row_index in range(team_count):
        for col_index in range(1, team_count + 1):
            cell = str(matrix.iloc[row_index, col_index])
            found = score_pattern.search(cell)

            if not found:
                continue

            team_a = team_names[row_index]
            team_b = team_names[col_index - 1]

            if team_a == team_b:
                continue

            # 중복 제거
            if row_index > col_index - 1:
                continue

            score_a = int(found.group(1))
            score_b = int(found.group(2))
            date = found.group(3)

            matches.append({
                "tournament": key,
                "date": date,
                "team_a": team_a,
                "team_b": team_b,
                "score_a": score_a,
                "score_b": score_b
            })

    print(f"{key} 경기 수:", len(matches))

    return matches

for tournament in TOURNAMENTS:
    matches = scrape_tournament(tournament)
    all_matches.extend(matches)
    time.sleep(1)

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(all_matches, f, ensure_ascii=False, indent=2)

# teams.json은 덮어쓰지 않고, 발견 팀 목록만 별도 저장
with open("teams_found.json", "w", encoding="utf-8") as f:
    json.dump(all_teams, f, ensure_ascii=False, indent=2)

print("\n========================")
print("전체 저장 완료")
print("========================")
print("총 경기 수:", len(all_matches))
print("총 팀 수:", len(all_teams))
print("matches.json 저장 완료")
print("teams_found.json 저장 완료")