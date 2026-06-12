def get_labels(language):
    if language == "일본어":
        return {
            "opening": "#オープニング",
            "drops": "#[実況席_下段CG] Drops",
            "gem": "#[実況席_下段CG] GEMクーポン",
            "reward": "#[実況席_下段CG] 視聴報酬",
            "ticket": "#[実況席_下段CG] チケット販売",
            "event": "#[FCG] イベント",
            "previous": "#[CG] 前回試合結果",
            "standings": "#順位表",
            "today": "#本日の対戦カード",
            "today_result": "#[CG] 本日の試合結果",
            "next": "#[CG] 次回対戦カード",
            "ending": "#終了画面",
            "roster": "選手ロスター",
            "team_point": "チームポイント",
            "map_open": "#第1セット マップ公開",
            "banpick": "#BAN/PICK進行",
            "game": "#試合進行",
            "match_result": "#試合結果",
            "highlight": "#ハイライト",
            "substitution": "#選手交代 *ある場合",
            "potm": "# POTM",
            "interview": "#インタビュー進行",
            "break": "#休憩",
            "match_end": "—-----------------------------------------------試合終了—--------------------------------------------------",
        }

    return {
        "opening": "#오프닝",
        "drops": "#[중계석_하단CG] 드롭스",
        "gem": "#[중계석_하단CG] 젬 쿠폰",
        "reward": "#[중계석_하단CG] 시청보상",
        "ticket": "#[중계석_하단CG] 티켓판매",
        "event": "#[FCG] 이벤트",
        "previous": "#[CG] 지난 경기 결과",
        "standings": "#스탠딩",
        "today": "# 오늘의 매치업",
        "today_result": "#[CG] 오늘 매치 결과",
        "next": "#[CG] 넥스트 매치업",
        "ending": "# 종료 대판",
        "roster": "선수 로스터",
        "team_point": "팀포인트",
        "map_open": "# 1세트 맵 공개",
        "banpick": "#밴픽 진행",
        "game": "#경기진행",
        "match_result": "#매치결과",
        "highlight": "#하이라이트",
        "substitution": "#선수교체 *있을 경우",
        "potm": "# POTM",
        "interview": "# 인터뷰 진행",
        "break": "# 쉬는 시간",
        "match_end": "—-----------------------------------------------매치 종료—--------------------------------------------------",
    }


def format_roster(team_name, rosters, language):
    roster_text = rosters.get(team_name, "").strip()

    if not roster_text:
        if language == "일본어":
            return ["- ロスター未入力"]
        return ["- 로스터 미입력"]

    players = [p.strip() for p in roster_text.splitlines() if p.strip()]
    return [f"- {p}" for p in players]


def generate_opening(language, event_name, day_label, caster, analyst):
    lines = []

    if language == "일본어":
        lines.append(f"{caster}/ OWCSをご覧の皆さま、こんばんは。")
        lines.append(f"{event_name}、{day_label}の放送でお届けします。")
        lines.append(f"本日は解説の{analyst}さんと一緒にお送りします。よろしくお願いします。")
        lines.append(f"{analyst}/ はい、よろしくお願いします。{analyst}です。")
        lines.append(f"{caster}/ 本日の第1試合に入る前に、")
        lines.append("まずはOWCS Dropsとイベント情報を画面で確認していきましょう。")
    else:
        lines.append(f"{caster}/ 시청자 여러분 안녕하십니까! 오버워치 챔피언스 시리즈 코리아,")
        lines.append(f"{event_name} {day_label} 무대로 인사드립니다.")
        lines.append(f"오늘 도움 말씀에 {analyst} 해설과 함께합니다. 안녕하세요.")
        lines.append(f"{analyst}/ 네, 안녕하세요! {analyst}입니다.")
        lines.append(f"{caster}/ 본격적인 오늘의 첫 번째 매치로 들어가기 전에,")
        lines.append("이번 주에도 풍성하게 준비된 OWCS 드롭스 소식과 이벤트 내용 먼저 화면으로 만나보시죠.")

    return lines


def generate_previous_comment(language, caster):
    if language == "일본어":
        return [
            f"{caster}/ まずは前回の試合結果から確認していきましょう。",
            "各チームの序盤の流れと順位争いの構図が少しずつ見えてきています。",
        ]

    return [
        f"{caster}/ 먼저 지난 경기 결과부터 확인해 보겠습니다.",
        "지난 경기들을 통해 각 팀의 초반 흐름과 순위 싸움의 윤곽이 조금씩 드러나고 있습니다.",
    ]


