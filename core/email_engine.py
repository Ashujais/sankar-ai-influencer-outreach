"""
Step 4: AI-Powered Cold Email Outreach Engine.
Uses Claude AI to craft hyper-personalized outreach emails compliant with CAN-SPAM / GDPR.
Enforces human approval before sending and includes real Gmail SMTP & simulated sending.
"""

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import anthropic
from config import settings, CampaignConfig
from core.database import db

logger = logging.getLogger(__name__)


COLD_EMAIL_SYSTEM_PROMPT = """You are an elite Brand Partnerships Director who writes authentic, warm, and highly converting influencer outreach emails.
You avoid generic marketing fluff, corporate jargon, and spammy buzzwords.
Your emails feel like a thoughtful 1-on-1 note from one human to another.

Key Rules:
1. Subject Line: Personalized, conversational, 4-7 words (e.g., 'Maya x AuraWellness | Your morning adaptogen post').
2. Hook: Greet the creator by first name and specifically reference the personalization hook provided (their post, bio, or niche).
3. The Brand & Product: Introduce the brand and why their specific aesthetic/values match.
4. The Proposition: Clearly explain the collaboration offer (gifted package, paid fee, or affiliate).
5. Low-Friction Call to Action: A simple, pressure-free question (e.g. 'Can I send a complimentary box to your PO Box or studio?').
6. Sender Sign-off: Full name, title, brand name.
7. Anti-Spam Compliance: Include physical mailing address and an opt-out unsubscribe statement at the footer.

Output format must be strict JSON:
{
  "subject": "Email Subject",
  "body": "Full email body in plaintext with linebreaks."
}
"""


