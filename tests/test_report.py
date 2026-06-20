from tests.test_agent import sample_analysis

from src.report import build_markdown_report


def test_report_contains_market_sections_and_skills():
    report = build_markdown_report(sample_analysis())

    assert "# 資料分析師｜求職市場分析" in report
    assert "## 熱門技能" in report
    assert "| SQL | 2 | 高 | 必要為主 | 高 |" in report
    assert "## 職缺原文證據" in report
    assert "職缺 1：「熟悉 SQL」" in report
    assert "## 學習與作品集計畫" in report
