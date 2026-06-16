import requests
from bs4 import BeautifulSoup
import re
import json
import os

SEASON_URLS = {
    "2025_KR_STAGE1": [
        "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_1/Korea"
    ],
    "2025_KR_STAGE2": [
        "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_2/Korea"
    ],
    "2025_KR_STAGE3": [
        "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2025/Asia/Stage_3/Korea"
    ],
    "2026_KR_STAGE1": [
        "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_1/Korea"
    ],
    "2026_KR_STAGE2": [
    "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_2/Korea/Regular_Season"
],
}

MAPS_JSON = "maps.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TEAM_ALIASES = {
    "CR": "Crazy Raccoon",
    "Crazy Raccoon": "Crazy Raccoon",
    "FLC": "Team Falcons",
    "FL": "Team Falcons",
    "Team Falcons": "Team Falcons",
    "ZETA": "ZETA DIVISION",
    "ZETA DIVISION": "ZETA DIVISION",
    "T1": "T1",
    "O2B": "O2 Blast",
    "O2 Blast": "O2 Blast",
    "PF": "Poker Face",
    "Poker Face": "Poker Face",
    "CB": "Cheeseburger",
    "Cheeseburger": "Cheeseburger",
    "SBAD": "SuperBad",
    "SuperBad": "SuperBad",
    "ZSG": "ZANSIDE GAMING",
    "ZANSIDE GAMING": "ZANSIDE GAMING",
}

TEAM_NAMES = sorted(TEAM_ALIASES.keys(), key=len, reverse=True)

MAPS = [
    "Lijiang Tower", "Busan", "Ilios", "Nepal", "Oasis",
    "Runasapi", "Esperança", "New Queen Street", "Colosseo",
    "Blizzard World", "King's Row", "Hollywood", "Eichenwalde",
    "Numbani", "Midtown", "Paraiso",
    "Havana", "Rialto", "Junkertown", "Watchpoint: Gibraltar",
    "Circuit Royal", "Dorado", "Route 66",
    "Suravasa", "New Junk City", "Aatlis",
]

def normalize_team(team):
    return TEAM_ALIASES.get(team.strip(), team.strip())

def get_series_format(score_a, score_b):
    return "FT4" if score_a == 4 or score_b == 4 else "FT3"

def make_series_key(series):
    maps_key = ",".join([m["map"] for m in series.get("maps", [])])
    return f"{series['tournament']}|{series['team_a']}|{series['team_b']}|{series['score_a']}|{series['score_b']}|{maps_key}"

