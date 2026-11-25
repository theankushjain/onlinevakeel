import logging
import os
import re
import time
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class ConversationalAgent:
    """
    Conversational Agent: Translates complex statutory provisions and court procedures
    into warm, empathetic, and crystal-clear layman guidance for everyday citizens.
    Powered by hybrid intelligence: Gemini 3.5 Flash + Capstone Qwen3-8B + Deterministic Legal Corpus.
    """

    #: Total wall-clock budget for the Gemini step, across every model tried.
    GEMINI_TOTAL_BUDGET_S = 12.0

    @classmethod
    def generate_human_response(
        cls,
        user_query: str,
        category: str,
        facts: Dict[str, Any],
        remedies: List[Dict[str, Any]],
        triage: Dict[str, Any],
        language: str = "en",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        ans = None

        # Check if query is in Hindi / Devanagari script
        is_hindi = (language or "").startswith("hi") or any('\u0900' <= char <= '\u097F' for char in user_query)

        # 1. If Hindi query, prioritize Qwen3-8B for nuanced vernacular reasoning
        if is_hindi and settings.QWEN_API_KEY:
            try:
                ans = cls._call_qwen_api(user_query, category, facts, remedies, triage, language, history)
            except Exception as e:
                logger.debug(f"Qwen Hindi call failed: {e}")

        # 2. Try Gemini 3.5 Flash if not yet answered
        if not ans and settings.GEMINI_API_KEY:
            try:
                llm_response = cls._call_gemini_api(user_query, category, facts, remedies, triage, language, history)
                if llm_response:
                    ans = llm_response
            except Exception as e:
                logger.warning(f"Gemini API call failed, attempting Qwen fallback: {e}")

        # 3. Resilient Secondary Fallback: Qwen3-8B (vLLM VM07)
        if not ans and settings.QWEN_API_KEY:
            try:
                ans = cls._call_qwen_api(user_query, category, facts, remedies, triage, language, history)
            except Exception as e:
                logger.warning(f"Qwen API fallback failed: {e}")

        # 4. Resilient Deterministic Statutory Explanation Engine
        if not ans:
            ans = cls._generate_layman_explanation(category, facts, remedies, triage, language, history, user_query)

        # 4a. Emergency helplines, whichever engine produced the text above.
        # This used to live only inside the template engine, so a citizen who
        # got a model-written answer never saw a helpline at all.
        emergency = cls._emergency_prefix(triage)
        if emergency and "15100" not in ans:
            ans = f"{emergency}\n\n{ans}"

        # 5. Location Prompt and Confirmation Engine
        has_location = bool(
            facts.get("locations_mentioned") or 
            facts.get("district_courts_mentioned") or 
            facts.get("detected_district")
        )
        
        if not has_location:
            ans_lower = ans.lower()
            asked_for_loc = (
                "which city" in ans_lower or 
                "what city" in ans_lower or 
                "which district" in ans_lower or 
                "mention your city" in ans_lower or
                "what is your city" in ans_lower or
                "what is your district" in ans_lower or
                "कौन से शहर" in ans_lower or
                "किस शहर" in ans_lower or
                "ज़िला न्यायालय" in ans_lower
            )
            if not asked_for_loc:
                # Kept to one line. The phrases "which city" / "शहर" are also what
                # the frontend looks for to detect that we asked — do not drop them.
                if (language or "en").startswith("hi"):
                    ans += (
                        "\n\n📍 **आप किस शहर में हैं?** अपना शहर या नज़दीकी "
                        "ज़िला न्यायालय बताइए — मैं वहीं के वकील दिखाऊँगा।"
                    )
                else:
                    ans += (
                        "\n\n📍 **Which city are you in?** Tell me your city or nearest "
                        "district court and I will shortlist advocates who appear there."
                    )
        else:
            # Strip out any lingering question asking for location that the LLM may have generated
            patterns_to_strip = [
                r'\*?\(?To suggest verified advocates who practice before your exact local District Court.*?\)?\*?',
                r'📍\s*\*\*Which city or district court are you in\?\*\*.*',
                r'📍\s*\*\*आपका शहर व ज़िला न्यायालय\?\*\*.*',
                r'\(?could you (?:also )?tell me which city[^\.\n]*\??\)?',
                r'\(?could you (?:also )?mention which city[^\.\n]*\??\)?',
                r'which city or district are you located in\??',
                r'what city are you in\??',
                r'what is your city\??',
                r'what is your district\??',
                r'किस शहर में स्थित हैं\??',
                r'कौन से शहर में स्थित हैं\??',
            ]
            for pat in patterns_to_strip:
                ans = re.sub(pat, '', ans, flags=re.IGNORECASE).strip()

            detected_district = facts.get("detected_district") or ""
            detected_state = facts.get("detected_state") or ""
            detected_court = facts.get("detected_court") or (facts.get("district_courts_mentioned") or [""])[0]
            detected_city = (facts.get("locations_mentioned") or [""])[0]
            detected_loc = (facts.get("localities_mentioned") or [""])[0]

            loc_parts = []
            if detected_loc and detected_loc != detected_district and detected_loc != detected_city:
                loc_parts.append(detected_loc)
            if detected_court:
                loc_parts.append(detected_court)
            if detected_district and detected_district not in str(loc_parts):
                loc_parts.append(detected_district)
            elif detected_city and detected_city not in str(loc_parts):
                loc_parts.append(detected_city)
            if detected_state and detected_state not in str(loc_parts):
                loc_parts.append(detected_state)
            
            loc_summary = ", ".join(loc_parts) if loc_parts else (detected_district or detected_city)
            
            # Confirm the match once, on the turn the location is first resolved.
            # Repeating it on every later turn added a paragraph to each reply
            # and told the citizen nothing new.
            already_confirmed = any(
                "location matched" in (turn.get("text") or "").lower()
                for turn in (history or [])
                if turn.get("sender") not in ("user", "citizen")
            )
            if (loc_summary and not already_confirmed
                    and "verified advocates practicing in" not in ans.lower()
                    and "location matched" not in ans.lower()):
                ans += (
                    f"\n\n🎯 **Location matched** — advocates practising in **{loc_summary}** "
                    f"are now at the top of your list."
                )
        return ans

    @classmethod
    def _call_gemini_api(
        cls,
        user_query: str,
        category: str,
        facts: Dict[str, Any],
        remedies: List[Dict[str, Any]],
        triage: Dict[str, Any],
        language: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        # Ordered by measured response time, fastest first. gemini-3.5-flash is
        # last because it regularly takes 14s or more, well past our timeout.
        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.5-flash"
        ]
        api_key = settings.GEMINI_API_KEY
        
        system_instruction = """You are 'OnlineVakeel' (ऑनलाइन वकील), an empathetic, warm, and highly practical Indian legal counselor.
Your mission is to guide Indian citizens who are feeling stressed, cheated, or confused about their legal rights.
GUIDELINES:
1. Tone: Warm, reassuring, and conversational — like a senior advocate explaining things over tea to a worried family member.
2. Jargon-free: Explain the law in simple everyday terms (layman English or simple Hindi if queried in Hindi).
3. MULTI-TURN CONTEXT AWARENESS:
   - If this is a follow-up question (e.g. 'I secretly recorded a video', 'what if they ignore it?', 'I am in Noida', 'can I use stamp paper in court?', 'what about police FIR?'):
     * NEVER start with a generic greeting or restart the consultation from scratch!
     * Directly and precisely answer the user's specific follow-up question in depth.
     * Explain exact admissibility, relevant sections (e.g. Section 63 BSA / 65B Evidence Act, Section 175 BNSS, Section 318 BNS), and practical court steps.
     * Keep your answer anchored to their ongoing case details (disputed item/amount, city, counterparty).
4. Grounding: Rely strictly on verified statutory provisions and established Indian judicial precedents. Do not invent section numbers or case laws.
5. LOCATION & LOCAL ADVOCATE JURISDICTION:
   - If Extracted Case Facts already has locations_mentioned, detected_district, or district_courts_mentioned, or if the user already stated their city in the chat:
     * DO NOT ask them which city or district they are located in!
     * Instead, acknowledge their location and confirm how local jurisdiction applies (e.g., District Court or Consumer Commission of their district).
   - ONLY if no location is mentioned anywhere, you may politely ask once at the conclusion of your response:
     '*(To suggest verified advocates who practice before your exact local District Court or High Court, could you also tell me which city or district you are located in?)*'
6. LENGTH — this matters as much as accuracy:
   - Answer a first question in at most 120 words. Answer a follow-up in at most 80.
   - Use this shape and nothing more: one short opening sentence, then at most 3 bullets, then one 'Next step:' line.
   - No preamble, no summary of what the citizen just told you, no closing pleasantries.
   - The citizen already sees the full statutory detail in a panel beside the chat, so do not
     reproduce long explanations of each section here. Name the section and move on."""

        formatted_history = ""
        if history and len(history) > 0:
            formatted_history = "\nPREVIOUS CONVERSATION HISTORY:\n"
            for turn in history[-8:]:
                sender = "Citizen" if turn.get("sender") in ["user", "citizen"] else "OnlineVakeel"
                txt = turn.get("text", "")[:350]
                formatted_history += f"{sender}: {txt}\n"

        context_data = f"""
Category: {category}
User Latest Query: {user_query}
Extracted Case Facts: {facts}
Verified Statutory Remedies from Database: {remedies}
Urgency Level: {triage.get('urgency')}
Language Preference: {language}
{formatted_history}
"""

        # Primary payload with thinking budget to prevent unconstrained thinking timeouts
        payload_with_budget = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\nCase Context:\n{context_data}\n\nPlease generate your direct, human-friendly legal counsel response to the user's latest query now."}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                # Thinking tokens are drawn from maxOutputTokens, so this ceiling
                # has to leave room for both. Dropping it to 400 while keeping a
                # 256-token budget starves the answer down to a dozen words.
                "maxOutputTokens": 900,
                "thinkingConfig": {"thinkingBudget": 128}
            }
        }

        # Fallback payload without thinking config for models that don't support thinkingConfig
        payload_standard = {
            "contents": payload_with_budget["contents"],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 900
            }
        }

        # Overall budget for this step. Without it, four model names at nine
        # seconds each could keep a citizen waiting well past half a minute
        # before the written-out fallback ever ran.
        deadline = time.monotonic() + cls.GEMINI_TOTAL_BUDGET_S

        for model_name in models_to_try:
            remaining = deadline - time.monotonic()
            if remaining <= 1.0:
                logger.info("Gemini budget exhausted; falling through to the next engine.")
                break
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            for payload in [payload_with_budget, payload_standard]:
                try:
                    with httpx.Client(timeout=min(9.0, max(1.0, deadline - time.monotonic()))) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidate = data["candidates"][0]
                            text = candidate["content"]["parts"][0]["text"]
                            # thinkingBudget is a hint, not a hard cap: a model
                            # can think past it and leave too little room for the
                            # answer, which comes back cut off mid-sentence.
                            # Never show the citizen a half-finished citation.
                            if candidate.get("finishReason") == "MAX_TOKENS":
                                logger.warning(
                                    f"Gemini {model_name} hit the output cap; discarding the partial answer."
                                )
                                break
                            if text and len(text.strip()) > 30:
                                return text.strip()
                        elif resp.status_code == 400 and payload == payload_with_budget:
                            # Model might not support thinkingConfig, try standard payload
                            continue
                        else:
                            logger.warning(f"Gemini model {model_name} returned {resp.status_code}: {resp.text[:120]}")
                            break
                except Exception as e:
                    logger.warning(f"Error calling {model_name}: {e}")
                    break
        return ""

    @classmethod
    def _call_qwen_api(
        cls,
        user_query: str,
        category: str,
        facts: Dict[str, Any],
        remedies: List[Dict[str, Any]],
        triage: Dict[str, Any],
        language: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Executes inference via the Capstone Qwen3-8B model (IIT KGP cluster).
        Enforces token caps (max 600) and SSL CA certificate verification.
        """
        if not settings.QWEN_API_KEY:
            return None

        system_instruction = (
            "You are 'OnlineVakeel' (ऑनलाइन वकील), an empathetic, warm, and highly practical Indian legal counselor. "
            "Your mission is to guide Indian citizens who are feeling stressed, cheated, or confused about their legal rights. "
            "Explain the law in simple everyday terms (layman English or simple conversational Hindi if queried in Hindi). "
            "Rely strictly on verified statutory provisions and established Indian legal remedies. Do not invent sections or laws. "
            "LENGTH: answer in at most 110 words — one short opening sentence, then at most 3 bullets, then one "
            "'Next step:' line. No preamble and no restating the question. Name the governing section rather than "
            "explaining it at length; the citizen already sees the full provision in a panel beside the chat."
        )

        messages = [{"role": "system", "content": system_instruction}]

        if history:
            for turn in history[-4:]:
                sender = "user" if turn.get("sender") in ["user", "citizen"] else "assistant"
                txt = turn.get("text", "")[:280]
                if txt:
                    messages.append({"role": sender, "content": txt})

        remedies_summary = "; ".join([
            f"{r.get('act_name', 'Indian Act')} Sec {r.get('section', '')}: {r.get('title', '')}"
            for r in remedies[:3]
        ])

        user_content = (
            f"Citizen Legal Situation: {user_query}\n"
            f"Case Category: {category}\n"
            f"Facts Identified: {facts}\n"
            f"Governing Statutory Remedies: {remedies_summary}\n\n"
            f"Name the governing section, give at most three short practical steps, and stop. "
            f"Stay within 110 words."
        )
        if (language or "en").startswith("hi"):
            user_content += " Please explain in clear, natural conversational Hindi (हिंदी)."

        messages.append({"role": "user", "content": user_content})

        try:
            cert_path = settings.QWEN_CA_CERT_PATH if os.path.exists(settings.QWEN_CA_CERT_PATH) else True
            with httpx.Client(verify=cert_path, timeout=35.0) as client:
                res = client.post(
                    f"{settings.QWEN_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.QWEN_MODEL,
                        "messages": messages,
                        # 400 was being hit mid-sentence (finish_reason="length"),
                        # so answers arrived truncated. With the length rule above
                        # the model now stops on its own well inside this ceiling.
                        "max_tokens": 320,
                        "temperature": 0.35
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and len(choices) > 0:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content:
                            logger.info("Qwen3-8B successfully synthesized citizen legal counsel response.")
                            return content
                elif res.status_code == 429:
                    logger.warning("Qwen3-8B busy (active request limit 1). Falling back to secondary engine.")
                else:
                    logger.warning(f"Qwen API returned HTTP {res.status_code}: {res.text[:120]}")
        except Exception as e:
            logger.warning(f"Qwen API call encountered error (falling back to secondary): {e}")

        return None

    # ------------------------------------------------------------------ #
    # Deterministic explanation engine                                     #
    # ------------------------------------------------------------------ #
    # Every answer uses the same shape: one plain-language sentence, up to
    # three short bullets, one next step. The full statutory detail stays in
    # the Remedies panel beside the chat, so the conversation stays readable.

    #: What a contemporaneous recording actually proves, by legal domain.
    PROOF_BY_CATEGORY = {
        "property_rera": "it captures the builder accepting your money and admitting the delay",
        "cheque_bounce": "it supports the debt the cheque was issued against",
        "consumer_dispute": "it records what the seller actually promised you",
        "cyber_fraud": "it shows how you were induced into the transaction",
        "employment_labour": "it records what your employer agreed to pay",
        "criminal_bail": "it records what was said at the time of the incident",
    }
    DEFAULT_PROOF = "it records what the other side actually said at the time"

    #: Where each kind of matter is finally decided.
    FORUM_BY_CATEGORY = {
        "property_rera": "State RERA Authority",
        "cheque_bounce": "Judicial Magistrate",
        "consumer_dispute": "District Consumer Commission",
        "cyber_fraud": "cyber crime cell and the Magistrate",
        "rti_public": "First Appellate Authority",
    }
    DEFAULT_FORUM = "competent court"

    @staticmethod
    def _compose(headline: str, bullets: Optional[List[str]] = None,
                 next_step: str = "", prefix: str = "") -> str:
        """Assemble the fixed answer shape and keep it short."""
        blocks = []
        if prefix:
            blocks.append(prefix)
        blocks.append(headline)
        if bullets:
            blocks.append("\n".join(f"- {point}" for point in bullets[:3]))
        if next_step:
            blocks.append(f"**Next step:** {next_step}")
        return "\n\n".join(blocks)

    @classmethod
    def _emergency_prefix(cls, triage: Dict[str, Any]) -> str:
        """Safety first: this is prefixed before any other routing."""
        if triage.get("urgency") != "emergency":
            return ""
        return (
            "🚨 **If anyone is in immediate danger, call 112 now.** "
            "Free legal aid: NALSA **15100** · Women **1091** · Cyber fraud **1930**."
        )

    @classmethod
    def _generate_layman_explanation(
        cls,
        category: str,
        facts: Dict[str, Any],
        remedies: List[Dict[str, Any]],
        triage: Dict[str, Any],
        language: str,
        history: Optional[List[Dict[str, Any]]] = None,
        user_query: str = ""
    ) -> str:
        amount = facts.get("monetary_amount") or "the amount in dispute"
        city = (facts.get("locations_mentioned") or [""])[0]
        label = category.replace("_", " ").title()
        q = (user_query or "").lower()

        # The emergency line is built first so that it survives every branch
        # below. A short message mentioning the police or a recording must not
        # cost the citizen their helpline.
        prefix = cls._emergency_prefix(triage)
        proof = cls.PROOF_BY_CATEGORY.get(category, cls.DEFAULT_PROOF)
        forum = cls.FORUM_BY_CATEGORY.get(category, cls.DEFAULT_FORUM)

        # ---------------- follow-up questions, answered in context ---------
        if any(w in q for w in ["video", "record", "recording", "audio", "sting",
                                "camera", "taped", "call record"]):
            return cls._compose(
                "A recording you made yourself can normally be used as evidence in an Indian court.",
                [
                    "Indian evidence law turns on relevance, so a recording made without the other "
                    "side's knowledge is not shut out for that reason alone.",
                    f"In your matter {proof}.",
                    "Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 requires a signed certificate "
                    "confirming the file is original and untampered.",
                ],
                "Keep the original phone or memory card untouched — do not forward the file on "
                "WhatsApp, which strips its metadata. Your advocate will prepare the certificate.",
                prefix,
            )

        if any(w in q for w in ["stamp paper", "100 rs", "100 rupee", "notary",
                                "notarized", "unregistered", "agreement"]):
            return cls._compose(
                "The stamp paper does not transfer ownership, but it is still strong evidence.",
                [
                    "Under the Registration Act, 1908, immovable property passes only by a "
                    "registered sale deed.",
                    "The proviso to Section 49 of that Act lets an unregistered agreement be read "
                    "as evidence of the contract and of the money paid.",
                    f"So it is written proof that {amount} changed hands on agreed terms.",
                ],
                "Keep the original safe and list it as an annexure to your notice.",
                prefix,
            )

        if any(w in q for w in ["police", "fir", "thana", "station", "chowki",
                                "refuse", "not registering", "not filing"]):
            return cls._compose(
                "If the police will not register your FIR, there is a defined route above them.",
                [
                    "Send the complaint in writing to the Superintendent of Police or DCP by "
                    "registered post with acknowledgement due.",
                    "If that goes unanswered, your advocate applies to the Judicial Magistrate "
                    "under Section 175(3) of the Bharatiya Nagarik Suraksha Sanhita, 2023.",
                    "The Magistrate can direct the station to register the FIR and report back.",
                ],
                "Keep the postal receipt — it is your proof that the complaint was made.",
                prefix,
            )

        if any(w in q for w in ["ignore", "not replying", "no reply", "15 days",
                                "expired", "after notice"]):
            return cls._compose(
                "If they ignore the 15-day notice, that silence works in your favour.",
                [
                    "The 15-day window exists to complete your cause of action; once it lapses "
                    "you are free to file.",
                    "Sent by registered post, Section 27 of the General Clauses Act presumes the "
                    "notice was duly served.",
                    f"Your advocate can then move the {forum}.",
                ],
                "Keep the postal receipt and the tracking printout — both go in as annexures.",
                prefix,
            )

        is_follow_up = bool(history and len(history) > 1) or len(q.split()) < 15
        if is_follow_up:
            where = f" An advocate in {city} can review the papers and file without delay." if city else ""
            return cls._compose(
                f"On your {label.lower()} matter, here is where things stand.",
                [
                    "Keep every receipt, message and document together in date order.",
                    "The draft notice on the right already carries the facts you have given so far.",
                ],
                f"Tell me any new fact and the notice updates itself.{where}",
                prefix,
            )

        # ---------------- first full answer, by legal domain ---------------
        if category == "cheque_bounce":
            return cls._compose(
                f"A bounced cheque of {amount} is a criminal offence under Section 138 of the "
                "Negotiable Instruments Act, 1881.",
                [
                    "The demand notice must go out within **30 days** of the bank's return memo.",
                    "The person who issued the cheque then has **15 days** to pay.",
                    "If they do not, you can file before the Magistrate — up to 2 years' "
                    "imprisonment, or a fine of twice the cheque amount.",
                ],
                "The Section 138 notice is ready on the right. Send it by registered post.",
                prefix,
            )

        if category == "property_rera":
            return cls._compose(
                f"Under Section 18 of the RERA Act, 2016 the delay gives you a choice, and "
                f"{amount} is recoverable either way.",
                [
                    "Withdraw from the project and claim the full amount back with interest at "
                    "your State's prescribed rate.",
                    "Or stay in the project and claim interest for every month of delay until "
                    "you get possession.",
                    "The claim goes to the State RERA Authority, not to a civil court.",
                ],
                "Issue the Section 18 notice on the right, giving the builder 15 days to respond.",
                prefix,
            )

        if category == "consumer_dispute":
            return cls._compose(
                f"Section 35 of the Consumer Protection Act, 2019 covers a defective product or "
                f"deficient service worth {amount}.",
                [
                    "You can claim a refund or a replacement, plus compensation for the trouble caused.",
                    "You have **2 years** from the date the problem arose.",
                    "File online through the e-Daakhil portal, or at the District Commission where "
                    "you live or work.",
                ],
                "Send the notice on the right first — most companies settle once a formal notice arrives.",
                prefix,
            )

        if category == "cyber_fraud":
            return cls._compose(
                "Call **1930** now — the first few hours decide whether the money can still be frozen.",
                [
                    "Report on 1930 and at cybercrime.gov.in, and keep the acknowledgement number.",
                    f"Online cheating of {amount} is punishable under Section 318 of the Bharatiya "
                    "Nyaya Sanhita, 2023.",
                    "Save every screenshot, UTR number and call log.",
                ],
                "Tell your bank in writing the same day and keep their acknowledgement.",
                prefix,
            )

        if category == "rti_public":
            return cls._compose(
                "You can demand these records under Section 6(1) of the Right to Information Act, 2005.",
                [
                    "The fee is ₹10, payable by Indian Postal Order or online.",
                    "The Public Information Officer must reply within **30 days**.",
                    "A late or false reply can cost the officer ₹250 a day, up to ₹25,000.",
                ],
                "The RTI application is drafted on the right — address it to the PIO of that department.",
                prefix,
            )

        cite = remedies[0].get("statutory_cite") if remedies else ""
        return cls._compose(
            f"Here is where your {label.lower()} matter stands.",
            [
                f"The provision that applies is {cite}." if cite else
                "The verified sections that apply are listed in the panel on the right.",
                "A written notice is the normal first step before approaching any court or tribunal.",
                "Keep the paper trail — receipts, messages and dates, in order.",
            ],
            f"Review the draft notice on the right" + (f" and connect with an advocate in {city}." if city else "."),
            prefix,
        )
