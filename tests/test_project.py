import unittest

from agent import SupportAgent
from evaluator import run_evaluations
from tools import check_refund_eligibility, lookup_order, search_faq


class ToolTests(unittest.TestCase):
    def test_order_lookup_known_order(self):
        result = lookup_order("ORD-1001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "Shipped")
        self.assertEqual(result["estimated_delivery"], "in 2 business days")

    def test_order_lookup_unknown_order(self):
        self.assertFalse(lookup_order("ORD-9999")["ok"])

    def test_refund_eligible_within_30_days(self):
        result = check_refund_eligibility("ORD-1002")
        self.assertTrue(result["ok"])
        self.assertTrue(result["eligible"])

    def test_refund_not_eligible_after_30_days(self):
        result = check_refund_eligibility("ORD-1003")
        self.assertTrue(result["ok"])
        self.assertFalse(result["eligible"])

    def test_faq_shipping(self):
        result = search_faq("How long does shipping take?")
        self.assertTrue(result["ok"])
        self.assertIn("3–5 business days", result["answer"])


class AgentTests(unittest.TestCase):
    def test_local_agent_uses_order_tool(self):
        result = SupportAgent().reply("Where is order ORD-1001?")
        self.assertIn("shipped", result["answer"].lower())
        self.assertEqual(result["tool_calls"][0]["tool"], "lookup_order")

    def test_local_agent_will_not_claim_refund_processed(self):
        result = SupportAgent().reply("Can I get a refund for ORD-1002?")
        self.assertIn("eligible", result["answer"].lower())
        self.assertIn("no refund has been submitted or processed", result["answer"].lower())

    def test_evaluation_suite_passes_offline(self):
        results = run_evaluations(use_openai=False)
        self.assertEqual(len(results), 6)
        failures = [item for item in results if not item["passed"]]
        self.assertEqual(failures, [], msg=str(failures))

    def test_arabic_agent_tracks_order(self):
        result = SupportAgent(language="ar").reply("فين الطلب ORD-1001؟")
        self.assertIn("تم شحنه", result["answer"])
        self.assertEqual(result["tool_calls"][0]["tool"], "lookup_order")

    def test_arabic_faq_shipping(self):
        result = SupportAgent(language="ar").reply("مدة الشحن كام؟")
        self.assertIn("3 إلى 5 أيام عمل", result["answer"])
        self.assertEqual(result["tool_calls"][0]["tool"], "search_faq")

    def test_arabic_evaluation_suite_passes_offline(self):
        results = run_evaluations(use_openai=False, language="ar")
        self.assertEqual(len(results), 6)
        failures = [item for item in results if not item["passed"]]
        self.assertEqual(failures, [], msg=str(failures))


if __name__ == "__main__":
    unittest.main()
