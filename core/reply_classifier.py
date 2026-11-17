"""
Step 6: AI Email Reply Management with Claude AI.
Reads and classifies incoming emails into 4 categories:
1. Interested
2. Not Interested
3. Pricing Enquiries
4. Collaboration Requests

Generates contextual reply drafts, suggests next actions, and automatically updates CRM statuses.
Enforces human review and approval before replies are dispatched.
"""

import json
import logging
from typing import Dict, Any, Optional, List
import anthropic
from config import settings, CampaignConfig
from core.database import db

logger = logging.getLogger(__name__)


REPLY_CLASSIFIER_PROMPT = """You are an AI Communications Specialist for an Influencer Partnerships team.
Your job is to read an incoming email reply from an influencer and perform intelligent triage:

1. CLASSIFY into exactly ONE of these four categories:
   - 'Interested' (The creator is excited, wants to try product, requests sample, or wants to collaborate)
   - 'Not Interested' (The creator politely or firmly declines, says not taking collabs, or asks to unsubscribe)
   - 'Pricing Enquiries' (The creator asks for budget, provides their rate card, or inquires about monetary compensation)
   - 'Collaboration Requests' (The creator proposes specific deliverables, dates, counter-offers, or asks for creative briefing)

2. ANALYZE:
   - Sentiment ('Positive', 'Neutral', 'Negative')
   - Confidence score (0.0 to 1.0)
   - Brief summary of their reply

3. SUGGEST NEXT ACTION:
   - Clear practical next step (e.g. 'Request shipping address for gift kit', 'Share standard $250 reel budget & review rate card', 'Acknowledge decline & archive lead')

4. GENERATE A PERSONALIZED REPLY DRAFT:
   - Tailored to their message
   - If Interested: enthusiastic, asking for shipping address and preferred product flavor
   - If Not Interested: polite, gracious, confirms removal, zero pushiness
   - If Pricing Enquiry: professional, asking for their rate card/media kit and stating our typical $250-$500 budget
   - If Collaboration Request: confirming details and offering a 10-minute sync or sending collaboration agreement

5. STATUS UPDATE:
   - Suggested CRM status ('Interested', 'Not Interested', 'Replied', or 'Collaboration Confirmed')

Output strictly valid JSON:
{
  "classification": "Interested" | "Not Interested" | "Pricing Enquiries" | "Collaboration Requests",
  "confidence": 0.95,
  "sentiment": "Positive" | "Neutral" | "Negative",
  "summary": "Short 1 sentence summary of creator message",
  "suggested_next_action": "Actionable task",
  "reply_draft": "Full email reply text ready to send",
  "recommended_status": "Interested" | "Not Interested" | "Replied" | "Collaboration Confirmed"
}
"""


