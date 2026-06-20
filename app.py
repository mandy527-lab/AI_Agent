import os

import streamlit as st
from dotenv import load_dotenv

from src.agent import analyze_job_market
from src.report import build_markdown_report
from src.resume_parser import extract_resume_text


load_dotenv()

st.set_page_config(
    page_title="Job Market Intelligence Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Job Market Intelligence Agent")
st.caption("比較多個職缺，找出市場技能需求，再用履歷證據評估你的準備方向。")

with st.sidebar:
    st.header("這個 Agent 做什麼？")
    st.markdown(
        """
1. 比較 2–5 個真實職缺
2. 統計重複出現的技能
3. 區分必要與加分條件
4. 選擇性比對履歷證據
5. 排出學習與作品集優先順序

它提供市場情報與決策支援，不替你捏造履歷或代答面試。
"""
    )
    st.divider()
    model = st.text_input(
        "Gemini 模型",
        value=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        help="可在 .env 內修改 GEMINI_MODEL。",
    )
    st.caption("資料會送到 Gemini API。免費方案請避免上傳敏感個資。")

st.subheader("1. 收集要比較的職缺")
job_count = st.number_input(
    "職缺數量",
    min_value=2,
    max_value=5,
    value=3,
    step=1,
    help="建議貼入相似職位，例如 3 個 Data Analyst 職缺。",
)

job_descriptions = []
for index in range(int(job_count)):
    job_descriptions.append(
        st.text_area(
            f"職缺 {index + 1}",
            height=180,
            key=f"job_{index}",
            placeholder="貼上公司、職稱、工作內容、必要條件與加分條件……",
        )
    )

st.subheader("2. 選擇性加入履歷")
st.write("不放履歷也能分析市場；放入後會額外顯示你的優勢與技能缺口。")
resume_file = st.file_uploader(
    "上傳履歷（選填）",
    type=["pdf", "docx", "txt"],
    help="支援文字型 PDF、Word 與純文字檔。",
)

if st.button("開始市場分析", type="primary", use_container_width=True):
    if not os.getenv("GEMINI_API_KEY"):
        st.error("找不到 GEMINI_API_KEY。請依 README 設定 .env。")
    elif sum(bool(job.strip()) for job in job_descriptions) < 2:
        st.warning("請至少貼上 2 個完整職缺。")
    else:
        try:
            resume_text = ""
            if resume_file is not None:
                resume_text = extract_resume_text(resume_file)
                if not resume_text.strip():
                    st.error("沒有讀到履歷文字。掃描版 PDF 請先進行 OCR。")
                    st.stop()

            with st.spinner("Agent 正在整理跨職缺市場需求……"):
                result = analyze_job_market(
                    job_descriptions=job_descriptions,
                    resume_text=resume_text,
                    model=model,
                )

            st.session_state["market_result"] = result
            st.session_state["used_resume"] = bool(resume_text)
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"分析失敗：{error}")
            st.info("請確認 Gemini API Key、免費額度、網路連線與模型名稱。")

if "market_result" in st.session_state:
    result = st.session_state["market_result"]
    used_resume = st.session_state.get("used_resume", False)

    st.success("市場分析完成")
    role_col, jobs_col, skills_col = st.columns([2, 1, 1])
    role_col.metric("目標職位", result.target_role)
    jobs_col.metric("分析職缺", result.total_jobs)
    skills_col.metric("技能類別", len(result.top_skills))
    st.write(result.market_summary)

    report = build_markdown_report(result)
    st.download_button(
        "下載 Markdown 報告",
        data=report,
        file_name="job-market-analysis.md",
        mime="text/markdown",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["市場技能", "職缺比較", "個人差距", "行動計畫"]
    )

    with tab1:
        st.subheader("跨職缺技能需求")
        skill_rows = [
            {
                "技能": item.skill,
                "出現職缺數": item.demand_count,
                "需求程度": item.demand_level,
                "條件類型": item.requirement_type,
                "來源職缺": ", ".join(map(str, item.source_jobs)),
            }
            for item in result.top_skills
        ]
        st.dataframe(skill_rows, use_container_width=True, hide_index=True)
        if skill_rows:
            st.bar_chart(skill_rows, x="技能", y="出現職缺數")

    with tab2:
        for job in result.job_summaries:
            with st.expander(
                f"職缺 {job.job_number}｜{job.company}｜{job.role_title}",
                expanded=True,
            ):
                for requirement in job.key_requirements:
                    st.markdown(f"- {requirement}")

    with tab3:
        if not used_resume:
            st.info("這次沒有提供履歷，因此只顯示市場分析。")
        else:
            strength_col, gap_col = st.columns(2)
            with strength_col:
                st.subheader("已有優勢")
                if result.candidate_strengths:
                    for item in result.candidate_strengths:
                        st.markdown(f"**{item.skill}**")
                        st.write(f"履歷證據：{item.resume_evidence}")
                        st.caption(item.market_relevance)
                else:
                    st.write("沒有找到能明確連結市場需求的履歷證據。")

            with gap_col:
                st.subheader("技能缺口")
                if result.skill_gaps:
                    for item in result.skill_gaps:
                        st.markdown(f"**{item.skill}｜{item.priority}優先**")
                        st.write(item.reason)
                        st.caption(f"下一步：{item.next_step}")
                else:
                    st.write("沒有發現明顯技能缺口。")

    with tab4:
        st.subheader("學習與作品集順序")
        for step in sorted(result.learning_plan, key=lambda item: item.order):
            st.markdown(f"### {step.order}. {step.focus}")
            st.write(step.action)
            st.success(f"能力證明：{step.proof_of_skill}")

        st.subheader("面試準備主題")
        for topic in result.interview_focus:
            st.markdown(f"- {topic}")
