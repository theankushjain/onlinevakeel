import logging
import time
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class DraftingAgent:
    """
    Drafting Agent: Generates & continuously updates pre-litigation statutory documents
    (Legal Demand Notices, Electronic Evidence Certificates under Sec 63 BSA, RTI Applications)
    dynamically synchronized with every turn of the citizen-counsel conversation.
    """

    #: Total wall-clock budget for the Gemini drafting step, across every model tried.
    GEMINI_TOTAL_BUDGET_S = 18.0

    @classmethod
    def draft_document(
        cls,
        category: str,
        facts: Dict[str, Any],
        user_message: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        remedies: Optional[List[Dict[str, Any]]] = None,
        citizen_name: str = "Client (Name Protected)",
        opponent_name: str = "Opponent Party / Noticee"
    ) -> Dict[str, Any]:
        """
        Drafts or updates a formal legal notice incorporating all ongoing case facts,
        statutory remedies, and newly disclosed evidence from the chat.
        """
        today_str = datetime.now().strftime("%d-%B-%Y")
        amount = facts.get("monetary_amount") or "INR [Specify Disputed Amount]"
        dates = ", ".join(facts.get("dates_mentioned", [])) or today_str
        city = (facts.get("locations_mentioned") or ["New Delhi"])[0]

        # 1. Gather all conversation text to understand complete evolving context
        combined_text_list = []
        if history:
            for turn in history:
                if turn.get("sender") in ["user", "citizen"]:
                    combined_text_list.append(turn.get("text", ""))
        if user_message:
            combined_text_list.append(user_message)
        full_user_context = " ".join(combined_text_list)
        full_context_lower = full_user_context.lower()

        # 2. Extract specific evidence & factual elements from conversation
        has_video = any(w in full_context_lower for w in ["video", "record", "recording", "audio", "camera", "sting", "taped", "call record"])
        has_stamp = any(w in full_context_lower for w in ["stamp paper", "100 rs", "100 rupee", "notary", "unregistered", "agreement"])
        has_cash = any(w in full_context_lower for w in ["cash", "nakad", "handover", "currency"])
        has_plot_fraud = any(w in full_context_lower for w in ["plot", "land", "relative", "not their", "not theirs", "fake title", "unapproved", "rera"])
        has_cheque = any(w in full_context_lower for w in ["cheque", "check", "bounce", "dishonour", "return memo", "138"])
        has_consumer = any(w in full_context_lower for w in ["consumer", "defective", "warranty", "refund", "damaged", "replacement"])

        incorporated_facts = []
        if facts.get("monetary_amount"):
            incorporated_facts.append(f"Disputed Amount: {facts['monetary_amount']}")
        if has_cash:
            incorporated_facts.append("Payment Mode: Cash Consideration Handover")
        if has_stamp:
            incorporated_facts.append("Contract Document: Agreement on ₹100 Stamp Paper")
        if has_video:
            incorporated_facts.append("Contemporaneous Proof: Video Recording (Sec 63 BSA Preserved)")
        if has_plot_fraud:
            incorporated_facts.append("Cause of Action: Fraudulent Land Sale & Cheating (Sec 318 BNS)")

        # 3. Attempt Dynamic LLM Drafting if Gemini API key configured
        if settings.GEMINI_API_KEY:
            try:
                llm_draft = cls._call_gemini_drafting(
                    category=category,
                    facts=facts,
                    user_message=user_message,
                    history=history,
                    remedies=remedies,
                    citizen_name=citizen_name,
                    opponent_name=opponent_name,
                    city=city,
                    today_str=today_str,
                    amount=amount,
                    has_video=has_video,
                    has_stamp=has_stamp
                )
                if llm_draft and len(llm_draft.strip()) > 300:
                    title = cls._extract_title(llm_draft, category)
                    return {
                        "title": title,
                        "notice_type": f"{category}_legal_notice",
                        "content": llm_draft.strip(),
                        "statutory_period": "15 Days Statutory Window",
                        "jurisdiction": city,
                        "incorporated_facts": incorporated_facts,
                        "last_updated": datetime.now().strftime("%I:%M %p"),
                        "evidence_flags": {"video": has_video, "stamp": has_stamp, "cash": has_cash}
                    }
            except Exception as e:
                logger.warning(f"Gemini legal notice drafting failed, using dynamic procedural generator: {e}")

        # 4. Fallback: Intelligent Deterministic Legal Notice Engine
        return cls._generate_dynamic_notice(
            category=category,
            facts=facts,
            full_context_lower=full_context_lower,
            has_video=has_video,
            has_stamp=has_stamp,
            has_cash=has_cash,
            has_plot_fraud=has_plot_fraud,
            has_cheque=has_cheque,
            has_consumer=has_consumer,
            citizen_name=citizen_name,
            opponent_name=opponent_name,
            city=city,
            today_str=today_str,
            amount=amount,
            dates=dates,
            incorporated_facts=incorporated_facts
        )

    @classmethod
    def _call_gemini_drafting(
        cls,
        category: str,
        facts: Dict[str, Any],
        user_message: str,
        history: Optional[List[Dict[str, Any]]],
        remedies: Optional[List[Dict[str, Any]]],
        citizen_name: str,
        opponent_name: str,
        city: str,
        today_str: str,
        amount: str,
        has_video: bool,
        has_stamp: bool
    ) -> str:
        models_to_try = [
            # Ordered by measured response time, fastest first. The previous
            # order put gemini-3.5-flash second, and it regularly consumed the
            # full timeout before a usable draft came back.
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.5-flash"
        ]
        api_key = settings.GEMINI_API_KEY

        formatted_history = ""
        if history and len(history) > 0:
            formatted_history = "\nCONSULTATION CHAT TRANSCRIPT:\n"
            for turn in history[-6:]:
                sender = "Citizen" if turn.get("sender") in ["user", "citizen"] else "OnlineVakeel"
                formatted_history += f"{sender}: {turn.get('text', '')[:300]}\n"

        prompt = f"""You are a Senior Indian Advocate drafting an official Pre-Litigation Statutory Legal Notice for service by Registered Post A.D. / Speed Post.
The notice must strictly reflect the actual evolving facts from this citizen consultation:

CASE DATA:
- Citizen: {citizen_name}
- Opponent / Noticee: {opponent_name}
- City Jurisdiction: {city}
- Date: {today_str}
- Disputed Stake: {amount}
- Category: {category}
- Specific Facts Extracted: {facts}
- Latest Citizen Message: {user_message}
{formatted_history}

SPECIAL STATUTORY REQUIREMENTS:
1. If the citizen disclosed a video/audio recording: You MUST add an explicit paragraph pleading the contemporaneous video recording as electronic evidence preserved in compliance with Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA).
2. If an agreement on stamp paper was mentioned: Plead it as written proof of transaction and receipt of consideration under Section 49 proviso of Registration Act, 1908.
3. If land/plot cheating was mentioned: Cite Section 318 (Cheating) and Section 316 (Criminal Breach of Trust) of Bharatiya Nyaya Sanhita, 2023 (BNS).
4. Demand full refund of {amount} with 18% p.a. interest within a strict statutory period of 15 DAYS.
5. Warn of immediate filing of criminal complaint before Judicial Magistrate under Section 175(3) BNSS and civil suit for recovery on default.

Draft the complete, professional Legal Notice text now with proper numbered paragraphs and legal terminology."""

        payload_with_budget = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1400,
                "thinkingConfig": {"thinkingBudget": 256}
            }
        }
        payload_standard = {
            "contents": payload_with_budget["contents"],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1400
            }
        }

        # Overall budget for this step; the deterministic generator below
        # produces a complete notice, so there is no reason to keep a citizen
        # waiting on a fourth slow model.
        deadline = time.monotonic() + cls.GEMINI_TOTAL_BUDGET_S

        for model_name in models_to_try:
            if deadline - time.monotonic() <= 1.0:
                logger.info("Gemini drafting budget exhausted; using the deterministic generator.")
                break
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            for payload in [payload_with_budget, payload_standard]:
                try:
                    with httpx.Client(timeout=min(12.0, max(1.0, deadline - time.monotonic()))) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidate = data["candidates"][0]
                            text = candidate["content"]["parts"][0]["text"]
                            # A notice cut off mid-clause is worse than no notice
                            # at all — fall through to the deterministic generator.
                            if candidate.get("finishReason") == "MAX_TOKENS":
                                logger.warning(
                                    f"Gemini {model_name} hit the output cap while drafting; discarding the partial notice."
                                )
                                break
                            if text and len(text.strip()) > 250:
                                return text.strip()
                        elif resp.status_code == 400 and payload == payload_with_budget:
                            continue
                        else:
                            break
                except Exception:
                    break
        return ""

    @classmethod
    def _generate_dynamic_notice(
        cls,
        category: str,
        facts: Dict[str, Any],
        full_context_lower: str,
        has_video: bool,
        has_stamp: bool,
        has_cash: bool,
        has_plot_fraud: bool,
        has_cheque: bool,
        has_consumer: bool,
        citizen_name: str,
        opponent_name: str,
        city: str,
        today_str: str,
        amount: str,
        dates: str,
        incorporated_facts: List[str]
    ) -> Dict[str, Any]:
        """
        Deterministic, robust legal notice generator that constructs paragraphs
        specifically addressing video evidence, stamp paper, cash handover, and fraud.
        """
        # A. Cheque Dishonour Case (Sec 138 NI Act)
        if has_cheque or category == "cheque_bounce":
            title = f"STATUTORY DEMAND NOTICE UNDER SECTION 138 NEGOTIABLE INSTRUMENTS ACT FOR {amount}"
            body = f"""REGISTERED SPEED POST WITH ACKNOWLEDGMENT DUE / LEGAL DEMAND NOTICE

Date: {today_str}
Place: {city}

TO,
{opponent_name}
[Address of the Drawer / Accused]

SUB: STATUTORY DEMAND NOTICE UNDER SECTION 138 READ WITH SECTION 142 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 FOR DISHONOUR OF CHEQUE OF {amount}

Sir / Madam,

Under instructions from and on behalf of my client, {citizen_name}, residing at {city}, India, I hereby serve upon you this formal Statutory Legal Demand Notice:

1. That in discharge of your legally enforceable debt, commercial liability, and financial commitment towards my client, you had issued and handed over a valid cheque in the sum of {amount} drawn on your bank account in favour of my client.

2. That my client presented the said cheque for encashment through their banker within its period of validity. However, the said cheque was returned dishonoured and unpaid by the drawee bank with the official Return Memo stating 'FUNDS INSUFFICIENT / EXCEEDS ARRANGEMENT' on {dates}.

3. That the dishonour of the said cheque has caused wrongful financial loss to my client, and your failure to maintain sufficient balance constitutes a cognizable criminal offence punishable under Section 138 of the Negotiable Instruments Act, 1881.

4. {"That my client is in possession of contemporaneous electronic records, communications, and acknowledgments substantiating the underlying debt, preserved in compliance with Section 63 of Bharatiya Sakshya Adhiniyam, 2023." if has_video else "That all original bank memos, deposit slips, and transaction records have been secured by my client for judicial production."}

5. I hereby formally call upon you to pay the entire cheque amount of {amount} to my client within a period of 15 (FIFTEEN) DAYS from the date of receipt of this notice.

6. Take notice that in default of payment within the aforesaid 15-day statutory window, my client shall immediately initiate criminal proceedings against you under Section 138 of the Negotiable Instruments Act, 1881 before the Court of the Metropolitan Magistrate / Judicial Magistrate First Class having jurisdiction, seeking imprisonment up to 2 years and a fine of twice the cheque amount, entirely at your sole risk, cost, and consequences.

Yours faithfully,

ADVOCATE FOR THE COMPLAINANT
Chambers of Legal Counsel, {city}
[Bar Council Reg. No: Enrolled Advocate]
"""
            notice_type = "cheque_bounce_notice"

        # B. Land / Plot Fraud, Relative Inducement, Stamp Paper, Secret Video Recording
        elif has_plot_fraud or category == "property_rera" or has_stamp:
            title = f"LEGAL DEMAND NOTICE FOR CHEATING & RECOVERY OF {amount} UNDER SECTIONS 316 & 318 BNS, 2023"
            
            video_para = (
                f"4. That my client is in lawful possession of contemporaneous video and audio recordings capturing the entire transaction, "
                f"wherein you explicitly acknowledged receiving the sum of {amount} in cash and falsely represented ownership and right to sell the said plot. "
                f"The said electronic recordings have been preserved in original, untampered digital format in strict compliance with Section 63 of the "
                f"Bharatiya Sakshya Adhiniyam, 2023 (BSA), and the original recording device and hash value have been secured for forensic submission before the court."
                if has_video else
                f"4. That you made repeated oral and written representations regarding clear and marketable title to the said land, which have now been verified to be completely fictitious and fraudulent."
            )

            stamp_para = (
                f"3. That to induce my client into parting with life-savings of {amount}, you executed an agreement on a Rs. 100 Stamp Paper. "
                f"While you knew that title to immovable property cannot transfer without a registered deed, you dishonestly executed the agreement to simulate legality. "
                f"Under the Proviso to Section 49 of the Registration Act, 1908, the said stamp paper agreement constitutes binding documentary evidence of the transaction, "
                f"payment of consideration, and your criminal intention to deceive."
                if has_stamp else
                f"3. That you wrongfully induced my client to part with {amount} without having lawful title or authority to alienate the property."
            )

            body = f"""REGISTERED SPEED POST A.D. / FORMAL PRE-LITIGATION & CRIMINAL LEGAL NOTICE

Date: {today_str}
Place: {city}

TO,
{opponent_name}
[Address of the Noticee / Relative]

SUB: LEGAL NOTICE FOR IMMEDIATE REFUND OF {amount} WITH 18% P.A. INTEREST AND NOTICE OF CRIMINAL PROCEEDINGS UNDER SECTIONS 316 & 318 OF BHARATIYA NYAYA SANHITA, 2023 (BNS) FOR FRAUDULENT PLOT TRANSACTION

Sir / Madam,

Under instructions from and on behalf of my client, {citizen_name}, resident of {city}, India, I hereby serve upon you this peremptory Legal Demand Notice:

1. That you, exploiting familial relations, trust, and goodwill, approached my client and offered to sell an unapproved plot of land situated in {city}, falsely representing and assuring that you were the sole, absolute, and undisputed owner with full legal right to convey title.

2. That relying upon your fraudulent representation, my client agreed to purchase the said plot and paid to you the total agreed consideration amounting to {amount} {"in cash" if has_cash else "towards the transaction"}.

{stamp_para}

{video_para}

5. That it has now come to my client's knowledge that you never held any valid title, ownership, or authority over the said plot, and that the property belongs to third parties. Your acts of misrepresentation, concealment, and wrongful pocketing of {amount} constitute criminal breach of trust under Section 316 BNS and cheating under Section 318(4) of the Bharatiya Nyaya Sanhita, 2023 (punishable with imprisonment up to 7 years and fine).

6. In addition, your failure to deliver an approved, marketable plot violates the fundamental principles of real estate regulation and entitles my client to immediate restitution of the entire principal amount along with interest.

7. I hereby call upon you to refund the complete sum of {amount} along with interest @ 18% per annum from the date of payment until realization, within 15 (FIFTEEN) DAYS of the receipt of this notice.

8. Take notice that if you fail to refund the said amount within the stipulated 15-day period, my client shall proceed to:
   (a) Lodge a formal FIR under Section 318(4) & 316 BNS with the police authorities, and if necessary, approach the Judicial Magistrate under Section 175(3) of BNSS, 2023;
   (b) File a Civil Suit for Recovery of {amount} with damages and attachment before judgment under Order 38 Rule 5 of CPC;
   Entirely at your risk, cost, and legal peril.

Yours faithfully,

ADVOCATE FOR THE CLIENT
Chambers of Legal Practice, {city}
[Enrolled Advocate, Bar Council of India]
"""
            notice_type = "property_fraud_legal_notice"

        # C. Consumer Dispute
        elif has_consumer or category == "consumer_dispute":
            title = f"LEGAL NOTICE UNDER SECTION 35 CONSUMER PROTECTION ACT FOR DEFICIENCY & REFUND OF {amount}"
            body = f"""REGISTERED LEGAL NOTICE (PRE-LITIGATION NOTICE)

Date: {today_str}
Place: {city}

TO,
{opponent_name}
[Authorized Representative / Grievance Officer]

SUB: LEGAL NOTICE UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019 FOR REFUND OF {amount} WITH COMPENSATION FOR DEFICIENCY IN SERVICE

Sir / Madam,

Under instructions from my client, {citizen_name}, residing at {city}, I hereby serve upon you this Legal Notice:

1. That my client purchased goods / availed services from your establishment on {dates} against total consideration of {amount}.

2. That the said product/service was discovered to be grossly defective, non-compliant with standard specifications, and suffering from acute deficiency, causing distress and financial harm to my client.

3. That despite repeated requests, communications, and customer service grievances, you have refused and neglected to provide a replacement or legitimate refund of {amount}.

4. You are hereby called upon to refund the complete sum of {amount} along with interest @ 18% p.a. and Rs. 50,000/- towards mental agony and litigation expenses within 15 DAYS of receipt of this notice, failing which a formal Consumer Complaint will be instituted before the competent District Consumer Commission under Section 35 of the Consumer Protection Act, 2019.

Yours faithfully,

ADVOCATE FOR THE CONSUMER
"""
            notice_type = "consumer_legal_notice"

        # D. General Civil Recovery Notice
        else:
            title = f"FORMAL LEGAL DEMAND NOTICE FOR RECOVERY OF {amount} AND DAMAGES"
            body = f"""REGISTERED LEGAL DEMAND NOTICE

Date: {today_str}
Place: {city}

TO,
{opponent_name}
[Address of the Noticee]

SUB: FORMAL PRE-LITIGATION DEMAND NOTICE FOR RECOVERY OF {amount}

Sir / Madam,

Under instructions from my client, {citizen_name}, residing at {city}, I serve upon you this Legal Notice:

1. That you entered into transactions and commitments with my client concerning dispute of {amount} on or around {dates}.

2. That you have breached the agreed terms and failed to perform your legal obligations, causing severe wrongful loss and mental distress to my client.

3. {"Contemporaneous electronic records and communications have been documented and preserved under Section 63 of Bharatiya Sakshya Adhiniyam, 2023." if has_video else "All documentation and transaction proofs have been compiled for judicial proceedings."}

4. You are hereby called upon to clear the outstanding sum of {amount} within 15 DAYS of receipt of this notice, failing which formal civil and criminal proceedings shall be instituted against you without further intimation.

Yours faithfully,

ADVOCATE FOR THE CLIENT
"""
            notice_type = "civil_demand_notice"

        return {
            "title": title,
            "notice_type": notice_type,
            "content": body,
            "statutory_period": "15 Days Statutory Window",
            "jurisdiction": city,
            "incorporated_facts": incorporated_facts,
            "last_updated": datetime.now().strftime("%I:%M %p"),
            "evidence_flags": {"video": has_video, "stamp": has_stamp, "cash": has_cash}
        }

    @classmethod
    def _extract_title(cls, text: str, category: str) -> str:
        for line in text.split("\n")[:10]:
            clean = line.strip().replace("*", "").replace("#", "")
            if clean.startswith("SUB:") or clean.startswith("Subject:"):
                return clean.replace("SUB:", "").replace("Subject:", "").strip()
            if "LEGAL NOTICE" in clean.upper() or "DEMAND NOTICE" in clean.upper():
                return clean.strip()
        return f"PRE-LITIGATION LEGAL DEMAND NOTICE — {category.replace('_', ' ').upper()}"
