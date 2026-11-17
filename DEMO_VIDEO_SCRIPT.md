# Screen-Recorded Demo Video Script & Presentation Guide

**Assignment Title:** AI-Powered Instagram Influencer Research & Email Outreach Automation  
**Company:** Sankar Group – Department of Artificial Intelligence & Automation  
**Candidate Name / Presenter:** AI Automation Intern Candidate  
**Total Video Length:** 4–6 Minutes  
**Resolution:** 1080p Full HD (Screen + Voiceover / Webcam bubble)  

---

## 🎬 Video Overview & Timestamp Breakdown

| Timestamp | Section | Visual Focus | Goal |
|---|---|---|---|
| **0:00 - 0:45** | **1. Introduction & Architecture** | Web Dashboard Overview & Architecture Diagram | Introduce objective, tools used (Claude AI, Gmail, SQLite, Google Sheets, n8n), and pipeline. |
| **0:45 - 1:30** | **2. Step 1: Instagram Research** | Tab 1: Instagram Research | Demonstrate search by niche, location, follower count, and public business email collection. |
| **1:30 - 2:30** | **3. Step 2: Claude AI Filtering** | Tab 2: Claude AI Filtering | Show Claude AI scoring (0-100), categorization, executive summaries, and personalization hooks. |
| **2:30 - 3:15** | **4. Step 3: CRM & Google Sheets** | Tab 3: Google Sheets & CRM | Show deduplication, lifecycle status tracking, live CSV/Excel export, and Google Sheets sync. |
| **3:15 - 4:15** | **5. Step 4: Cold Email & Approval** | Tab 4: AI Cold Email | Show CAN-SPAM compliant email generation, Human-in-the-Loop review, inline editing, and dispatch. |
| **4:15 - 5:00** | **6. Step 5: Follow-up Engine** | Tab 5: Follow-ups | Demonstrate 3-5 day trigger, Time Simulator (+3 days), and automatic halt mechanism. |
| **5:00 - 6:00** | **7. Step 6: AI Reply Management** | Tab 6: Reply Manager & n8n | Simulate incoming reply, show Claude triage into 4 categories, auto CRM update, and n8n workflow. |

---

## 🎙️ Scene-by-Scene Script & Action Guide

### Scene 1: Introduction & Objective (0:00 – 0:45)
* **Screen Action:** Open browser to `http://127.0.0.1:8000/`. Show the clean Overview Dashboard displaying the 8 lifecycle statuses, KPI counters, and campaign settings.
* **Voiceover Script:**
  > *"Hello everyone! In this video, I will demonstrate my complete AI-powered Instagram Influencer Research and Email Outreach Automation system built for the Sankar Group AI Automation Internship.*  
  >  
  > *Our objective is to automate the entire influencer outreach lifecycle with minimal manual effort while maintaining high personalization, CAN-SPAM compliance, and human oversight.*  
  >  
  > *The system is powered by Anthropic's Claude AI for intelligent reasoning, a resilient SQLite CRM layer with two-way Google Sheets synchronization, Gmail for outbound outreach, and an n8n visual automation workflow export."*

---

### Scene 2: Step 1 – Instagram Influencer Research (0:45 – 1:30)
* **Screen Action:** Click on the **1. Instagram Research** tab. Enter Niche: `Health & Wellness`, Location: `Austin`, Follower range: `10,000 to 200,000`. Click **Search Influencers**. Show the discovered cards with follower counts, verified emails, and bios.
* **Voiceover Script:**
  > *"In Step 1, we identify high-fit creators based on niche, target keywords, geographic location, and follower tiers. Here you can see our ethical extraction engine querying public creator bios and contact channels.*  
  >  
  > *It collects the creator's name, Instagram handle, verified public business email, engagement rate, location, and recent post topics without violating Instagram's terms of service.*  
  >  
  > *Every discovered creator is automatically staged into our CRM database with an initial status of 'Email Available' or 'New Lead', while strictly preventing duplicate records."*

---

### Scene 3: Step 2 – AI-Based Influencer Filtering (1:30 – 2:30)
* **Screen Action:** Click on **2. Claude AI Filtering**. Click **Run Claude AI Evaluation on All Leads**. Watch the progress bars animate with suitability scores (e.g. 98/100, 84/100), priority badges (High/Medium/Low), and detailed Claude summaries.
* **Voiceover Script:**
  > *"Next in Step 2, raw influencer data is passed to Claude AI. Rather than basic keyword matching, Claude analyzes the semantic alignment between our brand—AuraWellness Organics—and the creator's content.*  
  >  
  > *Claude evaluates content authenticity, assigns a normalized Suitability Score from 0 to 100, categorizes them into specialized sub-niches like 'Holistic Wellness & Mindful Rituals', and extracts authentic personalization hooks—such as referencing Maya's recent morning adaptogen latte post.*  
  >  
  > *This guarantees our cold emails never feel like generic spam templates."*

