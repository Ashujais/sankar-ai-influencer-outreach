"""
Database & CRM layer for Influencer Outreach Automation.
Handles SQLite storage, status lifecycles, and duplicate record prevention.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import settings


VALID_STATUSES = [
    "New Lead",
    "Email Available",
    "Email Sent",
    "Follow-up Due",
    "Replied",
    "Interested",
    "Not Interested",
    "Collaboration Confirmed",
]


class Database:
    def __init__(self, db_path: Path = settings.DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables with proper schemas and constraints."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Influencers CRM table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS influencers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                profile_link TEXT,
                niche TEXT,
                follower_count INTEGER DEFAULT 0,
                email TEXT,
                location TEXT,
                bio TEXT,
                engagement_rate REAL DEFAULT 0.0,
                recent_posts TEXT,
                suitability_score INTEGER DEFAULT 0,
                relevance_category TEXT,
                profile_summary TEXT,
                personalization_hooks TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'New Lead',
                followup_count INTEGER DEFAULT 0,
                sent_at TIMESTAMP,
                last_followup_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Outreach emails table (Initial, Follow-ups, and Approvals)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER,
                influencer_username TEXT,
                recipient_email TEXT,
                email_type TEXT NOT NULL,  -- initial, followup_1, followup_2, reply
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                approval_status TEXT DEFAULT 'Pending Approval', -- Pending Approval, Approved, Rejected
                sent_status TEXT DEFAULT 'Draft',               -- Draft, Queued, Sent, Failed
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id) ON DELETE CASCADE
            )
            """)

            # Incoming replies and AI classification
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER,
                sender_email TEXT NOT NULL,
                subject TEXT,
                body TEXT NOT NULL,
                classification TEXT,     -- Interested, Not Interested, Pricing Enquiries, Collaboration Requests
                confidence REAL DEFAULT 0.0,
                sentiment TEXT,
                reply_draft TEXT,
                next_action TEXT,
                approval_status TEXT DEFAULT 'Pending Approval', -- Pending Approval, Approved, Sent
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id) ON DELETE CASCADE
            )
            """)

            # Campaign settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT,
                brand_niche TEXT,
                product_name TEXT,
                product_description TEXT,
                target_audience TEXT,
                collaboration_type TEXT,
                call_to_action TEXT,
                sender_name TEXT,
                sender_title TEXT,
                sender_email TEXT,
                company_address TEXT,
                opt_out_text TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            conn.commit()

    # --- Influencer CRM Methods ---

    def add_or_update_influencer(self, data: Dict[str, Any]) -> tuple[int, bool]:
        """
        Adds influencer avoiding duplicate records.
        Returns: (influencer_id, was_created_boolean)
        """
        username = data.get("username", "").strip().lstrip("@").lower()
        if not username:
            raise ValueError("Influencer username is required.")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, status, email FROM influencers WHERE LOWER(username) = ?", (username,))
            existing = cursor.fetchone()

            email = data.get("email", "").strip()
            # Determine initial status
            initial_status = data.get("status")
            if not initial_status:
                initial_status = "Email Available" if email else "New Lead"

            if existing:
                # Update existing record without overriding progress
                record_id = existing["id"]
                current_status = existing["status"]
                
                # If we now have an email and status was 'New Lead', bump to 'Email Available'
                new_status = current_status
                if current_status == "New Lead" and email:
                    new_status = "Email Available"

                cursor.execute("""
                    UPDATE influencers SET
                        name = COALESCE(?, name),
                        profile_link = COALESCE(?, profile_link),
                        niche = COALESCE(?, niche),
                        follower_count = COALESCE(?, follower_count),
                        email = CASE WHEN ? != '' THEN ? ELSE email END,
                        location = COALESCE(?, location),
                        bio = COALESCE(?, bio),
                        engagement_rate = COALESCE(?, engagement_rate),
                        recent_posts = COALESCE(?, recent_posts),
                        status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get("name"),
                    data.get("profile_link", f"https://www.instagram.com/{username}/"),
                    data.get("niche"),
                    data.get("follower_count"),
                    email, email,
                    data.get("location"),
                    data.get("bio"),
                    data.get("engagement_rate"),
                    json.dumps(data.get("recent_posts", [])) if isinstance(data.get("recent_posts"), list) else data.get("recent_posts"),
                    new_status,
                    record_id
                ))
                conn.commit()
                return record_id, False
            else:
                cursor.execute("""
                    INSERT INTO influencers (
                        name, username, profile_link, niche, follower_count,
                        email, location, bio, engagement_rate, recent_posts,
                        suitability_score, relevance_category, profile_summary,
                        personalization_hooks, priority, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get("name", username),
                    username,
                    data.get("profile_link", f"https://www.instagram.com/{username}/"),
                    data.get("niche", "General"),
                    data.get("follower_count", 0),
                    email,
                    data.get("location", "Not specified"),
                    data.get("bio", ""),
                    data.get("engagement_rate", 0.0),
                    json.dumps(data.get("recent_posts", [])) if isinstance(data.get("recent_posts"), list) else data.get("recent_posts", "[]"),
                    data.get("suitability_score", 0),
                    data.get("relevance_category", ""),
                    data.get("profile_summary", ""),
                    data.get("personalization_hooks", ""),
                    data.get("priority", "Medium"),
                    initial_status,
                    data.get("notes", "")
                ))
                record_id = cursor.lastrowid
                conn.commit()
                return record_id, True

    def _parse_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if "recent_posts" in d and isinstance(d["recent_posts"], str):
            try:
                d["recent_posts"] = json.loads(d["recent_posts"])
            except Exception:
                pass
        return d

    def get_influencer(self, influencer_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,))
            row = cursor.fetchone()
            return self._parse_row(row) if row else None

    def get_influencer_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        username = username.strip().lstrip("@").lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE LOWER(username) = ?", (username,))
            row = cursor.fetchone()
            return self._parse_row(row) if row else None

    def get_all_influencers(self, status: Optional[str] = None, niche: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM influencers WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if niche:
                query += " AND niche LIKE ?"
                params.append(f"%{niche}%")
            query += " ORDER BY suitability_score DESC, follower_count DESC"
            cursor.execute(query, params)
            return [self._parse_row(row) for row in cursor.fetchall()]

    def update_influencer_status(self, influencer_id: int, new_status: str, notes: Optional[str] = None) -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if notes:
                cursor.execute("""
                    UPDATE influencers 
                    SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_status, notes, influencer_id))
            else:
                cursor.execute("""
                    UPDATE influencers 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_status, influencer_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_ai_evaluation(self, influencer_id: int, eval_data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE influencers SET
                    suitability_score = ?,
                    relevance_category = ?,
                    profile_summary = ?,
                    personalization_hooks = ?,
                    priority = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                eval_data.get("suitability_score", 0),
                eval_data.get("relevance_category", ""),
                eval_data.get("profile_summary", ""),
                eval_data.get("personalization_hooks", ""),
                eval_data.get("priority", "Medium"),
                influencer_id
            ))
            conn.commit()

    def mark_email_sent(self, influencer_id: int, email_type: str = "initial"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if email_type == "initial":
                cursor.execute("""
                    UPDATE influencers SET
                        status = 'Email Sent',
                        sent_at = CURRENT_TIMESTAMP,
                        followup_count = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (influencer_id,))
            else:
                cursor.execute("""
                    UPDATE influencers SET
                        last_followup_at = CURRENT_TIMESTAMP,
                        followup_count = followup_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (influencer_id,))
            conn.commit()

    # --- Email Record Methods ---

    def create_email(self, influencer_id: int, recipient_email: str, email_type: str, 
                     subject: str, body: str, approval_status: str = "Pending Approval") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM influencers WHERE id = ?", (influencer_id,))
            row = cursor.fetchone()
            username = row["username"] if row else ""

            cursor.execute("""
                INSERT INTO emails (
                    influencer_id, influencer_username, recipient_email, email_type, 
                    subject, body, approval_status, sent_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Draft')
            """, (influencer_id, username, recipient_email, email_type, subject, body, approval_status))
            email_id = cursor.lastrowid
            conn.commit()
            return email_id

    def get_email(self, email_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_emails_by_influencer(self, influencer_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE influencer_id = ? ORDER BY id ASC", (influencer_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_emails(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, i.name as influencer_name, i.niche, i.follower_count, i.suitability_score
                FROM emails e
                JOIN influencers i ON e.influencer_id = i.id
                WHERE e.approval_status = 'Pending Approval' AND e.sent_status != 'Sent'
                ORDER BY e.id DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_email_content(self, email_id: int, subject: str, body: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE emails SET subject = ?, body = ? WHERE id = ?", (subject, body, email_id))
            conn.commit()

    def update_email_status(self, email_id: int, approval_status: str, sent_status: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if sent_status:
                cursor.execute("""
                    UPDATE emails SET 
                        approval_status = ?, sent_status = ?, 
                        sent_at = CASE WHEN ? = 'Sent' THEN CURRENT_TIMESTAMP ELSE sent_at END
                    WHERE id = ?
                """, (approval_status, sent_status, sent_status, email_id))
            else:
                cursor.execute("UPDATE emails SET approval_status = ? WHERE id = ?", (approval_status, email_id))
            conn.commit()

    # --- Incoming Replies Methods ---

    def create_reply(self, influencer_id: int, sender_email: str, subject: str, body: str,
                     classification: str, confidence: float, sentiment: str, 
                     reply_draft: str, next_action: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO replies (
                    influencer_id, sender_email, subject, body,
                    classification, confidence, sentiment, reply_draft,
                    next_action, approval_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending Approval')
            """, (influencer_id, sender_email, subject, body, classification, confidence, sentiment, reply_draft, next_action))
            reply_id = cursor.lastrowid
            conn.commit()
            return reply_id

    def get_pending_replies(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, i.name as influencer_name, i.username, i.niche, i.status as influencer_status
                FROM replies r
                JOIN influencers i ON r.influencer_id = i.id
                ORDER BY r.id DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_reply_approval(self, reply_id: int, approval_status: str, updated_draft: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if updated_draft:
                cursor.execute("""
                    UPDATE replies SET approval_status = ?, reply_draft = ? WHERE id = ?
                """, (approval_status, updated_draft, reply_id))
            else:
                cursor.execute("UPDATE replies SET approval_status = ? WHERE id = ?", (approval_status, reply_id))
            conn.commit()

    # --- Metrics & Dashboard Stats ---

    def get_dashboard_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM influencers")
            total_leads = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM influencers WHERE email IS NOT NULL AND email != ''")
            emails_available = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM emails WHERE sent_status = 'Sent'")
            emails_sent = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM replies")
            total_replies = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM influencers WHERE status = 'Interested'")
            interested_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM influencers WHERE status = 'Collaboration Confirmed'")
            confirmed_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM emails WHERE approval_status = 'Pending Approval'")
            pending_email_approvals = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM replies WHERE approval_status = 'Pending Approval'")
            pending_reply_approvals = cursor.fetchone()[0]

            # Status breakdown
            cursor.execute("SELECT status, COUNT(*) as count FROM influencers GROUP BY status")
            status_breakdown = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Ensure all valid statuses appear in breakdown
            for s in VALID_STATUSES:
                if s not in status_breakdown:
                    status_breakdown[s] = 0

            return {
                "total_leads": total_leads,
                "emails_available": emails_available,
                "emails_sent": emails_sent,
                "total_replies": total_replies,
                "interested_count": interested_count,
                "confirmed_count": confirmed_count,
                "pending_email_approvals": pending_email_approvals,
                "pending_reply_approvals": pending_reply_approvals,
                "status_breakdown": status_breakdown
            }


db = Database()
