def generate_day_script(
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
):
    lines = []

    lines.append(f"{event_name} {day_label}")
    lines.append(f"일정 {date_text} {start_time} ~ 진행 {caster}/{analyst}")
    lines.append("")

    lines.append("#오프닝")
    lines.append(f"{caster}/ 시청자 여러분 안녕하십니까! 오버워치 챔피언스 시리즈 코리아,")
    lines.append(f"{day_label} 무대로 인사드립니다.")
    lines.append(f"오늘 도움 말씀에 {analyst} 해설과 함께합니다. 안녕하세요.")
    lines.append(f"{analyst}/ 네, 안녕하세요! {analyst}입니다.")
    lines.append(f"{caster}/ 본격적인 오늘의 첫 번째 매치로 들어가기 전에,")
    lines.append("이번 주에도 풍성하게 준비된 OWCS 드롭스 소식과 이벤트 내용 먼저 화면으로 만나보시죠.")
    lines.append("")

    lines.append("#[중계석_하단CG] 드롭스")
    lines.append("#[중계석_하단CG] 젬 쿠폰")
    lines.append("#[중계석_하단CG] 시청보상")
    lines.append("#[중계석_하단CG] 티켓판매")
    lines.append("#[FCG] 이벤트")
    lines.append("")

    lines.append("#[CG] 지난 경기 결과")
    for r in previous_results:
        lines.append(f"{r['team_a']} {r['score_a']} - {r['score_b']} {r['team_b']}")
    lines.append(f"{caster}/ 먼저 지난 경기 결과부터 확인해 보겠습니다.")
    lines.append("지난 경기들을 통해 각 팀의 초반 흐름과 순위 싸움의 윤곽이 조금씩 드러나고 있습니다.")
    lines.append("")

    lines.append("#스탠딩")
    for s in standings:
        lines.append(f"{s['rank']}위 {s['team']} {s['w']}승 {s['l']}패 {s['diff']}")
    lines.append("")

    lines.append("# 오늘의 매치업")
    for m in today_matches:
        lines.append(f"MATCH {m['match_no']} {m['time']} {m['team_a']} vs {m['team_b']}")
    lines.append(f"{caster}/ 오늘의 매치업 확인해보겠습니다.")
    for i, m in enumerate(today_matches, start=1):
        lines.append(f"{i}경기는 {m['team_a']}와 {m['team_b']}의 맞대결입니다.")
    lines.append("")

    for i, m in enumerate(today_matches, start=1):
        lines.append(f">>CG OUT 후 {m['team_a']} 입장")
        lines.append(f"#[FCG] {m['team_a']} 선수 로스터")
        lines.append(f"#M{i} {m['team_a']} 팀포인트")
        lines.append("TEAM POINT TITLE")
        lines.append("팀 포인트 국문 카피")
        lines.append("")

        lines.append(f">>CG OUT 후 {m['team_b']} 입장")
        lines.append(f"#[FCG] {m['team_b']} 선수 로스터")
        lines.append(f"#M{i} {m['team_b']} 팀포인트")
        lines.append("TEAM POINT TITLE")
        lines.append("팀 포인트 국문 카피")
        lines.append("")

        lines.append("# 1세트 맵 공개")
        lines.append("#밴픽 진행")
        lines.append("#경기진행")
        lines.append("#매치결과")
        lines.append("#하이라이트")
        lines.append("#선수교체 *있을 경우")
        lines.append("—-----------------------------------------------매치 종료—--------------------------------------------------")
        lines.append("# POTM")
        lines.append("# 인터뷰 진행")
        lines.append("# 쉬는 시간")
        lines.append("")

    lines.append("#[CG] 오늘 매치 결과")
    for m in today_matches:
        lines.append(f"{m['team_a']} 0 MATCH {m['match_no']} 0 {m['team_b']}")
    lines.append("")

    lines.append("#[CG] 넥스트 매치업")
    for m in next_matches:
        lines.append(f"MATCH {m['match_no']} {m['time']} {m['team_a']} vs {m['team_b']}")
    lines.append("")

    lines.append("# 종료 대판")
    lines.append("THANKS FOR")
    lines.append("WATCHING")
    lines.append("NEXT SCHEDULE")
    for m in next_matches:
        lines.append(f"{m['time']} {m['team_a']} vs {m['team_b']}")

    return "\n".join(lines)