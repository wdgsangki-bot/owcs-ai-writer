import pandas as pd
import json

EXCEL_FILE = "OWCS KR.xlsx"

xls = pd.ExcelFile(EXCEL_FILE)

players_db = {}

for sheet_name in xls.sheet_names:
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)

    df.columns = [
        "ignore",
        "team",
        "opr_handle",
        "role",
        "last_name",
        "first_name"
    ]

    df = df.iloc[1:].copy()
    df["team"] = df["team"].ffill()

    season_data = {}

    for _, row in df.iterrows():
        team = str(row["team"]).strip()
        player = str(row["opr_handle"]).strip()
        role = str(row["role"]).strip()

        if team == "nan" or player == "nan":
            continue

        if team not in season_data:
            season_data[team] = {
                "players": [],
                "staff": []
            }

        if role == "Player":
            season_data[team]["players"].append(player)
        else:
            season_data[team]["staff"].append(player)

    players_db[sheet_name] = season_data

with open("players.json", "w", encoding="utf-8") as f:
    json.dump(players_db, f, ensure_ascii=False, indent=2)

print("players.json 생성 완료")