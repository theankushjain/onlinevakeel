import logging
import os
import re
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
                if (language or "en").startswith("hi"):
                    ans += (
                        "\n\n---\n"
                        "📍 **आपका शहर व ज़िला न्यायालय?**\n"
                        "आपके नज़दीकी **ज़िला न्यायालय (District Court)** और चैंबर के वकीलों से आपको सीधे जोड़ने के लिए, कृपया बताएं कि **आप किस शहर, इलाके या ज़िला अदालत के पास स्थित हैं?**"
                    )
                else:
                    ans += (
                        "\n\n---\n"
                        "📍 **Which city or district court are you in?**\n"
                        "To recommend verified advocates practicing in your exact city, locality, and District Court (e.g., *Tis Hazari, Saket, Bandra, Mayo Hall, Pune, etc.*), could you please mention **which city and locality/court** you are located in?"
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
            
            if loc_summary and "verified advocates practicing in" not in ans.lower() and "location matched" not in ans.lower():
                ans += (
                    f"\n\n---\n"
                    f"🎯 **Location Matched**: Verified advocates practicing in **{loc_summary}** have been automatically prioritized in your Recommended Advocates list."
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
        models_to_try = [
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3-flash-preview"
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
     '*(To suggest verified advocates who practice before your exact local District Court or High Court, could you also tell me which city or district you are located in?)*'"""

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
                "maxOutputTokens": 1024,
                "thinkingConfig": {"thinkingBudget": 256}
            }
        }

        # Fallback payload without thinking config for models that don't support thinkingConfig
        payload_standard = {
            "contents": payload_with_budget["contents"],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            for payload in [payload_with_budget, payload_standard]:
                try:
                    with httpx.Client(timeout=6.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
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
            "Rely strictly on verified statutory provisions and established Indian legal remedies. Do not invent sections or laws."
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
            f"Provide a reassuring, empathetic explanation of their rights, the applicable Act/sections, and a clear 3-step practical action plan."
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
                        "max_tokens": 400,
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
        amount = facts.get("monetary_amount") or "your disputed amount"
        city = (facts.get("locations_mentioned") or ["your city"])[0]
        q_lower = (user_query or "").lower()

        # ─── SPECIFIC FOLLOW-UP QUESTIONS ROUTING ────────────────────────────
        is_follow_up = bool(history and len(history) > 1) or len(user_query.split()) < 15

        # 1. Secret Video / Audio Recording / Electronic Evidence Follow-up
        if any(w in q_lower for w in ["video", "record", "recording", "audio", "sting", "camera", "phone call", "call record", "whatsapp audio", "taped"]):
            return (
                f"### Yes, your secret video recording is legally admissible in an Indian court, and it is a massive asset for your case.\n\n"
                f"Under established Indian law, secretly recorded videos or audios **CAN be submitted as valid evidence** to prove fraud and cheating. "
                f"The Supreme Court of India (*R.M. Malkani v. State of Maharashtra* and *K.S. Puttaswamy*) has clearly ruled that the test in Indian evidence law is **relevance** — "
                f"even if evidence is recorded without the other party's consent or knowledge, that alone does **not** make it inadmissible.\n\n"
                f"Here is how this applies specifically to your dispute involving **{amount}** in **{city}**:\n\n"
                f"#### 1. Why this recording is devastating proof against the accused:\n"
                f"- **Proves Receipt of Cash**: If the video captures the relative taking the money or discussing the transaction, it completely demolishes any lie that 'I never received cash from them'.\n"
                f"- **Proves Criminal Cheating (*Mens Rea*)**: Under **Section 318 of Bharatiya Nyaya Sanhita, 2023 (BNS)** (replacing Section 420 IPC), selling a plot knowing you do not own it is a cognizable criminal offence punishable by up to 7 years in prison. The video proves their fraudulent inducement from day one.\n\n"
                f"#### 2. The Mandatory Legal Requirement: Section 63 BSA Certificate\n"
                f"- Under the new **Bharatiya Sakshya Adhiniyam, 2023 (BSA)** — specifically **Section 63** (which replaced the old Section 65B of the Indian Evidence Act) — electronic records must be accompanied by an **Electronic Evidence Certificate**.\n"
                f"- You (or the person who owns the recording device) must sign a certificate affirming:\n"
                f"  * The device (phone/camera) was in your regular lawful control.\n"
                f"  * The video is original, unedited, and free from tampering or morphing.\n\n"
                f"#### 3. Critical Precautions you must take immediately:\n"
                f"- ⚠️ **Never edit, trim, or compress the video**: Do NOT forward it via WhatsApp to yourself, as WhatsApp compresses the file and strips the original EXIF metadata (timestamp, device hash, location).\n"
                f"- **Preserve the Original Phone / Memory Card**: Keep the original device or SD card intact in a safe tamper-evident cover. Courts may send it to the State Forensic Science Laboratory (FSL) to verify authenticity.\n"
                f"- **Make a Bit-Stream Backup**: Copy the raw video file onto an external pen drive and keep multiple physical backups.\n\n"
                f"👉 **Next Step**: When you hand off this case to our advocate, share the raw file. The advocate will draft the **Section 63 BSA Certificate** and attach the video transcript to the formal Legal Notice and Police Complaint."
            )

        # 2. Stamp Paper / Notary / Unregistered Agreement Follow-up
        if any(w in q_lower for w in ["stamp paper", "100 rs", "100 rupee", "notary", "notarized", "unregistered", "agreement"]):
            return (
                f"### Let's clarify the legal standing of your ₹100 stamp paper agreement:\n\n"
                f"Under the **Registration Act, 1908 (Section 17 & 49)** and the **Transfer of Property Act, 1882**, immovable property worth more than ₹100 can only transfer ownership through a registered sale deed. "
                f"An unnotarized ₹100 stamp paper does not transfer title to you — but **it is still extremely valuable in court**:\n\n"
                f"#### 1. Valid as 'Collateral Evidence' of Payment and Terms\n"
                f"- Under the **Proviso to Section 49 of the Registration Act**, an unregistered agreement **can be received as evidence** of contract in court and as collateral proof of money paid ({amount}).\n"
                f"- Your relative cannot claim 'we had no deal' because their signature on that stamp paper is written proof of the transaction.\n\n"
                f"#### 2. Conclusive Proof of Criminal Cheating (Section 318 BNS / 420 IPC)\n"
                f"- In a criminal complaint for cheating, the court does not examine whether the deed is registered; the court examines whether the relative **fraudulently induced you to part with {amount}**.\n"
                f"- The stamp paper agreement is concrete proof that they promised you a plot they had no authority or title to sell."
            )

        # 3. Police Inaction / FIR Refusal Follow-up
        if any(w in q_lower for w in ["police", "fir", "thana", "station", "chowki", "refuse", "not registering", "not filing"]):
            return (
                f"### If the local police station is hesitating to register an FIR, here is your statutory remedy:\n\n"
                f"In land and financial fraud involving amounts like **{amount}**, local police stations sometimes try to turn citizens away by calling it a 'civil matter'. "
                f"However, cheating by selling non-existent title is a **cognizable criminal offence**.\n\n"
                f"#### Your 2-Step Remedy under the new criminal procedure:\n"
                f"1. **Step 1: Written Representation to the Superintendent of Police (SP) / DCP**\n"
                f"   - Send your complaint with annexures (stamp paper copy, video transcript, bank withdrawal trail) via Registered Post with Acknowledgment Due to the District SP/DCP.\n\n"
                f"2. **Step 2: Approach the Judicial Magistrate under Section 175(3) of BNSS, 2023**\n"
                f"   - Under **Section 175(3) of the Bharatiya Nagarik Suraksha Sanhita (BNSS)** (replacing the old Section 156(3) CrPC), your advocate can file an application before the local Magistrate.\n"
                f"   - The Magistrate has statutory power to order the police station to register an FIR and submit a formal investigation report within a court-monitored deadline."
            )

        # 4. If opponent ignores legal notice / 15-day expiry
        if any(w in q_lower for w in ["ignore", "not replying", "no reply", "15 days", "expired", "after notice"]):
            return (
                f"### What happens if the other party ignores your 15-day statutory notice:\n\n"
                f"1. **Cause of Action is Crystallized**:\n"
                f"   - The primary objective of the 15-day pre-litigation notice is to put the opponent on formal legal notice. When 15 days lapse without full payment or resolution, your legal 'Cause of Action' is complete.\n\n"
                f"2. **Presumption of Service under Law**:\n"
                f"   - When sent via Registered Speed Post with tracking acknowledgment, **Section 27 of the General Clauses Act** raises a mandatory presumption that the notice was duly served.\n\n"
                f"3. **Immediate Judicial Filing**:\n"
                f"   - Your advocate will file the formal complaint/suit immediately. In court, their silence or failure to reply to your notice is treated as adverse conduct, significantly strengthening your position."
            )

        # 5. General Follow-up Handling (when previous context exists)
        if is_follow_up:
            return (
                f"Regarding your follow-up on your ongoing **{category.replace('_', ' ').title()}** matter concerning **{amount}** in **{city}**:\n\n"
                f"#### Key Procedural Recommendations:\n"
                f"- **Maintain Clean Documentation**: Ensure every document, receipt, witness statement, or electronic recording is organized with exact chronological dates.\n"
                f"- **Statutory Remedy**: Under Indian law, pre-litigation notice followed by filing before the competent judicial forum is the standard course.\n"
                f"- **Advocate Consultation**: We recommend connecting with a verified advocate in **{city}** using the advocate card on the right to review your evidence and file necessary applications without delay."
            )

        # Emergency check
        emergency_prefix = ""
        if triage.get("urgency") == "emergency":
            emergency_prefix = (
                "🚨 **Important Safety Notice**: It appears you or someone involved may be facing immediate physical danger or police action. "
                "Please do not wait — call **112 (Emergency Police)** or **15100 (NALSA Free Legal Aid)** immediately. Your safety comes first.\n\n---\n\n"
            )

        if category == "cheque_bounce":
            return emergency_prefix + (
                f"### I completely understand your frustration.\n\n"
                f"Having a cheque of **{amount}** bounce is stressful, especially when you provided goods, services, or loans in good faith. "
                f"The good news is that **Indian law treats cheque dishonour very strictly** under **Section 138 of the Negotiable Instruments Act**.\n\n"
                f"#### Here is what the law says in simple terms:\n"
                f"- A bounced cheque is not just a civil breach — it is a **criminal offence** in India.\n"
                f"- If the drawer doesn't pay up, they risk facing **up to 2 years in prison**, a fine of up to **twice the cheque amount ({amount})**, or both.\n\n"
                f"#### Your Immediate 3-Step Action Plan:\n"
                f"1. **Do not delay (Statutory 30-Day Window)**: You must send a formal legal demand notice within **30 days** from the date your bank gave you the return memo.\n"
                f"2. **Give them 15 Days to Pay**: Under the law, the other party has **15 days** from receiving your notice to clear the money.\n"
                f"3. **File in Court if Unpaid**: If they fail to pay within those 15 days, your cause of action arises, and your lawyer can immediately file a criminal complaint before the Judicial Magistrate.\n\n"
                f"👉 **Good news**: I have already drafted your official **Section 138 Demand Notice** on the right side of your screen. "
                f"You can copy it, review the terms, and connect with a verified advocate in **{city}** to issue it via Registered Speed Post."
            )

        elif category == "property_rera":
            return emergency_prefix + (
                f"### You are in a strong legal position, and you have clear rights.\n\n"
                f"Buying a home is one of life's biggest milestones. When a builder takes **{amount}** and delays handing over your flat by months or years, "
                f"it causes tremendous financial and emotional strain.\n\n"
                f"Under the **RERA Act (Section 18)**, builders can no longer delay projects with impunity or make false promises.\n\n"
                f"#### You have two powerful legal choices right now:\n"
                f"1. **Option 1: Walk away with a 100% Full Refund + Interest**\n"
                f"   - If you no longer trust the developer, you have the statutory right to withdraw from the project.\n"
                f"   - The builder must return your entire **{amount}** with prescribed state RERA interest (typically State Bank MCLR + 2%, which is around 10–11% per annum) from the day you paid them.\n\n"
                f"2. **Option 2: Keep the Flat & Get Monthly Delay Compensation**\n"
                f"   - If you still love the property and want the flat, you can stay in the project and legally demand **monthly interest for every single month of delay** until the day they deliver the Occupancy Certificate.\n\n"
                f"#### What you should do next:\n"
                f"- We have already formatted a formal **Section 18 RERA Demand Notice** on the right side of this screen.\n"
                f"- Issue this notice giving the builder 15 days to respond.\n"
                f"- If they do not resolve it, your advocate can file a formal complaint online before the **State RERA Authority** to order immediate payment."
            )

        elif category == "consumer_dispute":
            return emergency_prefix + (
                f"### You do not have to accept poor service or broken promises.\n\n"
                f"Whether it is an e-commerce platform, a car dealership, or an electronics brand refusing to replace a defective product or honor a refund of **{amount}**, "
                f"the **Consumer Protection Act, 2019 (Section 35)** protects you directly against 'deficiency in service' and 'unfair trade practices'.\n\n"
                f"#### How the Consumer Commission helps you:\n"
                f"- You are legally entitled to a **full refund of {amount}** or a brand-new replacement.\n"
                f"- In addition, consumer forums routinely award **compensation for mental agony and litigation costs** against errant companies.\n"
                f"- You have **2 full years** from the date the problem occurred to seek justice.\n\n"
                f"#### Recommended Next Steps:\n"
                f"1. **Serve a Pre-Litigation Legal Notice**: Most companies settle as soon as they receive a formal notice from an advocate (check the draft notice on the right).\n"
                f"2. **File Online via e-Daakhil**: If they ignore the notice, we can help you file a complaint directly on the Government of India's **e-Daakhil consumer portal** without heavy court fees."
            )

        elif category == "cyber_fraud":
            return emergency_prefix + (
                f"### Act quickly — time is of the essence in online fraud.\n\n"
                f"Losing **{amount}** to a cyber scam, fake UPI request, or phishing link is harrowing. Here is what you must do immediately:\n\n"
                f"1. **Call 1930 Right Now (The Golden Hour)**: Dial the National Cyber Crime Helpline at **1930**. If reported within the first few hours, banks can freeze the scammer's beneficiary account and stop the money from being withdrawn.\n"
                f"2. **Register Official Complaint**: File a complaint on **cybercrime.gov.in** and save the acknowledgment number.\n"
                f"3. **Under Section 318 of Bharatiya Nyaya Sanhita (BNS 2023)**, financial cyber cheating carries up to **7 years imprisonment**.\n\n"
                f"Save all screenshots, transaction UTR numbers, and call logs as formal evidence."
            )

        elif category == "rti_public":
            return emergency_prefix + (
                f"### As an Indian citizen, you have the absolute legal right to know.\n\n"
                f"Under **Section 6(1) of the Right to Information (RTI) Act, 2005**, any government department, municipal corporation, or public authority is legally obligated to provide you official copies of records, file notings, and progress reports.\n\n"
                f"#### Important Rules you should know:\n"
                f"- **Fee is only Rs. 10**: You can pay via Indian Postal Order or online.\n"
                f"- **30-Day Strict Deadline**: The Public Information Officer (PIO) has exactly **30 days** to reply.\n"
                f"- **Heavy Penalty on Officers**: If they delay or provide false information, the Information Commission can penalize the officer **Rs. 250 per day** up to Rs. 25,000.\n\n"
                f"I have already prepared your formatted **RTI Application Form 'A'** on the right side of your screen."
            )

        else:
            return emergency_prefix + (
                f"### I am here to guide you through this step by step.\n\n"
                f"Legal issues can often feel confusing and overwhelming, but Indian law provides clear procedural remedies for your situation. "
                f"We have examined your facts concerning **{amount}** in **{city}**.\n\n"
                f"#### What you should know:\n"
                f"- Every legal remedy begins with establishing a clean, written paper trail.\n"
                f"- Serving a formal pre-litigation Legal Notice is the customary first step before approaching any court or tribunal.\n"
                f"- Please review the verified statutory provisions and the draft notice prepared on the right side of this screen."
            )
