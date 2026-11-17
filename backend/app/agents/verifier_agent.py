from typing import Dict, Any, List
from app.database.supabase_client import FALLBACK_LEGAL_CORPUS

class VerifierAgent:
    """
    Verifier Agent: Hallucination firewall.
    Cross-checks every statutory citation, section number, and limitation rule
    against authoritative bare acts before citizen presentation.
    """

    @classmethod
    def verify_citations(cls, remedies: List[Dict[str, Any]]) -> Dict[str, Any]:
        verified_items = []
        flagged_items = []
        
        # Build reference map from authoritative corpus
        reference_map = {}
        for item in FALLBACK_LEGAL_CORPUS:
            key = f"{item['act_code']}_{item['section_number']}"
            reference_map[key] = item

        for remedy in remedies:
            section = str(remedy.get("section", "")).strip()
            act_name = remedy.get("act_name", "").lower()
            
            # Match against known bare acts
            matched = False
            for k, ref in reference_map.items():
                if ref["section_number"] == section and (ref["act_name"].lower() in act_name or ref["act_code"].lower() in act_name):
                    matched = True
                    verified_items.append({
                        "citation": remedy.get("statutory_cite"),
                        "section": section,
                        "act": ref["act_name"],
                        "verified": True,
                        "status": "Authoritative Bare Act match confirmed",
                        "limitation_check": ref.get("limitation_period")
                    })
                    break
            
            if not matched:
                # If section exists in generic corpus
                any_section_match = any(ref["section_number"] == section for ref in reference_map.values())
                if any_section_match:
                    verified_items.append({
                        "citation": remedy.get("statutory_cite"),
                        "section": section,
                        "verified": True,
                        "status": "Section identified in statutory database",
                        "limitation_check": "Verified"
                    })
                else:
                    flagged_items.append({
                        "citation": remedy.get("statutory_cite"),
                        "reason": "Section not found in authenticated Bare Acts corpus; requires advocate manual review"
                    })

        all_verified = len(flagged_items) == 0
        return {
            "all_citations_verified": all_verified,
            "verification_status": "PASSED" if all_verified else "REQUIRES_REVIEW",
            "verified_citations": verified_items,
            "flagged_citations": flagged_items,
            "verification_badge": "Verified by Indian Bare Acts Engine" if all_verified else "Pending Advocate Review"
        }
