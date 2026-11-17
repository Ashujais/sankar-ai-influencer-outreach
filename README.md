# AI-Powered Instagram Influencer Research & Email Outreach Automation

> **Sankar Group – AI Automation Internship Practical Project Assignment**  
> **Department:** Artificial Intelligence & Automation  
> **Tools:** Claude AI, Instagram, Gmail, Google Sheets, n8n, Python, FastAPI, SQLite  

An end-to-end, production-ready AI automation system that discovers Instagram influencers in targeted niches, collects their publicly available business contact details, filters and scores them using Claude AI, manages leads in a deduplicated CRM synced with Google Sheets, drafts hyper-personalized CAN-SPAM compliant cold emails with human-in-the-loop approval, schedules automated follow-ups (3–5 days & 5–7 days), and intelligently classifies incoming email replies to draft responses and update CRM statuses automatically.

---

## 🌟 Key Features & Workflow Highlights

```
Instagram Research ➔ Contact Collection ➔ Claude AI Filtering ➔ Google Sheets / CRM
       ➔ Personalized Gmail Outreach ➔ Automated Follow-ups ➔ Reply Detection
       ➔ Claude AI Reply Draft ➔ CRM Auto-Status Update
```

- **Step 1: Ethical Instagram Research & Contact Collection**
  - Search public creator profiles by niche, keywords, geographic location, and follower tiers (10k–500k+).
  - Collects: Creator Name, Handle, Profile URL, Verified Public Business Email, Follower Count, Location, Bio, and Engagement Rate.
  - Ethical public web extraction compliant with Instagram's terms of service.
- **Step 2: AI-Based Influencer Filtering with Claude AI**
  - Evaluates brand alignment against campaign guidelines.
  - Assigns a normalized **Suitability Score (0–100)** and Priority (**High / Medium / Low**).
  - Generates a 2–3 sentence executive summary and extracts authentic **personalization hooks** from creator bios and recent posts.
- **Step 3: Google Sheets & CRM Integration**
  - ACID-compliant SQLite CRM database with uniqueness constraints preventing duplicate records.
  - Supports all 8 required lifecycle statuses: `New Lead`, `Email Available`, `Email Sent`, `Follow-up Due`, `Replied`, `Interested`, `Not Interested`, `Collaboration Confirmed`.
  - One-click export to formatted **CSV** and **Excel** files, plus direct two-way sync with **Google Sheets API** via `gspread`.
- **Step 4: AI Cold Email Outreach & Human Approval**
  - Claude AI crafts personalized 1-on-1 emails incorporating extracted talking points.
  - Fully compliant with **CAN-SPAM & GDPR** (sender identification, valid physical corporate address, and a prominent opt-out mechanism).
  - **Mandatory Human-in-the-Loop Approval:** Emails enter a review queue where operators can edit subjects/bodies inline and approve before sending.
  - Safe dispatch through **Gmail SMTP** or throttled test sandbox with anti-spam daily sending limits (50/day).
- **Step 5: Automated Follow-up Sequences & Hard Stop Rules**
  - Follow-up #1 scheduled after 3–5 days; Follow-up #2 after another 5–7 days (max 2 follow-ups).
  - **Immediate Cancellation Mechanism:** If the creator replies, expresses interest, declines, or opts out, all follow-ups are immediately locked and canceled!
  - Built-in **Timeline Fast-Forward Simulator** (`+3 Days`, `+5 Days`) to test and demonstrate follow-up triggers in real-time.
- **Step 6: AI Reply Management & CRM Auto-Update**
  - Ingests incoming emails and uses Claude AI to classify intent into 4 core categories:
    1. `Interested` (Wants sample product, shares shipping address)
    2. `Pricing Enquiries` (Asks for reel budget, shares rate card)
    3. `Collaboration Requests` (Proposes specific deliverables or dates)
    4. `Not Interested` (Declines or requests opt-out)
  - Detects sentiment, suggests actionable next steps, drafts tailored responses, and auto-updates CRM statuses.
  - AI-generated reply drafts require human approval before dispatch.
- **Visual n8n Platform Integration**
  - Includes a full workflow export file (`n8n/n8n_influencer_outreach_workflow.json`) with nodes for Webhooks, Claude AI LangChain agents, Google Sheets, and Gmail.

---

## 📁 Repository Structure

