import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from app.safety.pii_redactor import PIIRedactor
from app.safety.urgency_triage import UrgencyTriage
from app.agents.intake_agent import IntakeAgent
from app.agents.research_agent import ResearchAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.verifier_agent import VerifierAgent
from app.agents.handoff_agent import HandoffAgent
from app.agents.conversational_agent import ConversationalAgent

class OrchestratorAgent:
    """
    Central Orchestrator Agent:
    Coordinates multi-agent workflows, keeps persistent case session state,
    enforces DPDP privacy masking, runs hallucination verification, and triggers advocate handoff.
    """

    # In-memory session store (case_id -> state dict)
    ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _amount_value(text: Optional[str]) -> float:
        """Rough rupee value of an extracted amount, used only for comparison."""
        if not text:
            return 0.0
        t = text.lower().replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)", t)
        if not match:
            return 0.0
        value = float(match.group(1))
        if "crore" in t:
            value *= 10_000_000
        elif "lakh" in t:
            value *= 100_000
        elif re.search(r"\d\s*k\b", t):
            value *= 1_000
        return value

    @classmethod
    def process_consultation(
        cls, 
        user_message: str, 
        session_id: str = "", 
        history: Optional[List[Dict[str, Any]]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        case_id = session_id or f"OV-{uuid.uuid4().hex[:8].upper()}"

        # Step 1: Safety & DPDP Layer - Redact PII
        redacted_message, redactions = PIIRedactor.redact(user_message)
        
        # Step 2: Urgency Triage (Emergency escalation rules)
        triage_result = UrgencyTriage.evaluate(redacted_message)
        
        # Step 3: Intake Agent - Classify and extract facts
        intake_result = IntakeAgent.analyze(redacted_message, history=history)
        new_category = intake_result["category"]
        new_facts = intake_result["facts"]

        # Context Inheritance for Follow-Up Questions:
        existing_session = cls.ACTIVE_SESSIONS.get(case_id)
        if existing_session:
            # Preserve existing specific case category if follow-up is an elaboration or general
            if new_category == "general_civil" and existing_session.get("category"):
                category = existing_session.get("category")
            else:
                category = new_category
            
            old_facts = existing_session.get("facts", {})
            facts = {
                # A later message often mentions an incidental sum — the ₹100
                # stamp paper, a court fee — which used to overwrite the amount
                # in dispute and leave the notice demanding ₹100. Keep whichever
                # figure is larger so the principal survives the conversation.
                "monetary_amount": (
                    new_facts.get("monetary_amount")
                    if cls._amount_value(new_facts.get("monetary_amount"))
                    > cls._amount_value(old_facts.get("monetary_amount"))
                    else (old_facts.get("monetary_amount") or new_facts.get("monetary_amount"))
                ),
                "dates_mentioned": list(set(old_facts.get("dates_mentioned", []) + new_facts.get("dates_mentioned", []))),
                "locations_mentioned": new_facts.get("locations_mentioned") if new_facts.get("locations_mentioned") else old_facts.get("locations_mentioned", []),
                "localities_mentioned": new_facts.get("localities_mentioned") if new_facts.get("localities_mentioned") else old_facts.get("localities_mentioned", []),
                "district_courts_mentioned": new_facts.get("district_courts_mentioned") if new_facts.get("district_courts_mentioned") else old_facts.get("district_courts_mentioned", []),
                "identified_parties": list(set(old_facts.get("identified_parties", []) + new_facts.get("identified_parties", []))),
                "detected_district": new_facts.get("detected_district") or old_facts.get("detected_district"),
                "detected_state": new_facts.get("detected_state") or old_facts.get("detected_state"),
                "detected_court": new_facts.get("detected_court") or old_facts.get("detected_court"),
            }
        else:
            category = new_category
            facts = new_facts

        newly_detected_location = bool(
            new_facts.get("locations_mentioned") or 
            new_facts.get("localities_mentioned") or 
            new_facts.get("district_courts_mentioned")
        )

        # Step 4: Research Agent - Retrieve cited statutory remedies
        city = (facts.get("locations_mentioned") or [""])[0]
        locality = (facts.get("localities_mentioned") or [""])[0]
        district_court = facts.get("detected_court") or (facts.get("district_courts_mentioned") or [""])[0]
        research_result = ResearchAgent.research(category, redacted_message, facts)
        remedies = research_result["remedies"]

        # Step 5: Verifier Agent - Verify every citation
        verifier_result = VerifierAgent.verify_citations(remedies)

        # Steps 6 and 8 each make their own model call and neither reads the
        # other's result, so they run together rather than one after the other.
        # Step 7 is pure in-memory ranking and runs here while they are in flight.
        with ThreadPoolExecutor(max_workers=2) as pool:
            draft_future = pool.submit(
                DraftingAgent.draft_document,
                category=category,
                facts=facts,
                user_message=redacted_message,
                history=history,
                remedies=remedies
            )
            guidance_future = pool.submit(
                ConversationalAgent.generate_human_response,
                user_query=redacted_message,
                category=category,
                facts=facts,
                remedies=remedies,
                triage=triage_result,
                language=language,
                history=history
            )

            # Step 7: Handoff Agent - Advocate brief & matched verified lawyers
            brief_result = HandoffAgent.prepare_case_brief(
                case_id=case_id,
                category=category,
                facts=facts,
                remedies=remedies,
                urgency=triage_result["urgency"]
            )
            matched_advocates = HandoffAgent.match_advocates(
                category=category,
                city=city,
                locality=locality,
                district_court=district_court
            )
            exact_location_matches = [a for a in matched_advocates if a.get("is_location_match")]
            location_matched_count = len(exact_location_matches) if exact_location_matches else (1 if (city or district_court) else len(matched_advocates))

            # Step 6 result: the synchronized legal notice draft
            draft_result = draft_future.result()
            # Step 8 result: the plain-language reply
            guidance_text = guidance_future.result()

        # Save / Update session state
        cls.ACTIVE_SESSIONS[case_id] = {
            "case_id": case_id,
            "category": category,
            "facts": facts,
            "remedies": remedies,
            "updated_at": uuid.uuid4().hex
        }

        return {
            "case_id": case_id,
            "category": category,
            "category_label": category.replace('_', ' ').title(),
            "pii_redacted": redactions,
            "urgency": triage_result,
            "facts_extracted": facts,
            "missing_fields": intake_result["missing_fields"],
            "guidance": guidance_text,
            "statutory_remedies": remedies,
            "verification": verifier_result,
            "draft_document": draft_result,
            "advocate_brief": brief_result,
            "matched_advocates": matched_advocates,
            "location_matched_count": location_matched_count,
            "newly_detected_location": newly_detected_location,
            "detected_district": facts.get("detected_district"),
            "detected_state": facts.get("detected_state"),
            "detected_court": facts.get("detected_court"),
            "detected_city": (facts.get("locations_mentioned") or [""])[0],
        }

    @classmethod
    def _generate_citizen_guidance(
        cls, 
        category: str, 
        facts: Dict[str, Any], 
        remedies: List[Dict[str, Any]], 
        triage: Dict[str, Any],
        verifier: Dict[str, Any]
    ) -> str:
        lines = []
        if triage["urgency"] == "emergency":
            lines.append("⚠️ **EMERGENCY ESCALATION**: Immediate safety or criminal concern detected.")
            lines.append("Please contact the National Legal Helpline (NALSA) at **15100** or Emergency Police at **112** immediately.\n")

        lines.append(f"### Initial Legal Assessment ({category.replace('_', ' ').title()})\n")
        
        if facts.get("monetary_amount"):
            lines.append(f"- **Disputed Amount**: {facts['monetary_amount']}")
        if facts.get("dates_mentioned"):
            lines.append(f"- **Recorded Date(s)**: {', '.join(facts['dates_mentioned'])}")
        if facts.get("locations_mentioned"):
            lines.append(f"- **Jurisdiction**: {', '.join(facts['locations_mentioned'])}")
            
        lines.append("\n#### Verified Statutory Remedies Available:")
        for r in remedies:
            lines.append(f"- **{r['statutory_cite']}**: {r['summary']}")
            lines.append(f"  *Limitation Period*: {r['limitation']}")
            if r.get("penalties_or_relief"):
                lines.append(f"  *Relief / Consequence*: {r['penalties_or_relief']}")

        lines.append(f"\n✅ *{verifier['verification_badge']}*")
        lines.append("\nWe have prepared an initial statutory legal notice draft below. You can review it, export it, or connect with a verified advocate in your jurisdiction for filing.")
        return "\n".join(lines)
