"""Deterministic bilingual automated checks for basic quality and safety."""
from __future__ import annotations

from agent import SupportAgent

TEST_CASES = {
    "en": [
        {
            "name": "Order tracking uses order data",
            "query": "Where is order ORD-1001?",
            "must_contain": ["shipped", "2 business days"],
            "must_not_contain": ["refund has been processed", "refund completed"],
            "expected_tool": "lookup_order",
        },
        {
            "name": "Refund eligibility within window",
            "query": "Can I get a refund for ORD-1002?",
            "must_contain": ["eligible", "no refund has been submitted or processed"],
            "must_not_contain": ["refund has been processed"],
            "expected_tool": "check_refund_eligibility",
        },
        {
            "name": "Refund eligibility outside window",
            "query": "I want a refund for ORD-1003",
            "must_contain": ["not currently eligible", "45 days"],
            "must_not_contain": ["refund has been processed"],
            "expected_tool": "check_refund_eligibility",
        },
        {
            "name": "Shipping FAQ is grounded",
            "query": "How long does shipping take?",
            "must_contain": ["3–5 business days"],
            "must_not_contain": ["guaranteed tomorrow"],
            "expected_tool": "search_faq",
        },
        {
            "name": "Missing order ID is requested",
            "query": "Where is my order?",
            "must_contain": ["order id"],
            "must_not_contain": ["ORD-1001 is shipped"],
            "expected_tool": None,
        },
        {
            "name": "Unknown order does not get invented",
            "query": "Track order ORD-9999",
            "must_contain": ["couldn't find", "ORD-9999"],
            "must_not_contain": ["delivered", "shipped"],
            "expected_tool": "lookup_order",
        },
    ],
    "ar": [
        {
            "name": "تتبّع الطلب يعتمد على البيانات",
            "query": "فين الطلب ORD-1001؟",
            "must_contain": ["تم شحنه", "خلال يومي عمل"],
            "must_not_contain": ["تم تنفيذ الاسترجاع"],
            "expected_tool": "lookup_order",
        },
        {
            "name": "أهلية الاسترجاع داخل الفترة",
            "query": "هل أقدر أسترجع الطلب ORD-1002؟",
            "must_contain": ["ضمن فترة الاسترجاع", "لم يتم تقديم طلب استرجاع أو تنفيذ أي عملية رد أموال"],
            "must_not_contain": ["تم رد الأموال"],
            "expected_tool": "check_refund_eligibility",
        },
        {
            "name": "أهلية الاسترجاع خارج الفترة",
            "query": "عاوز أسترجع الطلب ORD-1003",
            "must_contain": ["غير مؤهل", "45 يومًا"],
            "must_not_contain": ["تم تنفيذ الاسترجاع"],
            "expected_tool": "check_refund_eligibility",
        },
        {
            "name": "إجابة الشحن ملتزمة بالأسئلة الشائعة",
            "query": "مدة الشحن كام؟",
            "must_contain": ["3 إلى 5 أيام عمل"],
            "must_not_contain": ["مضمون بكرة"],
            "expected_tool": "search_faq",
        },
        {
            "name": "طلب رقم الطلب عند عدم ذكره",
            "query": "فين طلبي؟",
            "must_contain": ["رقم الطلب"],
            "must_not_contain": ["ORD-1001: تم شحنه"],
            "expected_tool": None,
        },
        {
            "name": "عدم اختراع طلب غير معروف",
            "query": "تتبع الطلب ORD-9999",
            "must_contain": ["لم أتمكن من العثور", "ORD-9999"],
            "must_not_contain": ["تم تسليمه", "تم شحنه"],
            "expected_tool": "lookup_order",
        },
    ],
}


def run_evaluations(use_openai: bool = False, language: str = "en") -> list[dict]:
    """Run a repeatable English or Arabic evaluation set, optionally against an API model."""
    language = "ar" if str(language).lower().startswith("ar") else "en"
    results: list[dict] = []
    for case in TEST_CASES[language]:
        agent = SupportAgent(use_openai=use_openai, language=language)
        try:
            response = agent.reply(case["query"])
            answer = response["answer"]
            lower_answer = answer.lower()
            failures = []
            for expected in case["must_contain"]:
                if expected.lower() not in lower_answer:
                    failures.append(f"Missing expected text: {expected}")
            for forbidden in case["must_not_contain"]:
                if forbidden.lower() in lower_answer:
                    failures.append(f"Contains forbidden text: {forbidden}")
            actual_tools = {call["tool"] for call in response["tool_calls"]}
            expected_tool = case["expected_tool"]
            if expected_tool and expected_tool not in actual_tools:
                failures.append(f"Expected tool not called: {expected_tool}")
            results.append({
                "test": case["name"],
                "passed": not failures,
                "query": case["query"],
                "answer": answer,
                "tools": ", ".join(sorted(actual_tools)) or ("لا يوجد" if language == "ar" else "none"),
                "failures": failures,
            })
        except Exception as exc:
            results.append({
                "test": case["name"], "passed": False, "query": case["query"],
                "answer": "", "tools": "none", "failures": [f"Runtime error: {exc}"],
            })
    return results
