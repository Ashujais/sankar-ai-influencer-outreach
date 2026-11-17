"""
Configuration module for AI-Powered Instagram Influencer Research & Outreach Automation.
Handles environment variables, API keys, thresholds, and brand presets.
"""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class CampaignConfig(BaseModel):
    brand_name: str = "AuraWellness Organics"
    brand_niche: str = "Health & Wellness"
    product_name: str = "Morning Radiance Adaptogenic Elixir"
    product_description: str = "All-natural daily adaptogenic superfood blend with lion's mane, chaga, and organic matcha for sustained focus and glowing vitality."
    target_audience: str = "Mindful wellness seekers, organic lifestyle advocates, fitness and clean living enthusiasts aged 22-40."
    collaboration_type: str = "Gifted Product + $250 Sponsored Reel + 15% Affiliate Commission"
    call_to_action: str = "Can we send you a complimentary 30-day VIP kit to try, zero strings attached?"
    sender_name: str = "Sankar Outreach Team"
    sender_title: str = "Influencer Partnerships Lead"
    sender_email: str = os.getenv("SENDER_EMAIL", "partnerships@aurawellness.co")
    company_address: str = "AuraWellness Organics Inc., 100 Innovation Way, Suite 400, San Francisco, CA 94105"
    opt_out_text: str = "P.S. If you'd prefer not to receive collaboration opportunities from us, reply 'UNSUBSCRIBE' and we will immediately remove you from our roster."


class AppSettings:
    # Storage
    DB_PATH: Path = BASE_DIR / "influencer_crm.db"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    SAMPLES_DIR: Path = BASE_DIR / "samples"
    
    # Claude AI Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    AI_FALLBACK_SIMULATION: bool = True  # Allows full functionality without an active API key

    # Gmail SMTP Settings
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    MOCK_EMAIL_SENDING: bool = os.getenv("MOCK_EMAIL_SENDING", "True").lower() == "true"

    # Anti-Spam & Rate Limiting
    MAX_DAILY_EMAILS: int = int(os.getenv("MAX_DAILY_EMAILS", "50"))
    DELAY_BETWEEN_EMAILS_SEC: int = int(os.getenv("DELAY_BETWEEN_EMAILS_SEC", "5"))
    HUMAN_APPROVAL_REQUIRED: bool = True

    # Follow-Up Intervals (Days)
    FOLLOWUP_1_DAYS: int = int(os.getenv("FOLLOWUP_1_DAYS", "3"))
    FOLLOWUP_2_DAYS: int = int(os.getenv("FOLLOWUP_2_DAYS", "5"))
    MAX_FOLLOWUPS: int = 2

    # Google Sheets Sync
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")

    # Active Campaign Defaults
    default_campaign: CampaignConfig = CampaignConfig()


settings = AppSettings()