```
f:\Sankar_AI\
├── app.py                      # FastAPI Backend Server & UI Host
├── config.py                   # App Configuration, Campaign Presets, Environment Variables
├── requirements.txt            # Python Dependencies
├── influencer_crm.db           # SQLite CRM Database with complete lifecycle
│
├── core/
│   ├── database.py             # SQLite Schema, Deduplication, Status Transitions
│   ├── instagram_research.py   # Step 1: Ethical Public Instagram Discovery
│   ├── ai_filter.py            # Step 2: Claude AI Scoring (0-100) & Profile Analysis
│   ├── google_sheets.py        # Step 3: Google Sheets API & CSV/XLSX Sync
│   ├── email_engine.py         # Step 4: Claude Cold Email Drafter & Human Approval Queue
│   ├── followup_manager.py     # Step 5: Follow-up Sequencer & Timeline Simulator
│   └── reply_classifier.py     # Step 6: AI Reply Triage, Response Drafter, Auto-Update
│
├── static/
│   ├── index.html              # Sleek, Responsive Tailwind CSS Dashboard UI
│   ├── style.css               # Status Badge Styles & Animations
│   └── app.js                  # Frontend Application Logic & Real-Time Sync
│
├── exports/
│   ├── sample_influencers_crm.csv   # Sample CRM CSV with test records
│   └── sample_influencers_crm.xlsx  # Formatted Excel Workbook with colored statuses
│
├── samples/
│   ├── sample_initial_email.md      # Sample Cold Outreach Email
│   ├── sample_followup_email_1.md   # Sample Follow-up #1 (3-5 Days)
│   ├── sample_followup_email_2.md   # Sample Final Follow-up #2 (5-7 Days)
│   └── sample_ai_reply_drafts.md    # Verified AI Replies across all 4 categories
│
├── n8n/
│   ├── n8n_influencer_outreach_workflow.json  # Complete n8n Workflow JSON Export
│   └── README_n8n.md                          # Guide to import & run in n8n
│
├── tests/
│   ├── test_workflow.py        # Automated Pytest Suite (7/7 Passing Tests)
│   └── run_demo_cli.py         # Standalone End-to-End CLI Demo Runner
│
├── DEMO_VIDEO_SCRIPT.md        # Scene-by-Scene Video Presentation Walkthrough Script
├── SYSTEM_ARCHITECTURE.md      # Detailed Architecture, Schemas, Anti-Spam & Prompts
└── README.md                   # Project Documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- (Optional) Anthropic API key and Gmail App Password for live sending

### 2. Installation
Clone the repository and install dependencies:
```bash
cd f:\Sankar_AI
pip install -r requirements.txt
```

### 3. Environment Variables (Optional)
Create a `.env` file in the root directory (the application operates with high-fidelity fallback simulation if no keys are provided):
```env
# Optional: Live Claude AI Key
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: Live Gmail SMTP Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
MOCK_EMAIL_SENDING=False

# Optional: Google Sheets Sync
GOOGLE_SHEET_ID=your-google-sheet-id
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
```

### 4. Running the Interactive Web Dashboard
Launch the FastAPI application:
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

From the dashboard you can:
1. Search and discover influencers in Step 1.
2. Run Claude AI evaluation with one click in Step 2.
3. Manage CRM leads, filter statuses, and download CSV/Excel in Step 3.
4. Review, edit, approve, and send cold emails in Step 4.
5. Fast-forward the timeline by 3–5 days to test follow-up sequencing in Step 5.
6. Simulate incoming replies (Interested, Pricing, Collab, Decline) and watch Claude classify and draft replies in Step 6!

### 5. Running the Automated CLI Demonstration
To run a complete end-to-end terminal demo:
```bash
python tests/run_demo_cli.py
```

### 6. Running Automated Tests
Run the pytest test suite verifying all 6 workflow steps:
```bash
python -m pytest tests/test_workflow.py -v
```
Output:
```
tests/test_workflow.py::test_step1_instagram_research PASSED             [ 14%]
tests/test_workflow.py::test_step2_claude_ai_filtering PASSED            [ 28%]
tests/test_workflow.py::test_step3_crm_deduplication PASSED              [ 42%]
tests/test_workflow.py::test_step4_cold_email_human_approval_enforcement PASSED [ 57%]
tests/test_workflow.py::test_step5_followup_and_stop_mechanism PASSED    [ 71%]
tests/test_workflow.py::test_step6_ai_reply_classification_and_auto_status PASSED [ 85%]
tests/test_workflow.py::test_step3_google_sheets_export PASSED           [100%]
============================== 7 passed in 14.08s ==============================
```

---

## 📋 Evaluation Criteria & Compliance Checklist

| Required Area | Weight | Implemented Solution |
|---|---|---|
| **Instagram Research & Data Collection** | 20% | Niche, keyword, location, follower filters; collects verified public emails, handles, engagement rates ethically without API abuse. |
| **Claude AI Integration & Personalization** | 20% | Semantic brand-creator matching, 0–100 suitability scoring, niche categorization, and specific content talking points. |
| **Gmail Automation & Follow-ups** | 20% | Dual SMTP / sandbox mailer, anti-spam rate limiting, CAN-SPAM compliant footers, human review queue, 3–5d / 5–7d sequencing, and immediate halt on response. |
| **AI Reply Management** | 20% | Triage across 4 categories (`Interested`, `Not Interested`, `Pricing Enquiries`, `Collaboration Requests`), sentiment analysis, tailored reply drafting, and auto CRM updates. |
| **End-to-End Workflow & Demo** | 20% | Interactive Web App (`app.py`), CLI demo runner (`tests/run_demo_cli.py`), n8n export (`n8n/`), video recording script (`DEMO_VIDEO_SCRIPT.md`), and sample outputs. |

---

## 📄 License & Attribution
Built for the **Sankar Group AI Automation Internship Assignment**.  
Developed with Python 3.12, FastAPI, Anthropic Claude AI, SQLite3, and n8n.
