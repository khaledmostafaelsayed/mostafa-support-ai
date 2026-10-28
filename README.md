# Mostafa Support AI (مصطفى للدعم الذكي) — Bilingual Customer Support Agent with Automated Evaluation

A bilingual Arabic/English portfolio project demonstrating a customer-support agent, Python tools, right-to-left Arabic UI, and repeatable evaluation checks. The default mode runs locally without an API key. Optional OpenAI Responses API function calling lets a model choose when to use the same local tools.

> **Demo safety:** `data/orders.json` and `data/faq.json` contain fictional sample information. Do not connect this demo to real customer data or use it to make real refunds.

## Features

- Streamlit chat interface with Arabic right-to-left support and an Arabic/English language selector.
- Brand name and taglines configurable in `config.json`.
- Three tools: order lookup, refund-window eligibility, and FAQ search.
- Optional OpenAI Responses API function calling.
- Six automated checks per language (Arabic and English) for order facts, tool use, missing IDs, unknown IDs, and refund-claim safety.
- Downloadable JSON evaluation report.
- Eleven unit tests, including Arabic chat and bilingual evaluation.

## Quick start — Windows + Visual Studio Code

1. Install Python 3.10 or newer from python.org if not already installed. In the VS Code terminal, verify:

   ```powershell
   python --version
   ```

2. Open this project folder in VS Code. Select **Terminal → New Terminal**.

3. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt in VS Code and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

4. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Launch the app:

   ```powershell
   python -m streamlit run app.py
   ```

6. In the browser, choose **العربية** or **English**. Try `فين الطلب ORD-1001؟` or `Where is order ORD-1001?`, then click the evaluation button.

## Optional: connect an OpenAI model

1. Copy `.env.example` to a new file named `.env` in the project root.
2. Put your API key after `OPENAI_API_KEY=` and optionally change `OPENAI_MODEL` to a model enabled for your account.
3. Restart Streamlit, then choose **OpenAI API** in the sidebar.

Keep `.env` private; it is included in `.gitignore`. API usage may incur charges. The local demo remains available without a key.

## Run the tests

In the VS Code terminal:

```powershell
python -m pytest -v
```

The tests use only the local data and do not call an external model. Expected result: **11 tests passed**.

## Example prompts

Arabic:
- `فين الطلب ORD-1001؟`
- `هل أقدر أسترجع الطلب ORD-1002؟`
- `مدة الشحن كام؟`

English:
- `Where is order ORD-1001?`
- `Can I get a refund for ORD-1002?`
- `I want a refund for ORD-1003`
- `How long does shipping take?`
- `What payment methods do you accept?`
- `Where is my order?`

## Customise the name

Edit `config.json` to update `brand_name`, `brand_name_en`, the two taglines, and the icon. The interface reads these settings at startup.

## Architecture

```text
app.py  (Streamlit UI)
  ├── agent.py  (local mode or OpenAI Responses API orchestration)
  ├── tools.py  (three controlled Python functions)
  ├── evaluator.py  (repeatable quality and safety assertions)
  ├── data/orders.json
  └── data/faq.json

 tests/test_project.py  (unit tests)
```

## Evaluation design

The evaluator checks expected facts, forbidden claims, and whether the appropriate tool was called. This is a lightweight deterministic baseline, not a complete measure of real-world AI quality. For production-grade evaluation, add more representative test cases, regression datasets, human review, security testing, latency/cost monitoring, and model-based evaluators.

## Two-line project summary for an application

**Built a bilingual Arabic/English customer-support agent in Python with order-lookup, refund-eligibility, and FAQ tools, plus an optional OpenAI tool-calling integration.**
**Designed Arabic and English automated regression checks for grounded answers, correct tool use, unknown-order handling, and preventing false claims that refunds were processed.**
