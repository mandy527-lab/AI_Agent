from src.models import MarketAnalysis


def build_markdown_report(result: MarketAnalysis) -> str:
    """Turn a structured market analysis into a portable Markdown report."""
    lines = [
        f"# {result.target_role}｜求職市場分析",
        "",
        f"分析職缺數：{result.total_jobs}",
        "",
        "## 市場摘要",
        "",
        result.market_summary,
        "",
        "## 熱門技能",
        "",
        "| 技能 | 出現職缺數 | 需求程度 | 條件類型 |",
        "|---|---:|---|---|",
    ]

    for skill in result.top_skills:
        lines.append(
            f"| {skill.skill} | {skill.demand_count} | "
            f"{skill.demand_level} | {skill.requirement_type} |"
        )

    lines.extend(["", "## 個人優勢", ""])
    if result.candidate_strengths:
        for strength in result.candidate_strengths:
            lines.append(
                f"- **{strength.skill}**：{strength.resume_evidence} "
                f"（{strength.market_relevance}）"
            )
    else:
        lines.append("- 未提供履歷，因此沒有進行個人能力判斷。")

    lines.extend(["", "## 技能缺口", ""])
    if result.skill_gaps:
        for gap in result.skill_gaps:
            lines.append(
                f"- **{gap.skill}（{gap.priority}優先）**："
                f"{gap.reason} 下一步：{gap.next_step}"
            )
    else:
        lines.append("- 未提供履歷，或沒有發現有證據支持的技能缺口。")

    lines.extend(["", "## 學習與作品集計畫", ""])
    for step in sorted(result.learning_plan, key=lambda item: item.order):
        lines.append(
            f"{step.order}. **{step.focus}**：{step.action} "
            f"能力證明：{step.proof_of_skill}"
        )

    lines.extend(["", "## 面試準備主題", ""])
    lines.extend(f"- {topic}" for topic in result.interview_focus)
    lines.append("")
    return "\n".join(lines)

