# n8n Influencer Outreach Automation Workflow

This directory contains the production-ready n8n workflow export for the **Sankar Group AI Automation Internship Assignment**:
`n8n_influencer_outreach_workflow.json`

---

## 🛠️ Workflow Architecture in n8n

```
[Schedule Trigger / Manual Start]
               │
               ▼
[Step 1: HTTP Request - Instagram Research & Contact Collection]
               │
               ▼
[Step 2: Claude AI Profile Evaluator (LangChain / Anthropic)]
               │
               ▼
[Step 3: Google Sheets CRM Sync (Append/Update Leads)]
               │
               ▼
[Filter: Suitability Score ≥ 60 & Verified Email Present]
               │
               ▼
[Step 4: Claude AI Cold Email Drafter (CAN-SPAM Compliant)]
               │
               ▼
[Human Approval Notification (Webhook / Slack / UI Queue)]
               │
               ▼
[Gmail Node: Send Approved Cold Email (SMTP/OAuth)]
               │
               ▼
[Step 5: Wait Node: 3-5 Days Window]
               │
               ▼
[Gmail Node: Check for Incoming Creator Reply]
        ┌──────┴──────┐
  (Replied?)      (No Reply)
        │             │
        ▼             ▼
[Step 6: Claude AI   [Step 5: Claude AI
 Reply Classifier]    Follow-up #1 Drafter]
        │             │
        ▼             ▼
[Google Sheets CRM   [Gmail Node:
 Status Auto-Update]  Send Follow-up #1]
```

---

## 🚀 How to Import into n8n

1. Open your n8n workspace (self-hosted or n8n Cloud).
2. Go to **Workflows** &rarr; Click **Add Workflow**.
3. In the top right menu (`...`), select **Import from File**.
4. Choose `n8n_influencer_outreach_workflow.json` from this folder.
5. Configure your credentials:
   - **Anthropic API:** Set your Claude API key (`anthropic-credentials`).
   - **Google Sheets:** Connect OAuth2 or Google Service Account.
   - **Gmail:** Connect your Gmail account via OAuth2 or App Password SMTP.
6. Click **Activate Workflow** or test nodes individually.
