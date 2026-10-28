"""Bilingual customer-support agent with local demo mode and optional OpenAI tool calling.

All order records are fictional demo data. Do not connect this sample to real customer data.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from tools import check_refund_eligibility, lookup_order, search_faq

SYSTEM_INSTRUCTIONS = """You are a careful customer support assistant for a fictional portfolio demo.

Rules:
- Use the provided functions for order status, refund eligibility, and policy questions.
- Never invent order details, policy terms, dates, or completed actions.
- You may explain refund eligibility, but never claim that a refund was submitted or processed.
- If the order ID is missing for an order-specific question, ask the user for it.
- Treat the tool results as the source of truth. If information is unavailable, say so clearly.
- The tools contain fictional sample data. Do not ask for passwords, full payment-card numbers,
  one-time codes, or other sensitive authentication information.
- Be concise, polite, and helpful.
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "name": "lookup_order",
        "description": "Look up the status and estimated delivery of a fictional demo order by order ID.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. ORD-1001"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "check_refund_eligibility",
        "description": "Check whether a fictional demo order is within the 30-day return window. Does not issue a refund.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. ORD-1002"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_faq",
        "description": "Search the local demo FAQ for shipping, returns, refunds, or payment policy. Customer questions can be in Arabic or English.",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Customer's policy question in Arabic or English"}},
            "required": ["question"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _normalise_order_id(text: str) -> str | None:
    normalised = (text or "").translate(_ARABIC_DIGITS)
    match = re.search(r"\bORD[- ]?\d{4}\b", normalised, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(0).upper().replace(" ", "-")


def _run_local_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "lookup_order":
        return lookup_order(str(arguments.get("order_id", "")))
    if name == "check_refund_eligibility":
        return check_refund_eligibility(str(arguments.get("order_id", "")))
    if name == "search_faq":
        return search_faq(str(arguments.get("question", "")))
    return {"ok": False, "error": f"Unknown tool: {name}"}


def _is_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def _arabic_status(status: str) -> str:
    return {"shipped": "تم شحنه", "delivered": "تم تسليمه", "processing": "قيد التجهيز"}.get(status.lower(), status)


class SupportAgent:
    """Small agent wrapper. OpenAI mode requires OPENAI_API_KEY; local mode is offline."""

    def __init__(self, use_openai: bool = False, model: str | None = None, language: str = "en"):
        self.use_openai = bool(use_openai)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.language = "ar" if language.lower().startswith("ar") else "en"
        self.tool_calls: list[dict[str, Any]] = []

    def reply(self, message: str) -> dict[str, Any]:
        message = (message or "").strip()
        self.tool_calls = []
        if not message:
            answer = "اكتب سؤالك علشان أقدر أساعدك." if self.language == "ar" else "Please enter a message so I can help."
            return {"answer": answer, "tool_calls": [], "mode": self.mode}
        if self.use_openai:
            return self._reply_openai(message)
        return self._reply_local(message)

    @property
    def mode(self) -> str:
        return "OpenAI API" if self.use_openai else "Local demo (offline)"

    def _record_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = _run_local_tool(name, args)
        self.tool_calls.append({"tool": name, "arguments": args, "result": result})
        return result

    def _reply_local(self, message: str) -> dict[str, Any]:
        text = message.lower()
        order_id = _normalise_order_id(message)
        arabic = self.language == "ar"

        refund_terms = (
            "refund", "return", "money back", "reimburse", "استرجاع", "استرداد", "إرجاع", "ارجاع",
            "أرجع", "ارجع", "أسترجع", "استرجع", "ترجع الفلوس", "فلوسي", "رد المبلغ", "رد الأموال", "ارجع المنتج",
        )
        tracking_terms = (
            "where is", "track", "status", "delivery", "arrive", "order", "فين", "أين", "وين",
            "تتبع", "تابع", "حالة", "الطلب", "طلبي", "وصل", "مكان الطلب",
        )

        if any(term in text for term in refund_terms):
            if not order_id:
                answer = (
                    "أقدر أتحقق من سياسة الاسترجاع التجريبية. ابعت رقم الطلب، مثل ORD-1002. من فضلك لا ترسل بيانات البطاقة أو كلمات المرور."
                    if arabic else
                    "I can check the demo return policy. Please share the order ID (for example, ORD-1002). Do not share payment-card details or passwords."
                )
            else:
                result = self._record_tool("check_refund_eligibility", {"order_id": order_id})
                if result.get("ok") and result.get("eligible"):
                    answer = (
                        f"الطلب التجريبي {order_id} ضمن فترة الاسترجاع البالغة 30 يومًا، ويمكنك طلب الاسترجاع. هذا فحص للأهلية فقط؛ لم يتم تقديم طلب استرجاع أو تنفيذ أي عملية رد أموال."
                        if arabic else
                        f"Demo order {order_id} is within the 30-day return window and is eligible to request a refund. This is only an eligibility check; no refund has been submitted or processed."
                    )
                elif result.get("ok"):
                    reason = result.get("reason", "not available")
                    if arabic:
                        days = result.get("days_since_delivery")
                        if days is not None:
                            reason_ar = f"تم تسليم الطلب منذ {days} يومًا، أي خارج فترة الاسترجاع التجريبية البالغة 30 يومًا."
                        else:
                            reason_ar = "يجب تسليم الطلب أولًا قبل التحقق من فترة الاسترجاع."
                        answer = f"الطلب التجريبي {order_id} غير مؤهل حاليًا للاسترجاع وفقًا للسياسة التجريبية. السبب: {reason_ar} إذا كنت تعتقد أن هناك خطأ، تواصل مع خدمة العملاء."
                    else:
                        answer = f"Demo order {order_id} is not currently eligible under the demo return policy. Reason: {reason}. If you believe this is incorrect, contact a support representative."
                else:
                    answer = (
                        f"لم أتمكن من العثور على الطلب التجريبي {order_id}. راجع الرقم وحاول مرة أخرى."
                        if arabic else f"I couldn't find demo order {order_id}. Please check the ID and try again."
                    )
        elif any(term in text for term in tracking_terms):
            if not order_id:
                answer = (
                    "من فضلك ابعت رقم الطلب، مثل ORD-1001، علشان أبحث عنه في البيانات التجريبية. لا ترسل كلمات المرور أو بيانات بطاقات الدفع."
                    if arabic else
                    "Please share your order ID (for example, ORD-1001) so I can look it up in the demo records. Do not share passwords or payment-card details."
                )
            else:
                result = self._record_tool("lookup_order", {"order_id": order_id})
                if result.get("ok"):
                    eta = result.get("estimated_delivery")
                    if arabic:
                        status = _arabic_status(result["status"])
                        if eta:
                            eta_text = " موعد التسليم التقديري: خلال يومي عمل." if eta == "in 2 business days" else f" موعد التسليم التقديري: {eta}."
                        else:
                            eta_text = " لا يوجد موعد تسليم تقديري مسجل لهذا الطلب في البيانات التجريبية."
                        answer = f"حالة الطلب التجريبي {order_id}: {status}.{eta_text}"
                    else:
                        eta_text = f" Estimated delivery: {eta}." if eta else " No estimated delivery is available in the demo record."
                        answer = f"Demo order {order_id} is currently marked as {result['status']}.{eta_text}"
                else:
                    answer = (
                        f"لم أتمكن من العثور على الطلب التجريبي {order_id}. راجع الرقم وحاول مرة أخرى."
                        if arabic else f"I couldn't find demo order {order_id}. Please check the ID and try again."
                    )
        else:
            faq_terms = (
                "shipping", "ship", "deliver", "delivery time", "policy", "payment", "pay", "accepted",
                "business days", "return window", "how long", "الشحن", "شحن", "التوصيل", "يوصل", "وصول",
                "مدة", "كام يوم", "كم يوم", "سياسة", "الدفع", "بطاقة", "بطاقات", "أبل باي", "ابل باي",
                "وسائل الدفع", "طرق الدفع", "وقت الاسترداد", "مدة الاسترجاع", "متى يرجع المبلغ",
            )
            if any(term in text for term in faq_terms):
                result = self._record_tool("search_faq", {"question": message})
                answer = (result.get("answer_ar") if arabic else result.get("answer")) or (
                    "لم أجد إجابة مطابقة في الأسئلة الشائعة التجريبية. يُرجى التواصل مع ممثل خدمة العملاء للتأكد."
                    if arabic else "I couldn't find that in the demo FAQ. Please contact a support representative for confirmation."
                )
            elif order_id:
                result = self._record_tool("lookup_order", {"order_id": order_id})
                if result.get("ok"):
                    answer = (f"حالة الطلب التجريبي {order_id}: {_arabic_status(result['status'])}." if arabic
                              else f"Demo order {order_id} status: {result['status']}.")
                else:
                    answer = (f"لم أتمكن من العثور على الطلب التجريبي {order_id}. راجع الرقم وحاول مرة أخرى." if arabic
                              else f"I couldn't find demo order {order_id}. Please check the ID and try again.")
            else:
                answer = (
                    "أهلًا! أقدر أساعدك في تتبّع الطلبات التجريبية، والتحقق من أهلية الاسترجاع، ومعلومات الشحن وطرق الدفع. جرّب: «فين الطلب ORD-1001؟» أو «هل أقدر أسترجع الطلب ORD-1002؟»."
                    if arabic else
                    "I can help with demo order tracking, return eligibility, shipping times, and payment methods. Try: ‘Where is order ORD-1001?’ or ‘Can I get a refund for ORD-1002?’"
                )
        return {"answer": answer, "tool_calls": list(self.tool_calls), "mode": self.mode}

    def _reply_openai(self, message: str) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI package is missing. Run: python -m pip install openai") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file or choose Local demo mode.")

        language_instruction = (
            "Respond in natural Arabic. Prefer clear, friendly Modern Standard Arabic with a light conversational tone. Keep order IDs exactly as written."
            if self.language == "ar" else "Respond in English."
        )
        instructions = SYSTEM_INSTRUCTIONS + "\n\nLanguage requirement: " + language_instruction
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.responses.create(
            model=self.model,
            instructions=instructions,
            input=message,
            tools=TOOLS_SCHEMA,
        )
        # Allow a small, bounded number of tool rounds to avoid runaway tool loops.
        for _ in range(5):
            calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
            if not calls:
                answer = response.output_text or ("تعذر إنشاء الرد. حاول مرة أخرى." if self.language == "ar" else "I couldn't generate a response. Please try again.")
                return {"answer": answer, "tool_calls": list(self.tool_calls), "mode": self.mode}
            tool_outputs = []
            for call in calls:
                try:
                    args = json.loads(call.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._record_tool(call.name, args)
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                })
            response = client.responses.create(
                model=self.model,
                instructions=instructions,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=TOOLS_SCHEMA,
            )
        raise RuntimeError("The agent reached its tool-call limit. Try a simpler question.")