class ColdEmailEngine:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def generate_personalized_email(
        self,
        influencer_id: int,
        campaign: Optional[CampaignConfig] = None
    ) -> Dict[str, Any]:
        """
        Generates a personalized cold email using Claude AI and queues it for human approval.
        """
        influencer = db.get_influencer(influencer_id)
        if not influencer:
            raise ValueError(f"Influencer with ID {influencer_id} not found.")

        camp = campaign or settings.default_campaign
        email_content = self._draft_with_claude(influencer, camp)

        # Save to database in 'Pending Approval' state
        email_id = db.create_email(
            influencer_id=influencer_id,
            recipient_email=influencer.get("email") or "collabs@instagram.com",
            email_type="initial",
            subject=email_content["subject"],
            body=email_content["body"],
            approval_status="Pending Approval"
        )

        return {
            "email_id": email_id,
            "influencer_id": influencer_id,
            "influencer_name": influencer.get("name"),
            "recipient_email": influencer.get("email"),
            "subject": email_content["subject"],
            "body": email_content["body"],
            "approval_status": "Pending Approval",
            "sent_status": "Draft"
        }

    def _draft_with_claude(self, influencer: Dict[str, Any], camp: CampaignConfig) -> Dict[str, str]:
        if self.client and self.api_key:
            try:
                user_prompt = f"""
BRAND INFO:
- Brand: {camp.brand_name}
- Product: {camp.product_name} - {camp.product_description}
- Offer: {camp.collaboration_type}
- CTA: {camp.call_to_action}
- Sender: {camp.sender_name}, {camp.sender_title}
- Physical Address: {camp.company_address}
- Opt-out text: {camp.opt_out_text}

INFLUENCER DETAILS:
- Name: {influencer.get('name')}
- Username: @{influencer.get('username')}
- Niche: {influencer.get('niche')}
- Location: {influencer.get('location')}
- Personalization Hook: {influencer.get('personalization_hooks')}
- Summary: {influencer.get('profile_summary')}

Generate a warm, high-converting cold email for this creator.
"""
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=700,
                    temperature=0.4,
                    system=COLD_EMAIL_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                text = response.content[0].text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                import json
                return json.loads(text)
            except Exception as e:
                logger.warning(f"Claude API generation failed ({e}). Falling back to template engine.")
                return self._simulate_email_draft(influencer, camp)
        else:
            return self._simulate_email_draft(influencer, camp)

    def _simulate_email_draft(self, influencer: Dict[str, Any], camp: CampaignConfig) -> Dict[str, str]:
        """High-converting contextual email template mimicking Claude's output."""
        name = influencer.get("name", "there")
        first_name = name.split()[0]
        hook = influencer.get("personalization_hooks") or f"I came across your inspiring posts on {influencer.get('niche', 'wellness')} and loved your authentic perspective."

        subject = f"{first_name} x {camp.brand_name} | Loved your content!"
        body = f"""Hi {first_name},

Hope you're having a wonderful week!

{hook}

I'm reaching out from {camp.brand_name}. We recently launched our {camp.product_name} ({camp.product_description}). We are huge admirers of the mindful, health-first community you've cultivated on Instagram.

We would love to partner with you for an upcoming campaign:
• {camp.collaboration_type}
• Complete creative freedom in how you share with your audience

{camp.call_to_action}

If you're interested, just let me know and I'll send over the details right away!

Warm regards,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}
{camp.sender_email}

{camp.company_address}
---
{camp.opt_out_text}"""
        return {"subject": subject, "body": body}

    # --- Approval & Sending ---

    def approve_email(self, email_id: int) -> bool:
        """Approves a drafted email for sending."""
        email = db.get_email(email_id)
        if not email:
            return False
        db.update_email_status(email_id, approval_status="Approved", sent_status="Queued")
        return True

    def reject_email(self, email_id: int) -> bool:
        """Rejects a drafted email."""
        email = db.get_email(email_id)
        if not email:
            return False
        db.update_email_status(email_id, approval_status="Rejected", sent_status="Draft")
        return True

    def send_approved_email(self, email_id: int) -> Dict[str, Any]:
        """
        Sends an approved email through Gmail SMTP or simulated safe sandbox.
        Updates influencer status to 'Email Sent' and records timestamps.
        """
        email = db.get_email(email_id)
        if not email:
            raise ValueError(f"Email ID {email_id} not found.")

        if email["approval_status"] != "Approved":
            raise ValueError(f"Email {email_id} cannot be sent: Must be approved by a human first (current: {email['approval_status']}).")

        recipient = email["recipient_email"]
        subject = email["subject"]
        body = email["body"]
        influencer_id = email["influencer_id"]

        # Anti-spam delay simulation
        time.sleep(min(settings.DELAY_BETWEEN_EMAILS_SEC, 1))

        if not settings.MOCK_EMAIL_SENDING and settings.GMAIL_USER and settings.GMAIL_APP_PASSWORD:
            # Real Gmail SMTP sending
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{settings.default_campaign.sender_name} <{settings.GMAIL_USER}>"
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
                    server.send_message(msg)

                send_mode = "Live Gmail SMTP"
            except Exception as e:
                logger.error(f"Failed to send email via SMTP: {e}")
                db.update_email_status(email_id, approval_status="Approved", sent_status="Failed")
                return {"success": False, "error": str(e)}
        else:
            send_mode = "Simulated Outreach Sandbox (Anti-Spam Throttled)"

        # Mark email sent and update influencer lifecycle status
        db.update_email_status(email_id, approval_status="Approved", sent_status="Sent")
        db.mark_email_sent(influencer_id, email_type=email["email_type"])

        return {
            "success": True,
            "email_id": email_id,
            "influencer_id": influencer_id,
            "recipient": recipient,
            "send_mode": send_mode,
            "status": "Email Sent",
            "message": f"Outreach email successfully dispatched to {recipient} ({send_mode})."
        }

    def batch_generate_and_queue(self, min_score: int = 60) -> List[Dict[str, Any]]:
        """Generates outreach drafts for all vetted influencers with available emails."""
        influencers = db.get_all_influencers(status="Email Available")
        queued = []
        for inf in influencers:
            if inf.get("suitability_score", 0) >= min_score and inf.get("email"):
                draft = self.generate_personalized_email(inf["id"])
                queued.append(draft)
        return queued


email_engine = ColdEmailEngine()