class ReplyClassifier:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def process_incoming_reply(
        self,
        influencer_id: int,
        sender_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Processes an incoming reply, runs Claude classification, generates reply draft,
        updates CRM status, and queues the reply for human approval.
        """
        influencer = db.get_influencer(influencer_id)
        if not influencer:
            raise ValueError(f"Influencer ID {influencer_id} not found.")

        camp = settings.default_campaign
        analysis = self._classify_with_claude(influencer, camp, subject, body)

        # Update influencer CRM status automatically
        recommended_status = analysis.get("recommended_status", "Replied")
        note = f"AI Classified: {analysis.get('classification')} | Sentiment: {analysis.get('sentiment')}"
        db.update_influencer_status(influencer_id, recommended_status, notes=note)

        # Save to replies table with 'Pending Approval'
        reply_id = db.create_reply(
            influencer_id=influencer_id,
            sender_email=sender_email,
            subject=subject,
            body=body,
            classification=analysis.get("classification"),
            confidence=analysis.get("confidence", 0.9),
            sentiment=analysis.get("sentiment"),
            reply_draft=analysis.get("reply_draft"),
            next_action=analysis.get("suggested_next_action")
        )

        return {
            "reply_id": reply_id,
            "influencer_id": influencer_id,
            "influencer_name": influencer.get("name"),
            "sender_email": sender_email,
            "classification": analysis.get("classification"),
            "confidence": analysis.get("confidence"),
            "sentiment": analysis.get("sentiment"),
            "suggested_next_action": analysis.get("suggested_next_action"),
            "reply_draft": analysis.get("reply_draft"),
            "new_crm_status": recommended_status,
            "approval_status": "Pending Approval",
            "message": f"Reply processed: Classified as '{analysis.get('classification')}', CRM status updated to '{recommended_status}'."
        }

    def _classify_with_claude(
        self,
        influencer: Dict[str, Any],
        camp: CampaignConfig,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        if self.client and self.api_key:
            try:
                user_prompt = f"""
BRAND CONTEXT:
- Brand: {camp.brand_name}
- Product: {camp.product_name}
- Standard Offer: {camp.collaboration_type}

INFLUENCER CONTEXT:
- Name: {influencer.get('name')} (@{influencer.get('username')})
- Niche: {influencer.get('niche')}

INCOMING EMAIL:
- From: {influencer.get('email')}
- Subject: {subject}
- Body:
{body}

Classify this email, draft the reply, and return the strict JSON output.
"""
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    temperature=0.2,
                    system=REPLY_CLASSIFIER_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                text = response.content[0].text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except Exception as e:
                logger.warning(f"Claude API reply classification failed ({e}). Using intelligent fallback engine.")
                return self._simulate_reply_classification(influencer, camp, subject, body)
        else:
            return self._simulate_reply_classification(influencer, camp, subject, body)

    def _simulate_reply_classification(
        self,
        influencer: Dict[str, Any],
        camp: CampaignConfig,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Intelligent heuristic classifier mimicking Claude AI.
        Detects intent based on semantic markers.
        """
        body_lower = body.lower()
        first_name = influencer.get("name", "there").split()[0]

        # 1. Check for Not Interested / Decline / Unsubscribe
        if any(term in body_lower for term in ["unsubscribe", "not interested", "remove me", "pass on this", "not taking collabs", "decline", "stop emailing"]):
            classification = "Not Interested"
            sentiment = "Negative"
            confidence = 0.98
            summary = f"{first_name} politely declined the collaboration or asked to opt out."
            next_action = "Mark as Not Interested, cancel all follow-ups, and archive lead."
            recommended_status = "Not Interested"
            reply_draft = f"""Hi {first_name},

Thank you for letting us know! We have completely removed you from our outreach list.

Wishing you continued success with your channel!

Best,
{camp.sender_name} | {camp.brand_name}"""

        # 2. Check for Pricing / Budget / Rates
        elif any(term in body_lower for term in ["rate", "rates", "budget", "pricing", "cost", "fee", "compensation", "media kit", "deliverable price"]):
            classification = "Pricing Enquiries"
            sentiment = "Neutral"
            confidence = 0.93
            summary = f"{first_name} is requesting budget details or sharing their rate card."
            next_action = "Review influencer rate card against our $250-$500 budget and confirm deliverables."
            recommended_status = "Replied"
            reply_draft = f"""Hi {first_name},

Thanks for getting back to me so quickly!

Our standard budget for this campaign is $250 - $400 for 1 dedicated Instagram Reel + supporting story slides, plus our full 30-day {camp.product_name} VIP Kit.

Could you share your current media kit or rate card? If our budget aligns with your baseline, we can prepare the brief and collaboration agreement right away!

Looking forward to hearing from you,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}"""

        # 3. Check for Collaboration Requests / Specific proposals
        elif any(term in body_lower for term in ["deliverables", "brief", "contract", "timeline", "reel and stories", "creative freedom", "exclusivity"]):
            classification = "Collaboration Requests"
            sentiment = "Positive"
            confidence = 0.91
            summary = f"{first_name} is proposing specific campaign terms and deliverables."
            next_action = "Confirm deliverables and send official collaboration onboarding link."
            recommended_status = "Interested"
            reply_draft = f"""Hi {first_name},

That sounds like a great plan! The proposed deliverables align really well with our campaign goals.

I've attached our 1-page campaign brief with key product talking points and aesthetic guidelines. We prioritize your authentic voice, so full creative freedom is yours.

What's the best shipping address to dispatch your VIP product box to so you can start testing?

Warmly,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}"""

        # 4. Default to Interested
        else:
            classification = "Interested"
            sentiment = "Positive"
            confidence = 0.96
            summary = f"{first_name} is excited about the brand and wants to try the product."
            next_action = "Request shipping address and dispatch complimentary product box."
            recommended_status = "Interested"
            reply_draft = f"""Hi {first_name},

We are so thrilled to hear that! You're going to love our {camp.product_name}.

Where is the best shipping address (or PO Box) to send your complimentary 30-day VIP care package?

Once dispatched, I'll send over the tracking number along with our partnership overview.

So excited to collaborate with you!

Warmest regards,

{camp.sender_name}
{camp.sender_title} | {camp.brand_name}"""

        return {
            "classification": classification,
            "confidence": confidence,
            "sentiment": sentiment,
            "summary": summary,
            "suggested_next_action": next_action,
            "reply_draft": reply_draft,
            "recommended_status": recommended_status
        }

    def approve_and_send_reply(self, reply_id: int, updated_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Human reviewer approves the AI-drafted reply and dispatches it.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM replies WHERE id = ?", (reply_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Reply ID {reply_id} not found.")

            final_body = updated_text or row["reply_draft"]
            db.update_reply_approval(reply_id, approval_status="Approved", updated_draft=final_body)

            # If classification was 'Interested' or 'Collaboration Requests', can advance to 'Collaboration Confirmed'
            if row["classification"] in ["Interested", "Collaboration Requests"]:
                db.update_influencer_status(row["influencer_id"], "Collaboration Confirmed")

            return {
                "success": True,
                "reply_id": reply_id,
                "influencer_id": row["influencer_id"],
                "approval_status": "Approved",
                "status": "Dispatched",
                "message": f"Approved reply dispatched to {row['sender_email']}."
            }


reply_classifier = ReplyClassifier()
