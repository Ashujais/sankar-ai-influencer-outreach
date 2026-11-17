"""
Interactive End-to-End CLI Demo for Sankar Group AI Automation Internship.
Demonstrates all 6 required workflow steps sequentially with rich terminal output:
1. Instagram Research & Contact Collection
2. Claude AI-Based Influencer Filtering & Scoring
3. Google Sheets & CRM Sync
4. AI-Powered Cold Email Outreach & Human Approval
5. Automated Follow-up Management & Halt Mechanisms
6. AI Email Reply Management & Auto-Status Update
"""

import sys
import os
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from core.database import db
from core.instagram_research import researcher
from core.ai_filter import claude_filter
from core.google_sheets import google_sheets_crm
from core.email_engine import email_engine
from core.followup_manager import followup_manager
from core.reply_classifier import reply_classifier


def print_banner(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(step_num: int, title: str):
    print(f"\n[STEP {step_num}] >>> {title}")
    print("-" * 55)


def run_full_demo():
    print_banner("SANKAR GROUP - AI INFLUENCER OUTREACH & CRM AUTOMATION DEMO")
    print(f"Target Brand: {settings.default_campaign.brand_name}")
    print(f"Product:      {settings.default_campaign.product_name}")
    print(f"Database:     {settings.DB_PATH}")
    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 1: INSTAGRAM RESEARCH & CONTACT COLLECTION
    # -------------------------------------------------------------
    print_step(1, "Instagram Influencer Research & Contact Collection")
    print("Querying public Instagram creators for 'Health & Wellness' niche...")
    creators = researcher.search_influencers(
        niche="Health & Wellness",
        min_followers=20000,
        max_followers=200000
    )
    print(f"Found {len(creators)} matching creators with public business contact details:")
    for idx, c in enumerate(creators, 1):
        record_id, created = db.add_or_update_influencer(c)
        action_str = "Added new lead" if created else "Updated existing lead"
        print(f"  {idx}. {c['name']} (@{c['username']}) | Followers: {c['follower_count']:,} | Email: {c['email']} -> CRM [{action_str}]")

    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 2: CLAUDE AI INFLUENCER FILTERING & SCORING
    # -------------------------------------------------------------
    print_step(2, "AI-Based Influencer Filtering (Claude AI)")
    print("Submitting creator profiles to Claude AI for suitability analysis...")
    all_leads = db.get_all_influencers()

    for c in all_leads[:4]:  # Evaluate top candidates
        eval_res = claude_filter.evaluate_influencer(c, settings.default_campaign)
        db.update_ai_evaluation(c["id"], eval_res)
        print(f"\n  Creator: {c['name']} (@{c['username']})")
        print(f"    • Suitability Score: {eval_res['suitability_score']}/100 [Priority: {eval_res['priority']}]")
        print(f"    • Niche Category:    {eval_res['relevance_category']}")
        print(f"    • Claude Summary:    {eval_res['profile_summary']}")
        print(f"    • Outreach Hook:     \"{eval_res['personalization_hooks']}\"")

    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 3: GOOGLE SHEETS / CRM INTEGRATION
    # -------------------------------------------------------------
    print_step(3, "Google Sheets & CRM Integration")
    print("Exporting structured records to CSV & Excel...")
    csv_file = google_sheets_crm.export_to_csv()
    xlsx_file = google_sheets_crm.export_to_excel()
    print(f"  ✓ Exported CRM CSV:   {csv_file}")
    print(f"  ✓ Exported CRM Excel: {xlsx_file}")
    
    sheet_res = google_sheets_crm.sync_to_google_sheet()
    print(f"  ✓ Google Sheets Status: {sheet_res.get('mode')} - {sheet_res.get('message')}")

    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 4: AI-POWERED COLD EMAIL & HUMAN APPROVAL
    # -------------------------------------------------------------
    print_step(4, "AI Cold Email Outreach & Human Approval Workflow")
    target_influencer = db.get_influencer_by_username("maya.greenvibes") or all_leads[0]
    print(f"Generating personalized outreach email for {target_influencer['name']} using Claude AI...")
    
    draft = email_engine.generate_personalized_email(target_influencer["id"], settings.default_campaign)
    print("\n  --- AI-GENERATED COLD EMAIL DRAFT (Pending Human Approval) ---")
    print(f"  Subject: {draft['subject']}")
    print("  Body Preview:")
    for line in draft["body"].split("\n")[:7]:
        print(f"    | {line}")
    print("    | [...] (Includes CAN-SPAM opt-out & physical address)")

    print("\n  [Human Reviewer Action]: Reviewing and approving draft...")
    email_engine.approve_email(draft["email_id"])
    print(f"  ✓ Email ID {draft['email_id']} marked as APPROVED.")

    print("  Dispatching approved cold email through Gmail Engine...")
    send_result = email_engine.send_approved_email(draft["email_id"])
    print(f"  ✓ Dispatch Status: {send_result['status']} ({send_result['send_mode']})")
    
    updated_inf = db.get_influencer(target_influencer["id"])
    print(f"  ✓ Influencer CRM Status updated to: [{updated_inf['status']}]")

    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 5: AUTOMATED FOLLOW-UP EMAILS
    # -------------------------------------------------------------
    print_step(5, "Automated Follow-up Engine & Timeline Simulation")
    print("Checking for due follow-ups immediately...")
    due_before = followup_manager.scan_for_due_followups()
    print(f"  Follow-ups due now: {len(due_before)} (Initial email was just sent)")

    print("\n  [Fast-Forward Simulator]: Simulating passage of 4 calendar days...")
    ff_res = followup_manager.fast_forward_timeline(days=4, influencer_id=target_influencer["id"])
    print(f"  ✓ {ff_res['message']}")

    due_after = followup_manager.scan_for_due_followups()
    if due_after:
        target_due = due_after[0]
        print(f"  Trigger Activated: {target_due['name']} is now due for Follow-up #{target_due['followup_stage']}!")
        print(f"  Reason: {target_due['reason']}")

        print("  Generating Claude Follow-up #1 draft...")
        fu_draft = followup_manager.draft_followup_email(target_due["influencer_id"], stage=1)
        print(f"  ✓ Follow-up Subject: {fu_draft['subject']}")
        print(f"  ✓ Follow-up queued in Approval Queue.")

    time.sleep(1)

    # -------------------------------------------------------------
    # STEP 6: AI EMAIL REPLY MANAGEMENT & CRM AUTO-UPDATE
    # -------------------------------------------------------------
    print_step(6, "AI Email Reply Management (Claude AI)")
    print(f"Simulating incoming reply from {target_influencer['name']}...")
    
    test_reply_text = (
        "Hi Sankar team! Thanks for following up. I checked out the Morning Radiance blend and love the "
        "adaptogenic ingredient profile. I'd love to try a VIP package! What's your standard reel budget?"
    )
    print(f"\n  Incoming Message from {target_influencer['email']}:")
    print(f"  \"{test_reply_text}\"")

    print("\n  Processing with Claude AI classifier...")
    reply_res = reply_classifier.process_incoming_reply(
        influencer_id=target_influencer["id"],
        sender_email=target_influencer["email"],
        subject="Re: Collaboration inquiry",
        body=test_reply_text
    )

    print(f"  ✓ AI Classification:    [{reply_res['classification']}] (Confidence: {reply_res['confidence'] * 100:.0f}%)")
    print(f"  ✓ Sentiment Detected:   {reply_res['sentiment']}")
    print(f"  ✓ Suggested Next Step:  {reply_res['suggested_next_action']}")
    print(f"  ✓ CRM Status Updated:   [{reply_res['new_crm_status']}]")

    print("\n  --- AI-Generated Contextual Response Draft ---")
    for line in reply_res["reply_draft"].split("\n")[:6]:
        print(f"    | {line}")

    print("\n  [Human Reviewer Action]: Reviewing and approving reply...")
    approve_reply_res = reply_classifier.approve_and_send_reply(reply_res["reply_id"])
    print(f"  ✓ Approved reply dispatched. New CRM status: [{db.get_influencer(target_influencer['id'])['status']}]")

    # Verify Follow-up Halting
    print("\n  [Safety Rule Verification]: Checking follow-up state after creator replied...")
    due_final = followup_manager.scan_for_due_followups()
    halted_for_target = not any(d["influencer_id"] == target_influencer["id"] for d in due_final)
    print(f"  ✓ Immediate Stop Rule Enforced: Follow-ups for {target_influencer['name']} completely halted: {halted_for_target}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print_banner("DEMO COMPLETED SUCCESSFULLY!")
    stats = db.get_dashboard_stats()
    print("Pipeline Summary Metrics:")
    print(f"  • Total Leads in CRM:        {stats['total_leads']}")
    print(f"  • Verified Business Emails:  {stats['emails_available']}")
    print(f"  • Emails Sent:               {stats['emails_sent']}")
    print(f"  • Total Replies Processed:   {stats['total_replies']}")
    print(f"  • Collaborations Confirmed:  {stats['confirmed_count']}")
    print(f"\nStatus Breakdown across CRM:")
    for status, count in stats["status_breakdown"].items():
        if count > 0:
            print(f"  • {status:25}: {count}")

    print("\nTo launch the interactive Web Dashboard:")
    print("  Run: python app.py")
    print("  Then open: http://127.0.0.1:8000 in your browser.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_full_demo()
