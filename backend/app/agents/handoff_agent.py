from typing import Dict, Any, List
from app.database.supabase_client import db

class HandoffAgent:
    """
    Handoff Agent: Prepares DPDP-compliant case briefs for verified advocates
    and matches qualified lawyers by domain specialization and jurisdiction.
    """

    @classmethod
    def prepare_case_brief(
        cls, 
        case_id: str, 
        category: str, 
        facts: Dict[str, Any], 
        remedies: List[Dict[str, Any]], 
        urgency: str
    ) -> Dict[str, Any]:
        amount = facts.get("monetary_amount") or "Undisclosed / Non-monetary"
        dates = ", ".join(facts.get("dates_mentioned", [])) or "Recent"
        city = (facts.get("locations_mentioned") or ["General"])[0]

        brief_text = f"""--- CONFIDENTIAL LEGAL CASE BRIEF (DPDP PROTECTED) ---
Case Reference: {case_id}
Category: {category.upper().replace('_', ' ')}
Urgency Tier: {urgency.upper()}
Jurisdiction: {city}
Disputed Stake / Amount: {amount}
Timeline / Dates: {dates}

Key Statutory Grounds Identified:
{chr(10).join([f"- {r.get('statutory_cite')}: {r.get('summary')}" for r in remedies[:2]])}

Client Identity Status: PII Masked until Advocate Acceptance.
"""
        return {
            "case_id": case_id,
            "brief_text": brief_text,
            "summary_for_advocate": {
                "category": category,
                "amount": amount,
                "city": city,
                "urgency": urgency,
                "dates": dates
            }
        }

    @classmethod
    def match_advocates(
        cls, 
        category: str, 
        city: str = "", 
        locality: str = "", 
        district_court: str = ""
    ) -> List[Dict[str, Any]]:
        advocates = db.get_advocates(
            category=category, 
            city=city, 
            locality=locality, 
            district_court=district_court
        )
        return advocates