def load_existing_maps():
    if not os.path.exists(MAPS_JSON):
        return []
    try:
        with open(MAPS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_maps(series_list):
    with open(MAPS_JSON, "w", encoding="utf-8") as f:
        json.dump(series_list, f, ensure_ascii=False, indent=2)

def detect_winner(a, b, team_a, team_b):
    if a > b:
        return team_a
    if b > a:
        return team_b
    return "Draw"

def extract_maps_from_block(block, team_a, team_b):
    block = block.split("MVP:")[0]
    maps = []

    for map_name in MAPS:
        if map_name not in block:
            continue

        meter = re.search(rf"(\d+(?:\.\d+)?)m\s+{re.escape(map_name)}\s+(\d+(?:\.\d+)?)m", block)
        if meter:
            a = float(meter.group(1))
            b = float(meter.group(2))
            maps.append({
                "map": map_name,
                "meter_a": a,
                "meter_b": b,
                "winner": detect_winner(a, b, team_a, team_b)
            })
            continue

        score = re.search(rf"(\d+)\s+{re.escape(map_name)}\s+(\d+)", block)
        if score:
            a = int(score.group(1))
            b = int(score.group(2))
            maps.append({
                "map": map_name,
                "score_a": a,
                "score_b": b,
                "winner": detect_winner(a, b, team_a, team_b)
            })

    return maps

def build_team_regex():
    return r"(?:" + "|".join([re.escape(t) for t in TEAM_NAMES]) + r")"

def parse_page_text(tournament, url, text):
    team_re = build_team_regex()

    patterns = [
        re.compile(rf"({team_re})\s+(\d+)\s*:\s*(\d+)\s+\(Bo\d+\)\s+({team_re})"),
        re.compile(rf"({team_re})\s+(\d+)\s*-\s*(\d+)\s+\(Bo\d+\)\s+({team_re})"),
        re.compile(rf"({team_re})\s+(\d+)\s*:\s*(\d+)\s+({team_re})"),
        re.compile(rf"({team_re})\s+(\d+)\s*-\s*(\d+)\s+({team_re})"),
    ]

    headers_found = []
    for pattern in patterns:
        headers_found = list(pattern.finditer(text))
        if headers_found:
            break

    series_list = []

    for idx, match in enumerate(headers_found):
        team_a = normalize_team(match.group(1))
        score_a = int(match.group(2))
        score_b = int(match.group(3))
        team_b = normalize_team(match.group(4))

        if score_a == 0 and score_b == 0:
            continue

        start = match.end()
        end = headers_found[idx + 1].start() if idx + 1 < len(headers_found) else start + 3000
        block = text[start:end]

        maps = extract_maps_from_block(block, team_a, team_b)
        if not maps:
            continue

        series_list.append({
            "tournament": tournament,
            "source_url": url,
            "team_a": team_a,
            "team_b": team_b,
            "score_a": score_a,
            "score_b": score_b,
            "format": get_series_format(score_a, score_b),
            "maps": maps
        })

    return series_list

def parse_html_popups(tournament, url, soup):
    series_list = []

    popups = soup.select(".brkts-match-info-popup")

    for popup in popups:
        popup_text = popup.get_text(" ", strip=True)

        if "vs" in popup_text and not re.search(r"\d+\s*-\s*\d+", popup_text):
            continue

        names = []
        for name in popup.select(".name"):
            t = name.get_text(" ", strip=True)
            if t and t not in names:
                names.append(t)

        if len(names) < 2:
            continue

        team_a = normalize_team(names[0])
        team_b = normalize_team(names[1])

        score_text = ""
        scoreholder = popup.select_one(".match-info-header-scoreholder-upper")
        if scoreholder:
            score_text = scoreholder.get_text(" ", strip=True)

        score_match = re.search(r"(\d+)\s*[-:]\s*(\d+)", score_text)
        if not score_match:
            score_match = re.search(r"(\d+)\s*[-:]\s*(\d+)", popup_text)

        if not score_match:
            continue

        score_a = int(score_match.group(1))
        score_b = int(score_match.group(2))

        if score_a == 0 and score_b == 0:
            continue

        maps = extract_maps_from_block(popup_text, team_a, team_b)
        if not maps:
            continue

        series_list.append({
            "tournament": tournament,
            "source_url": url,
            "team_a": team_a,
            "team_b": team_b,
            "score_a": score_a,
            "score_b": score_b,
            "format": get_series_format(score_a, score_b),
            "maps": maps
        })

    return series_list

def scrape_season(tournament, url):
    print(f"\n수집 시작: {tournament}")
    print(url)

    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    print("HTML 길이:", len(response.text))

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    print("TEXT 길이:", len(text))

    series_list = parse_page_text(tournament, url, text)

    if not series_list:
        print("텍스트 파싱 0건 → HTML popup 파싱 시도")
        series_list = parse_html_popups(tournament, url, soup)

    print(f"추출 시리즈 수: {len(series_list)}")

    if len(series_list) == 0:
        with open(f"debug_{tournament}.txt", "w", encoding="utf-8") as f:
            f.write(text)
        with open(f"debug_{tournament}.html", "w", encoding="utf-8") as f:
            f.write(response.text)

    return series_list

def print_series(series):
    print("\n========================")
    print(f"{series['team_a']} {series['score_a']} - {series['score_b']} {series['team_b']} ({series['format']})")
    print("========================")

    for m in series["maps"]:
        if "meter_a" in m:
            print(f"{m['map']} | {m['meter_a']}m - {m['meter_b']}m | winner: {m['winner']}")
        else:
            print(f"{m['map']} | {m['score_a']} - {m['score_b']} | winner: {m['winner']}")

def main():
    existing = load_existing_maps()
    existing_keys = set(make_series_key(s) for s in existing)

    added = 0
    skipped = 0

    for tournament, urls in SEASON_URLS.items():
        for url in urls:
            scraped = scrape_season(tournament, url)

            for series in scraped:
                key = make_series_key(series)

                if key in existing_keys:
                    skipped += 1
                    continue

                existing.append(series)
                existing_keys.add(key)
                added += 1
                print_series(series)

    save_maps(existing)

    print("\n========================")
    print("maps.json 누적 저장 완료")
    print("========================")
    print(f"신규 추가: {added}경기")
    print(f"중복 제외: {skipped}경기")
    print(f"총 저장: {len(existing)}경기")

if __name__ == "__main__":
    main()