from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent import SupportAgent
from evaluator import run_evaluations

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

try:
    BRAND = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    BRAND = {
        "brand_name": "مصطفى للدعم الذكي", "brand_name_en": "Mostafa Support AI",
        "tagline_ar": "مساعد ذكي لخدمة العملاء — تتبّع الطلبات، أهلية الاسترجاع، وتقييم الإجابات تلقائيًا",
        "tagline_en": "AI Customer Support · Order Tracking · Refund Eligibility · Automated Evaluation",
        "icon": "🤝",
    }

st.set_page_config(page_title=f"{BRAND.get('brand_name_en', 'Mostafa Support AI')} — Customer Support Agent", page_icon=BRAND.get("icon", "🤝"), layout="wide")

# Language selection is intentionally the first visible control.
with st.sidebar:
    selected_language = st.selectbox("اللغة / Language", ["العربية", "English"], index=0, key="ui_language")
LANG = "ar" if selected_language == "العربية" else "en"

T = {
    "ar": {
        "brand": BRAND.get("brand_name", "مصطفى للدعم الذكي"),
        "tagline": BRAND.get("tagline_ar", "مساعد خدمة عملاء ذكي"),
        "demo_warning": "نسخة تجريبية للـPortfolio فقط — جميع الطلبات والسياسات خيالية. لا تدخل بيانات عملاء أو مدفوعات حقيقية.",
        "configuration": "الإعدادات",
        "agent_mode": "وضع التشغيل",
        "local_mode": "تجريبي محلي (بدون API خارجي)",
        "openai_mode": "OpenAI API",
        "openai_help": "وضع OpenAI يستخدم مفتاح API الخاص بك وقد يترتب عليه رسوم استخدام.",
        "missing_key": "لم يتم العثور على OPENAI_API_KEY في ملف .env. اختر الوضع المحلي أو أضف المفتاح إلى الملف.",
        "model": "النموذج",
        "sample_orders": "طلبات تجريبية",
        "sample_note": "هذه الأرقام تعمل فقط مع بيانات المشروع التجريبية.",
        "chat_title": "جرّب مساعد خدمة العملاء",
        "clear": "مسح المحادثة",
        "welcome": "أهلًا! أقدر أساعدك في تتبّع الطلبات التجريبية، والتحقق من أهلية الاسترجاع، ومعلومات الشحن وطرق الدفع. جرّب السؤال عن الطلب ORD-1001.",
        "chat_placeholder": "اكتب سؤالك عن طلب أو سياسة...",
        "tool_activity": "سجل استخدام الأدوات",
        "request_error": "تعذر على المساعد إكمال الطلب. جرّب الوضع المحلي أو راجع إعدادات الـAPI.",
        "evaluation_title": "التقييم الآلي",
        "evaluation_description": "ينفّذ ستة اختبارات متكررة للتحقق من صحة المعلومات، واستخدام الأدوات، وتجنّب الادعاءات غير الآمنة.",
        "eval_openai": "استخدم OpenAI API في التقييم",
        "run_eval": "تشغيل مجموعة التقييم",
        "running": "جارٍ تشغيل الاختبارات...",
        "not_run": "لم يتم التشغيل بعد",
        "not_run_help": "اضغط على «تشغيل مجموعة التقييم» لعرض النتائج.",
        "run_time": "وقت التشغيل",
        "query": "السؤال",
        "answer": "الإجابة",
        "tools_called": "الأدوات المستخدمة",
        "no_answer": "لا توجد إجابة",
        "failures": "ملاحظات الاختبار",
        "download": "تنزيل تقرير التقييم (JSON)",
        "footer": "مبني باستخدام Python وStreamlit واستدعاء الأدوات والتقييم الآلي. جميع بيانات العرض خيالية، والوضع المحلي لا يحتاج إلى API خارجي.",
        "status_shipped": "تم الشحن",
        "status_delivered": "تم التسليم",
        "days_ago_5": "تم التسليم منذ 5 أيام",
        "days_ago_45": "تم التسليم منذ 45 يومًا",
        "order_tracking": "تتبع الطلبات",
    },
    "en": {
        "brand": BRAND.get("brand_name_en", "Mostafa Support AI"),
        "tagline": BRAND.get("tagline_en", "AI Customer Support · Order Tracking · Refund Eligibility · Automated Evaluation"),
        "demo_warning": "Portfolio demo only — all orders and policies are fictional. Do not enter real customer or payment data.",
        "configuration": "Configuration",
        "agent_mode": "Agent mode",
        "local_mode": "Local demo (offline)",
        "openai_mode": "OpenAI API",
        "openai_help": "OpenAI mode uses your own API key and may incur API charges.",
        "missing_key": "OPENAI_API_KEY was not found in .env. Choose Local demo or add your key to the file.",
        "model": "Model",
        "sample_orders": "Sample orders",
        "sample_note": "These IDs only work against the local fictional dataset.",
        "chat_title": "Try the support agent",
        "clear": "Clear conversation",
        "welcome": "Hi! I can help with demo order tracking, return eligibility, shipping, and payments. Try asking about ORD-1001.",
        "chat_placeholder": "Ask about an order or policy...",
        "tool_activity": "Tool activity",
        "request_error": "The agent could not complete the request. Try Local demo or check your API setup.",
        "evaluation_title": "Automated evaluation",
        "evaluation_description": "Runs six repeatable checks for factual grounding, tool usage, and unsafe claims.",
        "eval_openai": "Use OpenAI API for evaluation run",
        "run_eval": "Run evaluation suite",
        "running": "Running tests...",
        "not_run": "Not run yet",
        "not_run_help": "Click ‘Run evaluation suite’ to generate results.",
        "run_time": "Run time",
        "query": "Query",
        "answer": "Answer",
        "tools_called": "Tools called",
        "no_answer": "(no answer)",
        "failures": "Test notes",
        "download": "Download evaluation report (JSON)",
        "footer": "Built with Python, Streamlit, tool calling, and a deterministic evaluation suite. Demo records are fictional and local mode runs without an external API.",
        "status_shipped": "Shipped",
        "status_delivered": "Delivered",
        "days_ago_5": "Delivered 5 days ago",
        "days_ago_45": "Delivered 45 days ago",
        "order_tracking": "Order tracking",
    },
}[LANG]

