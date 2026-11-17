from typing import Dict, Any, List
from app.database.supabase_client import db

class ResearchAgent:
    """
    Research Agent: Performs cited retrieval over statutory provisions
    and procedural limitation rules from the Indian Legal Corpus.
    """

    @classmethod
    def research(cls, category: str, query: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        # Perform retrieval
        sections = db.search_legal_corpus(f"{category} {query}", limit=3)
        
        remedies = []
        for s in sections:
            remedy = {
                "act_name": s["act_name"],
                "section": s["section_number"],
                "title": s["section_title"],
                "summary": s["plain_summary"],
                "limitation": s.get("limitation_period", "As per standard civil limitation rules"),
                "penalties_or_relief": s.get("penalties", "Civil remedy / compensation"),
                "status": s.get("bailable_status", "N/A"),
                "statutory_cite": f"Section {s['section_number']}, {s['act_name']}"
            }
            remedies.append(remedy)
            
        return {
            "category": category,
            "citations_found": len(remedies),
            "remedies": remedies,
            "suggested_action": cls._derive_recommended_action(category, remedies)
        }

    @classmethod
    def _derive_recommended_action(cls, category: str, remedies: List[Dict[str, Any]]) -> str:
        if category == "cheque_bounce":
            return "Send formal Statutory Legal Demand Notice within 30 days of receiving the Bank Return Memo giving 15 days to pay before initiating Section 138 criminal complaint."
        elif category == "consumer_dispute":
            return "Serve a formal pre-litigation Legal Notice giving 15 days to replace product/refund. If unaddressed, file a consumer complaint on the e-Daakhil portal or District Consumer Commission."
        elif category == "property_rera":
            return "Issue formal demand notice under Section 18 of RERA Act, 2016 for refund with interest or delayed possession compensation before approaching the State RERA Authority."
        elif category == "cyber_fraud":
            return "Immediately call National Cyber Crime Helpline 1930 within the 'golden hour' to freeze transaction, followed by filing an acknowledgment on cybercrime.gov.in."
        elif category == "rti_public":
            return "Draft and file an RTI application under Section 6(1) of RTI Act 2005 with Rs. 10 court fee / postal order addressed to the Public Information Officer (PIO)."
        return "Serve a formal Legal Notice through a registered advocate to create documented cause of action."