def generate_today_matchup_comment(language, caster, today_matches):
    lines = []

    if language == "일본어":
        lines.append(f"{caster}/ それでは本日の対戦カードを確認していきましょう。")
        for i, m in enumerate(today_matches, start=1):
            lines.append(f"{i}試合目は{m['team_a']}と{m['team_b']}の対戦です。")
        lines.append("本日も各チームにとって重要な一戦が続きます。")
    else:
        lines.append(f"{caster}/ 오늘의 매치업 확인해보겠습니다.")
        for i, m in enumerate(today_matches, start=1):
            lines.append(f"{i}경기는 {m['team_a']}와 {m['team_b']}의 맞대결입니다.")
        lines.append("오늘 역시 순위 싸움의 흐름을 바꿀 수 있는 중요한 경기들이 준비되어 있습니다.")

    return lines


def generate_day_script(
    language,
    event_name,
    day_label,
    date_text,
    start_time,
    caster,
    analyst,
    previous_results,
    standings,
    today_matches,
    next_matches,
    rosters,
):
    labels = get_labels(language)
    lines = []

    lines.append(f"{event_name} {day_label}")

    if language == "일본어":
        lines.append(f"日程 {date_text} {start_time} ~ 出演 {caster}/{analyst}")
    else:
        lines.append(f"일정 {date_text} {start_time} ~ 진행 {caster}/{analyst}")
    lines.append("")

    lines.append(labels["opening"])
    lines.extend(generate_opening(language, event_name, day_label, caster, analyst))
    lines.append("")

    lines.append(labels["drops"])
    lines.append(labels["gem"])
    lines.append(labels["reward"])
    lines.append(labels["ticket"])
    lines.append(labels["event"])
    lines.append("")

    lines.append(labels["previous"])
    for r in previous_results:
        lines.append(f"{r['team_a']} {r['score_a']} - {r['score_b']} {r['team_b']}")
    lines.extend(generate_previous_comment(language, caster))
    lines.append("")

    lines.append(labels["standings"])
    for s in standings:
        if language == "일본어":
            lines.append(f"{s['rank']}位 {s['team']} {s['w']}勝 {s['l']}敗 {s['diff']}")
        else:
            lines.append(f"{s['rank']}위 {s['team']} {s['w']}승 {s['l']}패 {s['diff']}")
    lines.append("")

    lines.append(labels["today"])
    for m in today_matches:
        lines.append(f"MATCH {m['match_no']} {m['time']} {m['team_a']} vs {m['team_b']}")
    lines.extend(generate_today_matchup_comment(language, caster, today_matches))
    lines.append("")

    for i, m in enumerate(today_matches, start=1):
        if language == "일본어":
            lines.append(f">>CG OUT 後 {m['team_a']} 入場")
        else:
            lines.append(f">>CG OUT 후 {m['team_a']} 입장")

        lines.append(f"#[FCG] {m['team_a']} {labels['roster']}")
        lines.extend(format_roster(m["team_a"], rosters, language))
        lines.append(f"#M{i} {m['team_a']} {labels['team_point']}")
        lines.append("TEAM POINT TITLE")
        lines.append("チームポイント 日本語コピー" if language == "일본어" else "팀 포인트 국문 카피")
        lines.append("")

        if language == "일본어":
            lines.append(f">>CG OUT 後 {m['team_b']} 入場")
        else:
            lines.append(f">>CG OUT 후 {m['team_b']} 입장")

        lines.append(f"#[FCG] {m['team_b']} {labels['roster']}")
        lines.extend(format_roster(m["team_b"], rosters, language))
        lines.append(f"#M{i} {m['team_b']} {labels['team_point']}")
        lines.append("TEAM POINT TITLE")
        lines.append("チームポイント 日本語コピー" if language == "일본어" else "팀 포인트 국문 카피")
        lines.append("")

        lines.append(labels["map_open"])
        lines.append(labels["banpick"])
        lines.append(labels["game"])
        lines.append(labels["match_result"])
        lines.append(labels["highlight"])
        lines.append(labels["substitution"])
        lines.append(labels["match_end"])
        lines.append(labels["potm"])
        lines.append(labels["interview"])
        lines.append(labels["break"])
        lines.append("")

    lines.append(labels["today_result"])
    for m in today_matches:
        lines.append(f"{m['team_a']} 0 MATCH {m['match_no']} 0 {m['team_b']}")
    lines.append("")

    lines.append(labels["next"])
    for m in next_matches:
        lines.append(f"MATCH {m['match_no']} {m['time']} {m['team_a']} vs {m['team_b']}")
    lines.append("")

    lines.append(labels["ending"])
    lines.append("THANKS FOR")
    lines.append("WATCHING")
    lines.append("NEXT SCHEDULE")
    for m in next_matches:
        lines.append(f"{m['time']} {m['team_a']} vs {m['team_b']}")

    return "\n".join(lines)