# Lightweight custom theme and right-to-left support for Arabic.
direction = "rtl" if LANG == "ar" else "ltr"
text_align = "right" if LANG == "ar" else "left"
st.markdown(f"""
<style>
  .stApp {{ --primary-color: #3157D5; }}
  [data-testid="stAppViewContainer"] {{ direction: {direction}; }}
  [data-testid="stSidebar"] {{ direction: {direction}; }}
  .stMarkdown, .stCaption, label, [data-testid="stChatMessage"] {{ direction: {direction}; text-align: {text_align}; }}
  .stTextInput input, [data-testid="stChatInput"] textarea {{ direction: {direction}; text-align: {text_align}; }}
  pre, code, .stCode {{ direction: ltr !important; text-align: left !important; }}
  h1, h2, h3 {{ letter-spacing: -0.02em; }}
  div[data-testid="stAlert"] {{ border-radius: 12px; }}
  div[data-testid="stMetric"] {{ padding: 0.4rem 0; }}
</style>
""", unsafe_allow_html=True)

st.title(f"{BRAND.get('icon', '🤝')} {T['brand']}")
st.caption(T["tagline"])
st.info(T["demo_warning"])

with st.sidebar:
    st.header(T["configuration"])
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    mode = st.radio(T["agent_mode"], [T["local_mode"], T["openai_mode"]], index=0, help=T["openai_help"])
    use_openai = mode == T["openai_mode"]
    if use_openai and not has_key:
        st.warning(T["missing_key"])
        use_openai = False
    if use_openai:
        st.caption(f"{T['model']}: {os.getenv('OPENAI_MODEL', 'gpt-5.5')}")
    st.divider()
    st.markdown(f"**{T['sample_orders']}**")
    if LANG == "ar":
        st.code("ORD-1001  •  تم الشحن\nORD-1002  •  تم التسليم منذ 5 أيام\nORD-1003  •  تم التسليم منذ 45 يومًا")
    else:
        st.code("ORD-1001  •  Shipped\nORD-1002  •  Delivered 5 days ago\nORD-1003  •  Delivered 45 days ago")
    st.caption(T["sample_note"])

chat_col, eval_col = st.columns([1.25, 0.95], gap="large")

with chat_col:
    st.subheader(T["chat_title"])
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": T["welcome"]}]
    if st.button(T["clear"], key="clear_chat"):
        st.session_state.messages = [{"role": "assistant", "content": T["welcome"]}]
        st.rerun()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("tool_calls"):
                with st.expander(T["tool_activity"]):
                    st.json(message["tool_calls"])
    prompt = st.chat_input(T["chat_placeholder"])
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        agent = SupportAgent(use_openai=use_openai, language=LANG)
        try:
            result = agent.reply(prompt)
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"], "tool_calls": result["tool_calls"]
            })
        except Exception as exc:
            error_text = f"{T['request_error']} ({exc})" if LANG == "en" else f"{T['request_error']} ({exc})"
            st.session_state.messages.append({"role": "assistant", "content": error_text})
        st.rerun()

with eval_col:
    st.subheader(T["evaluation_title"])
    st.write(T["evaluation_description"])
    eval_with_openai = st.checkbox(T["eval_openai"], value=False, disabled=not has_key)
    if st.button(T["run_eval"], type="primary", use_container_width=True):
        with st.spinner(T["running"]):
            st.session_state.eval_results = run_evaluations(use_openai=eval_with_openai, language=LANG)
            st.session_state.eval_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            st.session_state.eval_language = LANG
    results = st.session_state.get("eval_results")
    if results is None:
        st.metric(T["latest_pass_rate"] if "latest_pass_rate" in T else ("نسبة النجاح الأخيرة" if LANG == "ar" else "Latest pass rate"), T["not_run"])
        st.caption(T["not_run_help"])
    else:
        passed = sum(1 for item in results if item["passed"])
        total = len(results)
        metric_label = "نسبة النجاح الأخيرة" if LANG == "ar" else "Latest pass rate"
        st.metric(metric_label, f"{passed}/{total} ({passed / total:.0%})")
        st.caption(f"{T['run_time']}: {st.session_state.get('eval_timestamp', '')}")
        for result in results:
            status = "✅ ناجح" if result["passed"] and LANG == "ar" else "❌ فشل" if LANG == "ar" else "✅ PASS" if result["passed"] else "❌ FAIL"
            with st.expander(f"{status} · {result['test']}"):
                st.markdown(f"**{T['query']}:** {result['query']}")
                st.markdown(f"**{T['answer']}:** {result['answer'] or T['no_answer']}")
                st.markdown(f"**{T['tools_called']}:** {result['tools']}")
                if result["failures"]:
                    st.error("\n".join(result["failures"]))
        export = {
            "generated_at_utc": st.session_state.get("eval_timestamp"),
            "language": st.session_state.get("eval_language", LANG),
            "passed": passed,
            "total": total,
            "results": results,
        }
        st.download_button(T["download"], data=json.dumps(export, ensure_ascii=False, indent=2), file_name="mostafa_support_ai_evaluation_report.json", mime="application/json", use_container_width=True)

st.divider()
st.caption(T["footer"])
