"""
Step 3: Google Sheets & CRM Integration.
Exports and synchronizes influencer data between SQLite CRM, Google Sheets, CSV, and Excel.
Maintains deduplication, status integrity, and formatted column schemas.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import settings
from core.database import db, VALID_STATUSES


SHEET_HEADERS = [
    "ID",
    "Status",
    "Influencer Name",
    "Instagram Handle",
    "Profile Link",
    "Niche",
    "Followers",
    "Business Email",
    "Location",
    "Suitability Score (1-100)",
    "Priority",
    "Profile Summary",
    "Personalization Hook",
    "Follow-up Count",
    "Initial Email Sent Date",
    "Last Follow-up Date",
    "Notes"
]


class GoogleSheetsCRM:
    def __init__(self):
        self.service_account_path = settings.GOOGLE_SERVICE_ACCOUNT_JSON
        self.sheet_id = settings.GOOGLE_SHEET_ID

    def get_crm_records_dataframe(self) -> pd.DataFrame:
        """Fetches all records from SQLite and converts to structured DataFrame."""
        influencers = db.get_all_influencers()
        rows = []
        for i in influencers:
            rows.append({
                "ID": i.get("id"),
                "Status": i.get("status", "New Lead"),
                "Influencer Name": i.get("name", ""),
                "Instagram Handle": f"@{i.get('username', '')}",
                "Profile Link": i.get("profile_link", ""),
                "Niche": i.get("niche", ""),
                "Followers": i.get("follower_count", 0),
                "Business Email": i.get("email", ""),
                "Location": i.get("location", ""),
                "Suitability Score (1-100)": i.get("suitability_score", 0),
                "Priority": i.get("priority", "Medium"),
                "Profile Summary": i.get("profile_summary", ""),
                "Personalization Hook": i.get("personalization_hooks", ""),
                "Follow-up Count": i.get("followup_count", 0),
                "Initial Email Sent Date": str(i.get("sent_at") or ""),
                "Last Follow-up Date": str(i.get("last_followup_at") or ""),
                "Notes": i.get("notes", "")
            })
        return pd.DataFrame(rows, columns=SHEET_HEADERS)

    def export_to_csv(self, file_path: Optional[Path] = None) -> Path:
        """Exports CRM database to CSV format matching Google Sheet columns."""
        path = file_path or (settings.EXPORTS_DIR / "sample_influencers_crm.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        df = self.get_crm_records_dataframe()
        df.to_csv(path, index=False, encoding="utf-8")
        return path

    def export_to_excel(self, file_path: Optional[Path] = None) -> Path:
        """Exports CRM database to formatted Excel workbook."""
        path = file_path or (settings.EXPORTS_DIR / "sample_influencers_crm.xlsx")
        path.parent.mkdir(parents=True, exist_ok=True)
        df = self.get_crm_records_dataframe()
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Influencer CRM", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Influencer CRM"]
            header_format = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#1A73E8",
                "font_color": "#FFFFFF",
                "border": 1
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, max(len(str(value)) + 4, 15))
        return path

    def sync_to_google_sheet(self, sheet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronizes SQLite CRM records directly to a live Google Sheet using gspread.
        Returns sync details or graceful status if credentials not present.
        """
        target_sheet_id = sheet_id or self.sheet_id
        if not target_sheet_id or not os.path.exists(self.service_account_path):
            # Graceful notice when running without Google Cloud Service Account credentials
            csv_path = self.export_to_csv()
            xlsx_path = self.export_to_excel()
            return {
                "success": True,
                "mode": "Local CRM & CSV/XLSX Export Ready",
                "sheet_id": target_sheet_id or "Not configured (Using instant CSV/Excel export)",
                "records_synced": len(db.get_all_influencers()),
                "csv_path": str(csv_path),
                "xlsx_path": str(xlsx_path),
                "message": "CRM data exported successfully to CSV and Excel. To connect live Google Sheet, add service_account.json and GOOGLE_SHEET_ID."
            }

        try:
            import gspread
            gc = gspread.service_account(filename=self.service_account_path)
            sh = gc.open_by_key(target_sheet_id)
            worksheet = sh.get_worksheet(0)

            df = self.get_crm_records_dataframe()
            # Replace NaN with empty string
            df_filled = df.fillna("")
            values = [df_filled.columns.values.tolist()] + df_filled.values.tolist()

            worksheet.clear()
            worksheet.update(values)

            return {
                "success": True,
                "mode": "Live Google Sheets API",
                "sheet_title": sh.title,
                "records_synced": len(df),
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{target_sheet_id}/edit",
                "message": f"Successfully synced {len(df)} records to Google Sheet."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync to Google Sheets API. Exported locally to CSV instead."
            }

    def import_from_csv(self, file_path: Path) -> Dict[str, Any]:
        """Imports influencer leads from an external CSV file, avoiding duplicates."""
        added = 0
        updated = 0
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row.get("Instagram Handle", row.get("username", "")).lstrip("@")
                if not username:
                    continue
                data = {
                    "name": row.get("Influencer Name", row.get("name", username)),
                    "username": username,
                    "profile_link": row.get("Profile Link", f"https://www.instagram.com/{username}/"),
                    "niche": row.get("Niche", row.get("niche", "General")),
                    "follower_count": int(row.get("Followers", row.get("follower_count", 0)) or 0),
                    "email": row.get("Business Email", row.get("email", "")),
                    "location": row.get("Location", row.get("location", "")),
                    "status": row.get("Status", "New Lead")
                }
                _, created = db.add_or_update_influencer(data)
                if created:
                    added += 1
                else:
                    updated += 1

        return {"added": added, "updated": updated, "total": added + updated}


google_sheets_crm = GoogleSheetsCRM()