---

### Scene 4: Step 3 – Google Sheets / CRM Integration (2:30 – 3:15)
* **Screen Action:** Click on **3. Google Sheets & CRM**. Filter by status pills (`All Leads`, `Email Available`, `Email Sent`). Click **Download CSV** and **Sync to Google Sheets**.
* **Voiceover Script:**
  > *"In Step 3, all records are stored in our structured database adhering to the 8 required lifecycle statuses: New Lead, Email Available, Email Sent, Follow-up Due, Replied, Interested, Not Interested, and Collaboration Confirmed.*  
  >  
  > *Deduplication logic ensures that re-running searches will never create duplicate entries for the same handle or email.*  
  >  
  > *With one click, the CRM exports into formatted CSV and Excel files, or synchronizes live with Google Sheets via gspread and service account credentials."*

---

### Scene 5: Step 4 – AI-Powered Cold Email Outreach (3:15 – 4:15)
* **Screen Action:** Click on **4. AI Cold Email**. Click **Batch Generate Drafts (Score ≥ 60)**. Open Maya Lin's draft. Show the personalized hook, brand introduction, value proposition, low-friction CTA, company physical address, and unsubscribe footer. Click **Approve & Send**.
* **Voiceover Script:**
  > *"Step 4 generates hyper-personalized cold outreach emails. Claude weaves in the extracted personalization hook, introduces the brand, explains the collaboration perk—a complimentary 30-day VIP kit plus a $250 sponsored reel fee—and asks a single low-friction call-to-action.*  
  >  
  > *Crucially, we mandate a Human-in-the-Loop approval gate before any email is dispatched. A human reviewer can inspect and edit the subject or body right here. Once approved, the email is sent through Gmail with anti-spam rate throttling, and the CRM status updates to 'Email Sent'."*

---

### Scene 6: Step 5 – Automated Follow-up Management (4:15 – 5:00)
* **Screen Action:** Click on **5. Follow-ups**. Point out that zero follow-ups are due right after initial send. Click the **Test Simulator: +3 Days** button. Watch Maya Lin immediately appear under **Follow-up #1 Due**. Click **Draft Follow-up #1**.
* **Voiceover Script:**
  > *"Step 5 handles intelligent follow-up sequencing. Following industry best practices, Follow-up #1 is scheduled 3–5 days after initial outreach, and Follow-up #2 after another 5–7 days.*  
  >  
  > *To demonstrate this live without waiting calendar days, I built a Timeline Fast-Forward simulator. By advancing the clock 4 days, the system immediately flags Maya Lin as 'Follow-up Due' and drafts a polite bump.*  
  >  
  > *Most importantly, the system enforces a strict halt mechanism: if a creator replies, declines, or opts out, all future follow-ups are permanently locked and cancelled."*

---

### Scene 7: Step 6 – AI Reply Management & n8n Overview (5:00 – 6:00)
* **Screen Action:** Click on **6. AI Reply Manager**. Select Maya Lin. Click the **1. Interested** or **2. Pricing Query** scenario button and click **Send & Classify with Claude AI**. Show the AI classification card, sentiment, suggested next action, drafted response, and auto CRM update to `Replied` or `Interested`. Briefly show the `n8n_influencer_outreach_workflow.json` node graph.
* **Voiceover Script:**
  > *"Finally, Step 6 handles incoming replies. When an email arrives, Claude AI classifies the message into one of four key categories: Interested, Not Interested, Pricing Enquiries, or Collaboration Requests.*  
  >  
  > *Here, Maya replied asking about budget and deliverables. Claude classified this as 'Pricing Enquiry', suggested the next action of reviewing her rate card against our $250–$400 budget, generated a tailored reply draft, and updated her CRM status to 'Replied'. Once reviewed by a human, the reply is approved with one click.*  
  >  
  > *In addition to this complete Python web application, I've also exported the full visual automation pipeline as an n8n workflow file.*  
  >  
  > *This demonstrates a complete, practical, enterprise-ready influencer outreach automation system. Thank you!"*

---

## 💡 Quick Tips for Candidate Recording:
1. Start the backend with `python app.py` and open `http://127.0.0.1:8000/`.
2. Keep OBS Studio or Loom set to capture the browser window.
3. Follow the sequence above for a smooth 5-minute presentation that covers every evaluation criteria point!
