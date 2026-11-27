import re
import time
import uuid
from datetime import datetime, timezone
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
    # Demo-only in-memory ring buffer of real query execution traces
    TRACE_LOG: List[Dict[str, Any]] = []
    MAX_TRACES: int = 100

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
        trace_id = f"tr-{uuid.uuid4().hex[:10]}"
        pipeline_start = time.perf_counter()
        spans: List[Dict[str, Any]] = []

        def _ms(t0: float) -> float:
            return round((time.perf_counter() - t0) * 1000.0, 2)

        # Step 1: Safety & DPDP Layer - Redact PII
        t_step = time.perf_counter()
        redacted_message, redactions = PIIRedactor.redact(user_message)
        spans.append({
            "step": "1. PII Redactor (DPDP)",
            "agent": "PIIRedactor",
            "model_or_tool": "Regex + NER Guardrail",
            "start_ms": 0.0,
            "duration_ms": _ms(t_step),
            "status": "ok",
            "detail": f"Masked {len(redactions)} PII item(s): {', '.join(redactions) if redactions else 'none detected'}",
            "payload": {
                "pii_items_masked": redactions,
                "redacted_input_sent_to_agents": redacted_message,
            },
        })
        
        # Step 2: Urgency Triage (Emergency escalation rules)
        t_step = time.perf_counter()
        t0_offset = round((t_step - pipeline_start) * 1000.0, 2)
        triage_result = UrgencyTriage.evaluate(redacted_message)
        spans.append({
            "step": "2. Urgency Triage",
            "agent": "UrgencyTriage",
            "model_or_tool": "Rule-Based Escalation",
            "start_ms": t0_offset,
            "duration_ms": _ms(t_step),
            "status": "ok",
            "detail": f"Urgency: {triage_result.get('urgency', 'routine').upper()}",
            "payload": triage_result,
        })
        
        # Step 3: Intake Agent - Classify and extract facts
        t_step = time.perf_counter()
        t0_offset = round((t_step - pipeline_start) * 1000.0, 2)
        intake_result = IntakeAgent.analyze(redacted_message, history=history)
        new_category = intake_result["category"]
        new_facts = intake_result["facts"]
        spans.append({
            "step": "3. Intake & Fact Extraction",
            "agent": "IntakeAgent",
            "model_or_tool": "Structured Case Classifier",
            "start_ms": t0_offset,
            "duration_ms": _ms(t_step),
            "status": "ok",
            "detail": f"Category: {new_category} | City: {(new_facts.get('locations_mentioned') or ['N/A'])[0]}",
            "payload": {
                "classified_category": new_category,
                "extracted_facts": new_facts,
                "missing_fields": intake_result.get("missing_fields", []),
            },
        })

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
        t_step = time.perf_counter()
        t0_offset = round((t_step - pipeline_start) * 1000.0, 2)
        research_result = ResearchAgent.research(category, redacted_message, facts)
        remedies = research_result["remedies"]
        # Filter out unrelated banking/cyber precedents on general civil / noise nuisance disputes
        q_low = redacted_message.lower()
        if category == "general_civil" and any(n in q_low for n in ("loud music", "noise", "neighbor", "neighbour", "nuisance")):
            remedies = [r for r in remedies if "ramdoot" not in str(r.get("section", "")).lower() and "reserve bank" not in str(r.get("act_name", "")).lower()]
        cited_titles = [r.get("statutory_cite", "Unknown") for r in remedies[:3]]
        spans.append({
            "step": "4. Hybrid RAG Research",
            "agent": "ResearchAgent",
            "model_or_tool": "bge-small-en-v1.5 (vm02-ca.crt) + Hybrid Search",
            "start_ms": t0_offset,
            "duration_ms": _ms(t_step),
            "status": "ok",
            "detail": f"Retrieved {len(remedies)} statute(s): {'; '.join(cited_titles) if cited_titles else 'none'}",
            "payload": {
                "retrieved_remedies": [
                    {
                        "statutory_cite": r.get("statutory_cite"),
                        "summary": r.get("summary"),
                        "limitation": r.get("limitation"),
                        "penalties_or_relief": r.get("penalties_or_relief"),
                    }
                    for r in remedies
                ]
            },
        })

        # Step 5: Verifier Agent - Verify every citation & block unverified query statutes
        t_step = time.perf_counter()
        t0_offset = round((t_step - pipeline_start) * 1000.0, 2)
        verifier_result = VerifierAgent.verify_citations(remedies, user_query=redacted_message)
        spans.append({
            "step": "5. Citation Verifier",
            "agent": "VerifierAgent",
            "model_or_tool": "Groundedness & Anti-Hallucination Check",
            "start_ms": t0_offset,
            "duration_ms": _ms(t_step),
            "status": "ok" if verifier_result.get("all_citations_verified", False) else "warn",
            "detail": verifier_result.get("verification_badge", "Citations verified"),
            "payload": verifier_result,
        })

        # Steps 6 and 8 each make their own model call and neither reads the
        # other's result, so they run together rather than one after the other.
        # Step 7 is pure in-memory ranking and runs here while they are in flight.
        def _timed_draft():
            t0 = time.perf_counter()
            off = round((t0 - pipeline_start) * 1000.0, 2)
            res = DraftingAgent.draft_document(
                category=category,
                facts=facts,
                user_message=redacted_message,
                history=history,
                remedies=remedies
            )
            return res, off, _ms(t0)

        def _timed_guidance():
            t0 = time.perf_counter()
            off = round((t0 - pipeline_start) * 1000.0, 2)
            res = ConversationalAgent.generate_human_response(
                user_query=redacted_message,
                category=category,
                facts=facts,
                remedies=remedies,
                triage=triage_result,
                language=language,
                history=history
            )
            return res, off, _ms(t0)

        with ThreadPoolExecutor(max_workers=2) as pool:
            draft_future = pool.submit(_timed_draft)
            guidance_future = pool.submit(_timed_guidance)

            # Step 7: Handoff Agent - Advocate brief & matched verified lawyers
            t_handoff = time.perf_counter()
            handoff_off = round((t_handoff - pipeline_start) * 1000.0, 2)
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
            handoff_ms = _ms(t_handoff)
            exact_location_matches = [a for a in matched_advocates if a.get("is_location_match")]
            location_matched_count = len(exact_location_matches) if exact_location_matches else (1 if (city or district_court) else len(matched_advocates))

            # Step 6 result: the synchronized legal notice draft
            draft_result, draft_off, draft_ms = draft_future.result()
            # Step 8 result: the plain-language reply
            guidance_text, guidance_off, guidance_ms = guidance_future.result()

        # Hallucination Firewall: if the user asked to cite a non-existent statute/section,
        # prepend an explicit refusal and ensure no unrelated fallback precedent,
        # money-recovery notice, or monetary-only advocate match leaks through.
        if verifier_result.get("hallucination_guard_triggered"):
            blocked = ", ".join(verifier_result.get("unverified_query_citations", []))
            guard_notice = (
                f"⚠️ **Citation Verification Guardrail:** I cannot cite **{blocked}**, "
                "as it does not exist in the authenticated Indian Bare Acts corpus. "
                "OnlineVakeel.com does not fabricate statutory sections or case law.\n\n"
            )
            is_noise_dispute = category == "general_civil" and any(
                n in redacted_message.lower()
                for n in ("loud music", "noise", "neighbor", "neighbour", "nuisance")
            )
            if is_noise_dispute:
                guidance_text = (
                    guard_notice
                    + "For a **neighbor noise / loud music dispute** in India, the relevant legal avenues are:\n"
                    "- **Public Nuisance (Section 270, Bharatiya Nyaya Sanhita, 2023):** Addresses acts causing common injury, danger, or annoyance to the public or neighbors.\n"
                    "- **Noise Pollution (Regulation and Control) Rules, 2000:** Prohibits loudspeakers/loud music beyond permissible decibel limits, especially between **10:00 PM and 6:00 AM**.\n"
                    "- **Immediate Practical Steps:** Call **112** (Police) if the disturbance is ongoing at night, send a written complaint to your **RWA / Society** or local police station, or seek a **civil injunction**."
                )
                draft_result = {
                    "title": "Cease & Desist Notice — Noise & Public Nuisance (Section 270 BNS, 2023)",
                    "category": "general_civil",
                    "content": (
                        "LEGAL NOTICE (CEASE & DESIST — PUBLIC NUISANCE)\n\n"
                        "To,\n[Neighbour / Occupant Name & Address]\n\n"
                        "Subject: Formal Notice to Cease Excessive Noise / Loud Music Causing Public Nuisance\n\n"
                        "Sir/Madam,\n\n"
                        "1. That you are residing/occupying the adjacent premises and have been repeatedly playing loud music at unreasonable decibel levels, causing severe disturbance and mental distress.\n"
                        "2. That such conduct constitutes Public Nuisance under Section 270 of the Bharatiya Nyaya Sanhita (BNS), 2023, and violates the Noise Pollution (Regulation and Control) Rules, 2000 (particularly restricting loud sound between 10:00 PM and 6:00 AM).\n"
                        "3. You are hereby called upon to immediately cease and desist from creating excessive noise, failing which my client shall be constrained to lodge a police complaint / approach the competent Civil Court for injunctive relief.\n\n"
                        "Note: Unverified statutory references requested in the query were blocked by the Citation Verification Guardrail."
                    ),
                }
                # Filter out monetary/cheque-bounce specialists for non-monetary civil nuisance disputes
                civil_only = [
                    a for a in matched_advocates
                    if "general_civil" in (a.get("practice_areas") or [])
                    and "cheque_bounce" not in (a.get("practice_areas") or [])
                ]
                if civil_only:
                    matched_advocates = civil_only
            else:
                if blocked.lower() not in guidance_text.lower() or "cannot cite" not in guidance_text.lower():
                    guidance_text = guard_notice + guidance_text
                draft_result = {
                    "title": "Notice Draft Paused — Citation Verification Guardrail",
                    "category": category,
                    "content": (
                        f"Drafting paused: The query referenced unverified statutory citation(s) ({blocked}). "
                        "OnlineVakeel.com does not generate legal notices citing unverified or non-existent statutes. "
                        "Please clarify the underlying facts or consult a verified advocate."
                    ),
                }

        spans.append({
            "step": "6. Live Notice Drafter",
            "agent": "DraftingAgent",
            "model_or_tool": "Qwen/Qwen3-8B (vm07-ca.crt) / Template",
            "start_ms": draft_off,
            "duration_ms": draft_ms,
            "status": "ok",
            "detail": f"Drafted: {draft_result.get('title', 'Legal Notice')}",
            "payload": {
                "title": draft_result.get("title", "Legal Notice"),
                "notice_preview": (draft_result.get("content") or "")[:1000],
            },
        })
        spans.append({
            "step": "7. Advocate Matching",
            "agent": "HandoffAgent",
            "model_or_tool": "Jurisdiction & Practice Ranker",
            "start_ms": handoff_off,
            "duration_ms": handoff_ms,
            "status": "ok",
            "detail": f"Matched {len(matched_advocates)} advocate(s) ({location_matched_count} local)",
            "payload": {
                "location_matched_count": location_matched_count,
                "top_advocates": [
                    {
                        "name": a.get("name"),
                        "city": a.get("city"),
                        "practice_areas": a.get("practice_areas"),
                        "consult_fee": a.get("consult_fee"),
                    }
                    for a in matched_advocates[:5]
                ],
            },
        })
        spans.append({
            "step": "8. Conversational Guidance",
            "agent": "ConversationalAgent",
            "model_or_tool": "Qwen/Qwen3-8B (vm07-ca.crt)",
            "start_ms": guidance_off,
            "duration_ms": guidance_ms,
            "status": "ok",
            "detail": f"Generated {len(guidance_text)} chars of plain-language guidance",
            "payload": {
                "character_count": len(guidance_text),
                "language": language,
                "answer_excerpt": guidance_text[:500] + ("..." if len(guidance_text) > 500 else ""),
            },
        })

        total_latency_ms = _ms(pipeline_start)
        trace_record = {
            "trace_id": trace_id,
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "redacted_query": redacted_message[:220] + ("..." if len(redacted_message) > 220 else ""),
            "category": category,
            "urgency": triage_result.get("urgency", "routine"),
            "pii_redacted_count": len(redactions),
            "pii_types": redactions,
            "citations_count": len(remedies),
            "citations": cited_titles,
            "verified": bool(verifier_result.get("all_citations_verified", False)),
            "verification_badge": verifier_result.get("verification_badge", "Verified"),
            "matched_advocates_count": len(matched_advocates),
            "notice_title": draft_result.get("title", "Legal Notice"),
            "final_answer": guidance_text,
            "total_latency_ms": total_latency_ms,
            "spans": spans,
        }
        cls.TRACE_LOG.append(trace_record)
        if len(cls.TRACE_LOG) > cls.MAX_TRACES:
            cls.TRACE_LOG.pop(0)

        # Save / Update session state
        cls.ACTIVE_SESSIONS[case_id] = {
            "case_id": case_id,
            "category": category,
            "facts": facts,
            "remedies": remedies,
            "updated_at": uuid.uuid4().hex
        }

        return {
            "trace_id": trace_id,
            "total_latency_ms": total_latency_ms,
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
