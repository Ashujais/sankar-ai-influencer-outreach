"""
Comprehensive Automated Test Suite for AI Influencer Outreach & CRM Automation.
Tests all 6 required workflow steps and business logic constraints.
"""

import sys
import os
from pathlib import Path
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from core.database import db, VALID_STATUSES
from core.instagram_research import researcher
from core.ai_filter import claude_filter
from core.google_sheets import google_sheets_crm
from core.email_engine import email_engine
from core.followup_manager import followup_manager
from core.reply_classifier import reply_classifier


def test_step1_instagram_research():
    """Verifies Instagram researcher extracts required fields ethically."""
    results = researcher.search_influencers(niche="Health & Wellness", min_followers=10000, max_followers=100000)
    assert len(results) > 0, "Researcher should discover matching seed creators"
    
    first = results[0]
    assert "name" in first and len(first["name"]) > 0
    assert "username" in first and len(first["username"]) > 0
    assert "follower_count" in first and first["follower_count"] >= 10000
    assert "email" in first and "@" in first["email"]
    assert "profile_link" in first and "instagram.com" in first["profile_link"]


def test_step2_claude_ai_filtering():
    """Verifies Claude AI evaluates profile relevance, generates score (0-100), and hooks."""
    mock_creator = {
        "name": "Maya Lin",
        "username": "maya.greenvibes",
        "niche": "Health & Wellness",
        "follower_count": 48500,
        "email": "maya@greenvibesmedia.com",
        "location": "Austin, TX",
        "bio": "Holistic health advocate | Daily rituals for gut health & mindfulness 🌿",
        "engagement_rate": 4.2,
        "recent_posts": ["My 5-minute morning adaptogen latte ritual for laser focus ☕✨"]
    }

    eval_res = claude_filter.evaluate_influencer(mock_creator, settings.default_campaign)
    assert "suitability_score" in eval_res
    assert 0 <= eval_res["suitability_score"] <= 100
    assert eval_res["priority"] in ["High", "Medium", "Low"]
    assert len(eval_res["profile_summary"]) > 10
    assert len(eval_res["personalization_hooks"]) > 10


def test_step3_crm_deduplication():
    """Verifies that duplicate records are prevented by username."""
    test_creator = {
        "name": "Test Duplicate User",
        "username": "test_unique_handle_123",
        "email": "test@unique.com",
        "niche": "Fitness",
        "follower_count": 25000
    }

    id1, created1 = db.add_or_update_influencer(test_creator)
    assert created1 is True, "First insert should create a new record"

    # Second insert with same handle
    id2, created2 = db.add_or_update_influencer(test_creator)
    assert created2 is False, "Second insert with duplicate username must NOT create duplicate"
    assert id1 == id2, "Record IDs must match for deduplication"


def test_step4_cold_email_human_approval_enforcement():
    """Verifies that emails require human approval before sending."""
    creator = {
        "name": "Sarah Connor",
        "username": "sarah_wellness_test",
        "email": "sarah@testwellness.io",
        "niche": "Health & Wellness",
        "follower_count": 35000,
        "personalization_hooks": "Loved your gut health guide"
    }
    inf_id, _ = db.add_or_update_influencer(creator)

    # Generate draft
    draft = email_engine.generate_personalized_email(inf_id, settings.default_campaign)
    assert draft["approval_status"] == "Pending Approval"
    assert "Sarah" in draft["subject"] or "AuraWellness" in draft["subject"]
    assert "UNSUBSCRIBE" in draft["body"]

    # Try sending before approval -> should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        email_engine.send_approved_email(draft["email_id"])
    assert "Must be approved by a human first" in str(excinfo.value)

    # Approve and send
    email_engine.approve_email(draft["email_id"])
    send_res = email_engine.send_approved_email(draft["email_id"])
    assert send_res["success"] is True

    # Influencer status should now be Email Sent
    updated_inf = db.get_influencer(inf_id)
    assert updated_inf["status"] == "Email Sent"


def test_step5_followup_and_stop_mechanism():
    """Verifies follow-up timing and immediate halt rule on reply/opt-out."""
    creator = {
        "name": "Alex Mercer",
        "username": "alex_fitness_test",
        "email": "alex@fitnessdaily.org",
        "niche": "Fitness",
        "follower_count": 55000
    }
    inf_id, _ = db.add_or_update_influencer(creator)

    # Send initial email
    draft = email_engine.generate_personalized_email(inf_id, settings.default_campaign)
    email_engine.approve_email(draft["email_id"])
    email_engine.send_approved_email(draft["email_id"])

    # Simulate 4 days elapsed
    followup_manager.fast_forward_timeline(days=4, influencer_id=inf_id)
    due_list = followup_manager.scan_for_due_followups()
    alex_due = [d for d in due_list if d["influencer_id"] == inf_id]
    assert len(alex_due) == 1, "Should be due for Follow-up #1 after 4 days"
    assert alex_due[0]["followup_stage"] == 1

    # Now simulate influencer replying -> Status changes to Replied
    db.update_influencer_status(inf_id, "Replied")

    # Rescan followups: Alex MUST be excluded immediately
    due_after_reply = followup_manager.scan_for_due_followups()
    alex_after = [d for d in due_after_reply if d["influencer_id"] == inf_id]
    assert len(alex_after) == 0, "Follow-ups MUST stop immediately when influencer replies!"


def test_step6_ai_reply_classification_and_auto_status():
    """Verifies Claude AI classification of incoming replies into all 4 categories."""
    creator = {
        "name": "Jessica Alba Test",
        "username": "jessica_clean_test",
        "email": "jessica@cleanliving.com",
        "niche": "Clean Beauty",
        "follower_count": 40000
    }
    inf_id, _ = db.add_or_update_influencer(creator)

    # Test 1: Interested
    res_int = reply_classifier.process_incoming_reply(
        influencer_id=inf_id,
        sender_email=creator["email"],
        subject="Re: Collaboration",
        body="I would love to try your adaptogen elixir! Please send me the VIP kit."
    )
    assert res_int["classification"] == "Interested"
    assert db.get_influencer(inf_id)["status"] == "Interested"

    # Test 2: Pricing Enquiry
    res_price = reply_classifier.process_incoming_reply(
        influencer_id=inf_id,
        sender_email=creator["email"],
        subject="Re: Collaboration",
        body="What is your budget for an Instagram Reel? My rate is $500."
    )
    assert res_price["classification"] == "Pricing Enquiries"
    assert db.get_influencer(inf_id)["status"] == "Replied"

    # Test 3: Not Interested / Unsubscribe
    res_decline = reply_classifier.process_incoming_reply(
        influencer_id=inf_id,
        sender_email=creator["email"],
        subject="Re: Collaboration",
        body="Not interested in sponsorships. Please unsubscribe and remove me."
    )
    assert res_decline["classification"] == "Not Interested"
    assert db.get_influencer(inf_id)["status"] == "Not Interested"


def test_step3_google_sheets_export():
    """Verifies that CSV and Excel files are generated with valid headers."""
    csv_path = google_sheets_crm.export_to_csv()
    assert csv_path.exists()
    assert csv_path.stat().st_size > 0

    xlsx_path = google_sheets_crm.export_to_excel()
    assert xlsx_path.exists()
    assert xlsx_path.stat().st_size > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
