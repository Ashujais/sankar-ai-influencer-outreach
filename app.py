"""
Main Application: AI-Powered Instagram Influencer Research & Outreach Automation.
Provides FastAPI REST API and serves the interactive Dashboard UI.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings, CampaignConfig
from core.database import db
from core.instagram_research import researcher
from core.ai_filter import claude_filter
from core.google_sheets import google_sheets_crm
from core.email_engine import email_engine
from core.followup_manager import followup_manager
from core.reply_classifier import reply_classifier

app = FastAPI(
    title="AI-Powered Instagram Influencer Outreach & CRM Automation",
    description="End-to-End Automation for Discovery, Claude AI Filtering, Gmail Outreach, Follow-ups, and AI Reply Management",
    version="1.0.0"
)

# Enable CORS for local and web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Pydantic Schemas
class ResearchRequest(BaseModel):
    niche: str = "Health & Wellness"
    keywords: str = ""
    location: str = ""
    min_followers: int = 10000
    max_followers: int = 200000
    live_search: bool = False
    save_to_crm: bool = True


class InfluencerCreateRequest(BaseModel):
    name: str
    username: str
    profile_link: Optional[str] = None
    niche: str = "General"
    follower_count: int = 0
    email: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    engagement_rate: float = 3.0


class EmailApprovalRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None


class FastForwardRequest(BaseModel):
    days: int = 3
    influencer_id: Optional[int] = None


class IncomingReplyRequest(BaseModel):
    influencer_id: int
    sender_email: Optional[str] = None
    subject: str = "Re: Collaboration opportunity"
    body: str


class ReplyApprovalRequest(BaseModel):
    updated_draft: Optional[str] = None


# --- Web Page Route ---

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h2>AI Influencer Automation Backend Running. UI loading...</h2>")


# --- Metrics & Stats ---

@app.get("/api/stats")
def get_dashboard_stats():
    return db.get_dashboard_stats()


# --- Step 1: Instagram Research ---

@app.post("/api/research")
def run_research(req: ResearchRequest):
    results = researcher.search_influencers(
        niche=req.niche,
        keywords=req.keywords,
        location=req.location,
        min_followers=req.min_followers,
        max_followers=req.max_followers,
        live_search=req.live_search
    )

    saved_count = 0
    if req.save_to_crm:
        for r in results:
            _, created = db.add_or_update_influencer(r)
            if created:
                saved_count += 1

    return {
        "found_count": len(results),
        "saved_to_crm": saved_count,
        "results": results
    }


@app.post("/api/influencers/add")
def add_influencer(req: InfluencerCreateRequest):
    record_id, created = db.add_or_update_influencer(req.model_dump())
    return {
        "success": True,
        "influencer_id": record_id,
        "created": created,
        "message": "Influencer added to CRM." if created else "Existing influencer updated in CRM."
    }


@app.get("/api/influencers")
def list_influencers(status: Optional[str] = None, niche: Optional[str] = None):
    return db.get_all_influencers(status=status, niche=niche)


@app.get("/api/influencers/{influencer_id}")
def get_influencer(influencer_id: int):
    inf = db.get_influencer(influencer_id)
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found")
    emails = db.get_emails_by_influencer(influencer_id)
    return {"influencer": inf, "emails": emails}


# --- Step 2: AI-Based Influencer Filtering ---

@app.post("/api/influencers/evaluate/{influencer_id}")
def evaluate_single_influencer(influencer_id: int):
    inf = db.get_influencer(influencer_id)
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found")

    evaluation = claude_filter.evaluate_influencer(inf, settings.default_campaign)
    db.update_ai_evaluation(influencer_id, evaluation)

    # Return refreshed record
    updated_inf = db.get_influencer(influencer_id)
    return {
        "success": True,
        "influencer_id": influencer_id,
        "evaluation": evaluation,
        "influencer": updated_inf
    }


@app.post("/api/influencers/evaluate-all")
def evaluate_all_influencers():
    all_infs = db.get_all_influencers()
    evaluated = []
    for inf in all_infs:
        eval_res = claude_filter.evaluate_influencer(inf, settings.default_campaign)
        db.update_ai_evaluation(inf["id"], eval_res)
        evaluated.append({
            "id": inf["id"],
            "name": inf["name"],
            "score": eval_res["suitability_score"],
            "priority": eval_res["priority"]
        })
    return {
        "total_evaluated": len(evaluated),
        "results": evaluated
    }


# --- Step 3: Google Sheets & CRM Sync ---

@app.get("/api/export/csv")
def download_csv():
    csv_path = google_sheets_crm.export_to_csv()
    return FileResponse(
        str(csv_path),
        media_type="text/csv",
        filename="sample_influencers_crm.csv"
    )


@app.get("/api/export/excel")
def download_excel():
    xlsx_path = google_sheets_crm.export_to_excel()
    return FileResponse(
        str(xlsx_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="sample_influencers_crm.xlsx"
    )


@app.post("/api/sheets/sync")
def sync_sheets():
    result = google_sheets_crm.sync_to_google_sheet()
    return result


# --- Step 4: AI Cold Email Outreach ---

@app.get("/api/emails/pending")
def list_pending_emails():
    return db.get_pending_emails()


@app.post("/api/emails/generate/{influencer_id}")
def generate_email_draft(influencer_id: int):
    try:
        draft = email_engine.generate_personalized_email(influencer_id, settings.default_campaign)
        return draft
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/emails/batch-generate")
def batch_generate_emails(min_score: int = Query(60, ge=0, le=100)):
    drafts = email_engine.batch_generate_and_queue(min_score=min_score)
    return {"generated_count": len(drafts), "drafts": drafts}


@app.post("/api/emails/approve/{email_id}")
def approve_email(email_id: int, req: Optional[EmailApprovalRequest] = None):
    if req and (req.subject or req.body):
        email = db.get_email(email_id)
        if email:
            db.update_email_content(
                email_id,
                req.subject or email["subject"],
                req.body or email["body"]
            )
    success = email_engine.approve_email(email_id)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"success": True, "email_id": email_id, "approval_status": "Approved"}


@app.post("/api/emails/reject/{email_id}")
def reject_email(email_id: int):
    success = email_engine.reject_email(email_id)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"success": True, "email_id": email_id, "approval_status": "Rejected"}


@app.post("/api/emails/send/{email_id}")
def send_email(email_id: int):
    try:
        result = email_engine.send_approved_email(email_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/emails/batch-approve-and-send")
def batch_approve_and_send():
    pending = db.get_pending_emails()
    results = []
    for em in pending:
        email_engine.approve_email(em["id"])
        res = email_engine.send_approved_email(em["id"])
        results.append(res)
    return {"total_sent": len(results), "details": results}


# --- Step 5: Automated Follow-ups ---

@app.get("/api/followups/due")
def get_due_followups():
    due = followup_manager.scan_for_due_followups()
    return {"due_count": len(due), "influencers": due}


@app.post("/api/followups/draft/{influencer_id}")
def draft_followup(influencer_id: int, stage: int = Query(1, ge=1, le=2)):
    try:
        draft = followup_manager.draft_followup_email(influencer_id, stage=stage)
        return draft
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/followups/fast-forward")
def fast_forward_timeline(req: FastForwardRequest):
    result = followup_manager.fast_forward_timeline(days=req.days, influencer_id=req.influencer_id)
    return result


# --- Step 6: AI Reply Management ---

@app.post("/api/replies/simulate")
def simulate_incoming_reply(req: IncomingReplyRequest):
    inf = db.get_influencer(req.influencer_id)
    if not inf:
        raise HTTPException(status_code=404, detail="Influencer not found")

    sender = req.sender_email or inf.get("email") or f"{inf['username']}@gmail.com"
    result = reply_classifier.process_incoming_reply(
        influencer_id=req.influencer_id,
        sender_email=sender,
        subject=req.subject,
        body=req.body
    )
    return result


@app.get("/api/replies/pending")
def list_pending_replies():
    return db.get_pending_replies()


@app.post("/api/replies/approve/{reply_id}")
def approve_reply(reply_id: int, req: Optional[ReplyApprovalRequest] = None):
    try:
        updated_draft = req.updated_draft if req else None
        res = reply_classifier.approve_and_send_reply(reply_id, updated_text=updated_draft)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Campaign Settings ---

@app.get("/api/campaign")
def get_campaign():
    return settings.default_campaign.model_dump()


@app.post("/api/campaign")
def update_campaign(campaign: CampaignConfig):
    settings.default_campaign = campaign
    return {"success": True, "campaign": settings.default_campaign.model_dump()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
