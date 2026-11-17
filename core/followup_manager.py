"""
Step 5: Automated Follow-up Email Manager.
Tracks sent emails, identifies unresponsive prospects, schedules follow-ups (3-5 days & 5-7 days),
and immediately halts all follow-up activity upon reply, decline, or opt-out.
Includes a timeline fast-forward feature for rapid demonstration and testing.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from config import settings, CampaignConfig
from core.database import db

logger = logging.getLogger(__name__)


FOLLOWUP_1_PROMPT = """You are a polite Brand Partnerships Director writing a friendly, low-pressure follow-up email.
The creator was emailed 3 days ago but has not replied yet.

Rules:
1. Subject: Re: [Original Subject] or quick follow-up.
2. Tone: Warm, respectful, acknowledging they receive hundreds of DMs/emails.
3. Value: Briefly remind them of the complimentary sample kit and paid collaboration.
4. Simple question: Ask if they got a chance to see the previous note.
5. Opt-out: Remind them they can reply 'unsubscribe' if not interested.

Output strict JSON:
{"subject": "Subject", "body": "Body text"}
"""

FOLLOWUP_2_PROMPT = """You are writing a graceful final follow-up email (5 days after the previous one).
This is the last outreach note before closing the file.

Rules:
1. Subject: Quick final check-in / Closing the loop.
2. Tone: Zero pressure, polite, understanding.
3. Message: Acknowledge that the timing might not be right right now. Keep the door open for future collaborations.
4. Sign-off with good wishes.

Output strict JSON:
{"subject": "Subject", "body": "Body text"}
"""


class FollowUpManager:
    def __init__(self):
        self.followup_1_days = settings.FOLLOWUP_1_DAYS
        self.followup_2_days = settings.FOLLOWUP_2_DAYS
        self.max_followups = settings.MAX_FOLLOWUPS

    def scan_for_due_followups(self) -> List[Dict[str, Any]]:
        """
        Scans all influencers in the database to identify who is due for a follow-up.
        Enforces strict stop rule: If status is Replied, Interested, Not Interested,
        or Collaboration Confirmed, follow-ups are permanently stopped.
        """
        all_creators = db.get_all_influencers()
        due_list = []
        now = datetime.now()

        for c in all_creators:
            status = c.get("status")
            # HARD STOP CONDITIONS
            if status in ["Replied", "Interested", "Not Interested", "Collaboration Confirmed", "New Lead", "Email Available"]:
                continue

            followup_count = c.get("followup_count", 0)
            if followup_count >= self.max_followups:
                continue

            sent_at_str = c.get("sent_at")
            last_followup_str = c.get("last_followup_at")

            if not sent_at_str:
                continue

            try:
                # Parse timestamps
                sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00").split(".")[0])
            except Exception:
                sent_at = now - timedelta(days=4)

            # Check eligibility for Follow-up 1
            if followup_count == 0:
                days_since_initial = (now - sent_at).days
                if days_since_initial >= self.followup_1_days:
                    due_list.append({
                        "influencer_id": c["id"],
                        "name": c["name"],
                        "username": c["username"],
                        "email": c["email"],
                        "followup_stage": 1,
                        "days_waiting": days_since_initial,
                        "status": status,
                        "reason": f"{days_since_initial} days since initial email with no reply."
                    })
                    # Mark status as Follow-up Due in CRM
                    if status != "Follow-up Due":
                        db.update_influencer_status(c["id"], "Follow-up Due")

            # Check eligibility for Follow-up 2
            elif followup_count == 1:
                try:
                    ref_time = datetime.fromisoformat(last_followup_str.replace("Z", "+00:00").split(".")[0]) if last_followup_str else sent_at
                except Exception:
                    ref_time = now - timedelta(days=6)

                days_since_fu1 = (now - ref_time).days
                if days_since_fu1 >= self.followup_2_days:
                    due_list.append({
                        "influencer_id": c["id"],
                        "name": c["name"],
                        "username": c["username"],
                        "email": c["email"],
                        "followup_stage": 2,
                        "days_waiting": days_since_fu1,
                        "status": status,
                        "reason": f"{days_since_fu1} days since Follow-up #1 with no reply."
                    })
                    if status != "Follow-up Due":
                        db.update_influencer_status(c["id"], "Follow-up Due")

        return due_list

    def draft_followup_email(self, influencer_id: int, stage: int = 1) -> Dict[str, Any]:
        """
        Drafts a tailored Follow-up #1 or Follow-up #2 and queues it for human approval.
        """
        influencer = db.get_influencer(influencer_id)
        if not influencer:
            raise ValueError(f"Influencer {influencer_id} not found.")

        # Ensure creator hasn't replied or opted out
        if influencer["status"] in ["Replied", "Interested", "Not Interested", "Collaboration Confirmed"]:
            raise ValueError(f"Follow-up stopped: Influencer status is {influencer['status']}.")

        camp = settings.default_campaign
        name = influencer.get("name", "there")
        first_name = name.split()[0]

        if stage == 1:
            subject = f"Quick follow-up for {first_name} | {camp.brand_name}"
            body = f"""Hi {first_name},

I know inboxes get flooded, so I wanted to gently bump this in case my earlier note got buried!

We'd love to gift you a complete 30-day package of our {camp.product_name} and explore a paid reel sponsorship with you.

No worries at all if you're swamped right now—just wanted to make sure the invite reached you!

Could I pop a care package in the mail for you this week?

Warmly,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}
---
{camp.opt_out_text}"""
            email_type = "followup_1"
        else:
            subject = f"Closing the loop | {camp.brand_name} x {first_name}"
            body = f"""Hi {first_name},

Quick final note from me to close the loop on this!

I completely understand you're super busy or this might not be the right fit for your schedule right now. We'll continue cheering on your incredible content from afar!

If you ever want to collaborate down the road or test out any new launches, our door is always open.

Wishing you an amazing rest of the month!

Warm regards,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}
---
{camp.opt_out_text}"""
            email_type = "followup_2"

        # Queue in database with Pending Approval
        email_id = db.create_email(
            influencer_id=influencer_id,
            recipient_email=influencer.get("email") or "collabs@instagram.com",
            email_type=email_type,
            subject=subject,
            body=body,
            approval_status="Pending Approval"
        )

        return {
            "email_id": email_id,
            "influencer_id": influencer_id,
            "stage": stage,
            "subject": subject,
            "body": body,
            "approval_status": "Pending Approval"
        }

    def fast_forward_timeline(self, days: int = 3, influencer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Demonstration tool: Shifts timestamps backwards by N days to simulate the passage of time
        and test follow-up logic immediately.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if influencer_id:
                cursor.execute("""
                    UPDATE influencers 
                    SET sent_at = datetime(sent_at, '-' || ? || ' days'),
                        last_followup_at = datetime(last_followup_at, '-' || ? || ' days')
                    WHERE id = ? AND sent_at IS NOT NULL
                """, (days, days, influencer_id))
            else:
                cursor.execute("""
                    UPDATE influencers 
                    SET sent_at = datetime(sent_at, '-' || ? || ' days'),
                        last_followup_at = datetime(last_followup_at, '-' || ? || ' days')
                    WHERE sent_at IS NOT NULL
                """, (days, days))
            conn.commit()

        # Rescan due followups
        due = self.scan_for_due_followups()
        return {
            "days_advanced": days,
            "due_followups_count": len(due),
            "due_influencers": due,
            "message": f"Successfully simulated advancing time by {days} days. {len(due)} influencers are now due for follow-ups."
        }


followup_manager = FollowUpManager()
