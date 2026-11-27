import re
from typing import Dict, Any, List, Optional
from app.data.indian_districts import INDIAN_DISTRICTS_CATALOG

class IntakeAgent:
    """
    Intake Agent: Gathers structured case facts, dates, monetary stakes,
    and territorial jurisdiction across all 754 Indian judicial districts
    without providing premature legal conclusions.
    """

    CATEGORIES = {
        "cheque_bounce": ["cheque", "check", "bounce", "dishonour", "memo", "funds insufficient", "sign mismatch", "bounced"],
        "consumer_dispute": ["consumer", "defective", "refund", "warranty", "flipkart", "amazon", "service deficiency", "damaged product", "seller"],
        "property_rera": ["rera", "builder", "flat", "possession", "apartment", "society", "allottee", "registry", "delay in possession"],
        "cyber_fraud": ["cyber", "otp", "phishing", "scam", "upi", "hacked", "fraud transaction", "credit card fraud"],
        "employment_labour": ["salary unpaid", "terminated", "pf", "gratuity", "employer", "workplace", "severance"],
        "criminal_bail": ["bail", "police", "fir", "arrest", "custody", "warrant", "bns"],
        "rti_public": ["rti", "right to information", "government tender", "public authority", "sarkari"]
    }

    # Pre-index all 754 districts and court aliases
    _DISTRICT_MAP: Dict[str, Dict[str, Any]] = {}
    _SUBCOURT_MAP: Dict[str, Dict[str, Any]] = {}

    COMMON_ALIASES = {
        # Delhi NCR & Suburbs
        "noida": {"district": "Gautam Buddha Nagar", "city": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "court": "District & Sessions Court Surajpur (Greater Noida)", "locality": "Noida"},
        "greater noida": {"district": "Gautam Buddha Nagar", "city": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "court": "District & Sessions Court Surajpur (Greater Noida)", "locality": "Greater Noida"},
        "surajpur": {"district": "Gautam Buddha Nagar", "city": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "court": "District & Sessions Court Surajpur (Greater Noida)", "locality": "Surajpur"},
        "gurgaon": {"district": "Gurugram", "city": "Gurugram", "state": "Haryana", "court": "District Courts Complex Gurugram", "locality": "Gurgaon"},
        "gurugram": {"district": "Gurugram", "city": "Gurugram", "state": "Haryana", "court": "District Courts Complex Gurugram", "locality": "Gurugram"},
        "ghaziabad": {"district": "Ghaziabad", "city": "Ghaziabad", "state": "Uttar Pradesh", "court": "District & Sessions Court Ghaziabad", "locality": "Ghaziabad"},
        "faridabad": {"district": "Faridabad", "city": "Faridabad", "state": "Haryana", "court": "District & Sessions Court Faridabad", "locality": "Faridabad"},
        "delhi": {"district": "New Delhi", "city": "New Delhi", "state": "Delhi", "court": "Patiala House Court Complex", "locality": "New Delhi"},
        "new delhi": {"district": "New Delhi", "city": "New Delhi", "state": "Delhi", "court": "Patiala House Court Complex", "locality": "New Delhi"},
        "delhi ncr": {"district": "New Delhi", "city": "New Delhi", "state": "Delhi", "court": "Tis Hazari & Saket Courts", "locality": "Delhi NCR"},
        "saket": {"district": "South Delhi", "city": "New Delhi", "state": "Delhi", "court": "Saket District Court Complex", "locality": "Saket"},
        "tis hazari": {"district": "North Delhi", "city": "New Delhi", "state": "Delhi", "court": "Tis Hazari Court Complex", "locality": "Tis Hazari"},
        "patiala house": {"district": "New Delhi", "city": "New Delhi", "state": "Delhi", "court": "Patiala House Court Complex", "locality": "Patiala House"},
        "karkardooma": {"district": "East Delhi", "city": "New Delhi", "state": "Delhi", "court": "Karkardooma Court Complex", "locality": "Karkardooma"},
        "rohini": {"district": "North West Delhi", "city": "New Delhi", "state": "Delhi", "court": "Rohini District Court", "locality": "Rohini"},
        "dwarka": {"district": "South West Delhi", "city": "New Delhi", "state": "Delhi", "court": "Dwarka District Court", "locality": "Dwarka"},
        "rouse avenue": {"district": "New Delhi", "city": "New Delhi", "state": "Delhi", "court": "Rouse Avenue Court Complex", "locality": "Rouse Avenue"},

        # Bengaluru & Karnataka
        "bangalore": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Bengaluru"},
        "bengaluru": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Bengaluru"},
        "blr": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Bengaluru"},
        "mayo hall": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Mayo Hall / MG Road"},
        "mayohall": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Mayo Hall / MG Road"},
        "whitefield": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Whitefield"},
        "koramangala": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Koramangala"},
        "indiranagar": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Indiranagar"},
        "electronic city": {"district": "Bengaluru Urban", "city": "Bengaluru", "state": "Karnataka", "court": "City Civil Court (Mayohall / Mayo Hall)", "locality": "Electronic City"},

        # Mumbai & Maharashtra
        "mumbai": {"district": "Mumbai City", "city": "Mumbai", "state": "Maharashtra", "court": "City Civil & Sessions Court (Fort)", "locality": "Mumbai"},
        "bombay": {"district": "Mumbai City", "city": "Mumbai", "state": "Maharashtra", "court": "City Civil & Sessions Court (Fort)", "locality": "Mumbai"},
        "bandra": {"district": "Mumbai Suburban", "city": "Mumbai", "state": "Maharashtra", "court": "Bandra Metropolitan Magistrate Court", "locality": "Bandra"},
        "borivali": {"district": "Mumbai Suburban", "city": "Mumbai", "state": "Maharashtra", "court": "Borivali Court", "locality": "Borivali"},
        "andheri": {"district": "Mumbai Suburban", "city": "Mumbai", "state": "Maharashtra", "court": "Andheri Court", "locality": "Andheri"},
        "esplanade": {"district": "Mumbai City", "city": "Mumbai", "state": "Maharashtra", "court": "Esplanade Metropolitan Court", "locality": "Fort / Esplanade"},
        "thane": {"district": "Thane", "city": "Thane", "state": "Maharashtra", "court": "District & Sessions Court Thane", "locality": "Thane"},
        "vashi": {"district": "Thane", "city": "Thane", "state": "Maharashtra", "court": "Belapur Court (Navi Mumbai)", "locality": "Vashi"},
        "navi mumbai": {"district": "Thane", "city": "Thane", "state": "Maharashtra", "court": "Belapur Court (Navi Mumbai)", "locality": "Navi Mumbai"},
        "pune": {"district": "Pune", "city": "Pune", "state": "Maharashtra", "court": "Pune District & Sessions Court (Shivajinagar)", "locality": "Pune"},
        "shivajinagar": {"district": "Pune", "city": "Pune", "state": "Maharashtra", "court": "Pune District & Sessions Court (Shivajinagar)", "locality": "Shivajinagar"},
        "hinjewadi": {"district": "Pune", "city": "Pune", "state": "Maharashtra", "court": "Pune District & Sessions Court (Shivajinagar)", "locality": "Hinjewadi"},

        # Hyderabad & Telangana
        "hyderabad": {"district": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "court": "City Civil Court Hyderabad (Purani Haveli)", "locality": "Hyderabad"},
        "hyd": {"district": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "court": "City Civil Court Hyderabad (Purani Haveli)", "locality": "Hyderabad"},
        "secunderabad": {"district": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "court": "City Civil Court Hyderabad (Purani Haveli)", "locality": "Secunderabad"},
        "cyberabad": {"district": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "court": "Cyberabad District & Sessions Court", "locality": "Gachibowli / Madhapur"},
        "hitech city": {"district": "Hyderabad", "city": "Hyderabad", "state": "Telangana", "court": "City Civil Court Hyderabad", "locality": "Hitech City"},

        # Chennai, Kolkata, Lucknow, Jaipur, Chandigarh
        "chennai": {"district": "Chennai", "city": "Chennai", "state": "Tamil Nadu", "court": "City Civil Court Chennai", "locality": "Chennai"},
        "madras": {"district": "Chennai", "city": "Chennai", "state": "Tamil Nadu", "court": "City Civil Court Chennai", "locality": "Chennai"},
        "kolkata": {"district": "Kolkata", "city": "Kolkata", "state": "West Bengal", "court": "City Civil Court Calcutta / Alipore Court", "locality": "Kolkata"},
        "calcutta": {"district": "Kolkata", "city": "Kolkata", "state": "West Bengal", "court": "City Civil Court Calcutta / Alipore Court", "locality": "Kolkata"},
        "lucknow": {"district": "Lucknow", "city": "Lucknow", "state": "Uttar Pradesh", "court": "District & Sessions Court Lucknow (Qaiserbagh)", "locality": "Lucknow"},
        "qaiserbagh": {"district": "Lucknow", "city": "Lucknow", "state": "Uttar Pradesh", "court": "District & Sessions Court Lucknow (Qaiserbagh)", "locality": "Qaiserbagh"},
        "jaipur": {"district": "Jaipur", "city": "Jaipur", "state": "Rajasthan", "court": "District & Sessions Court Jaipur (Collectorate Circle)", "locality": "Jaipur"},
        "chandigarh": {"district": "Chandigarh", "city": "Chandigarh", "state": "Chandigarh", "court": "District Courts Complex Sector 43 Chandigarh", "locality": "Chandigarh"},
        "prayagraj": {"district": "Prayagraj", "city": "Prayagraj", "state": "Uttar Pradesh", "court": "District & Sessions Court Prayagraj", "locality": "Prayagraj"},
        "allahabad": {"district": "Prayagraj", "city": "Prayagraj", "state": "Uttar Pradesh", "court": "District & Sessions Court Prayagraj", "locality": "Allahabad"},
        "varanasi": {"district": "Varanasi", "city": "Varanasi", "state": "Uttar Pradesh", "court": "District & Sessions Court Varanasi", "locality": "Varanasi"},
        "kashi": {"district": "Varanasi", "city": "Varanasi", "state": "Uttar Pradesh", "court": "District & Sessions Court Varanasi", "locality": "Kashi"},
        "banaras": {"district": "Varanasi", "city": "Varanasi", "state": "Uttar Pradesh", "court": "District & Sessions Court Varanasi", "locality": "Banaras"}
    }

    @classmethod
    def _init_lookups(cls):
        if not cls._DISTRICT_MAP:
            for item in INDIAN_DISTRICTS_CATALOG:
                d_key = item["district"].strip().lower()
                cls._DISTRICT_MAP[d_key] = item
                # Also index sub-courts
                for sc in item.get("sub_courts", []):
                    cls._SUBCOURT_MAP[sc.strip().lower()] = item

    @classmethod
    def classify_category(cls, text: str) -> str:
        text_lower = text.lower()
        # Prevent neighbour/noise/nuisance disputes from being misclassified as cyber_fraud
        # just because the user mentions a fictional or incidental "cyber" statute name.
        nuisance_terms = ("loud music", "noise", "neighbor", "neighbour", "nuisance")
        financial_cyber_terms = ("otp", "upi", "phishing", "scam", "hacked", "fraud transaction", "credit card fraud", "money deducted", "bank")
        if any(nt in text_lower for nt in nuisance_terms) and not any(ft in text_lower for ft in financial_cyber_terms):
            return "general_civil"

        for cat, keywords in cls.CATEGORIES.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return "general_civil"

    @classmethod
    def extract_facts(cls, text: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Extracts monetary figures, dates, and locations across all 754 Indian districts.
        Also scans history if the current query is an elaboration or short answer.
        """
        cls._init_lookups()

        facts: Dict[str, Any] = {
            "monetary_amount": None,
            "dates_mentioned": [],
            "locations_mentioned": [],
            "identified_parties": [],
            "district_courts_mentioned": [],
            "localities_mentioned": [],
            "detected_district": None,
            "detected_state": None,
            "detected_court": None,
        }
        
        # 1. Money detection (Rs. 50,000 / 1 Lakh / 25000)
        money_match = re.search(r'(?:rs\.?|inr|rupees|\₹)\s*([\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore|k))?)', text, re.IGNORECASE)
        if money_match:
            facts["monetary_amount"] = money_match.group(0).strip()
            
        # 2. Date detection
        date_matches = re.findall(r'\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4})\b', text, re.IGNORECASE)
        facts["dates_mentioned"] = date_matches

        # Helper to match location against text
        def find_location_in_string(s: str) -> bool:
            s_clean = s.strip()
            s_lower = s_clean.lower()

            # Pattern A: Direct conversational extraction (e.g. "I am in Noida", "I live in Gautam Buddha Nagar", "located in Pune")
            patterns = [
                r'(?:i am in|i live in|located in|living in|based in|residing in|staying in|from|at|near)\s+([A-Za-z\s]+?)(?:[,\.\?!]|\band\b|\bwith\b|\bmy\b|$)',
                r'\b(?:city|district|court)\s+(?:is|of)?\s*([A-Za-z\s]+?)(?:[,\.\?!]|$)'
            ]
            for pat in patterns:
                m = re.search(pat, s_lower, re.IGNORECASE)
                if m:
                    candidate = m.group(1).strip()
                    # Clean trailing noise words
                    candidate = re.sub(r'\b(?:city|district|court|state|area|only|please|now)\b', '', candidate).strip()
                    if candidate in cls.COMMON_ALIASES:
                        al = cls.COMMON_ALIASES[candidate]
                        _apply_location(al["city"], al["district"], al["state"], al["court"], al.get("locality"))
                        return True
                    if candidate in cls._DISTRICT_MAP:
                        d_item = cls._DISTRICT_MAP[candidate]
                        _apply_location(d_item["district"], d_item["district"], d_item["state"], d_item["district_court"])
                        return True

            # Pattern B: Check Common Aliases in full text
            for alias, data in cls.COMMON_ALIASES.items():
                if re.search(r'\b' + re.escape(alias) + r'\b', s_lower):
                    _apply_location(data["city"], data["district"], data["state"], data["court"], data.get("locality"))
                    return True

            # Pattern C: Check all 754 Districts from catalog
            for d_name, d_item in cls._DISTRICT_MAP.items():
                if re.search(r'\b' + re.escape(d_name) + r'\b', s_lower):
                    _apply_location(d_item["district"], d_item["district"], d_item["state"], d_item["district_court"])
                    return True

            # Pattern D: Check sub-courts
            for sc_name, d_item in cls._SUBCOURT_MAP.items():
                if re.search(r'\b' + re.escape(sc_name) + r'\b', s_lower):
                    _apply_location(d_item["district"], d_item["district"], d_item["state"], d_item["district_court"])
                    return True

            # Pattern E: Short answer check (e.g. user just entered "Noida" or "Gautam Buddha Nagar")
            words = s_lower.strip().split()
            if len(words) <= 4:
                clean_short = " ".join(words)
                clean_short = re.sub(r'^(?:i am in|i live in|in|at|from)\s+', '', clean_short).strip()
                if clean_short in cls.COMMON_ALIASES:
                    al = cls.COMMON_ALIASES[clean_short]
                    _apply_location(al["city"], al["district"], al["state"], al["court"], al.get("locality"))
                    return True
                if clean_short in cls._DISTRICT_MAP:
                    d_item = cls._DISTRICT_MAP[clean_short]
                    _apply_location(d_item["district"], d_item["district"], d_item["state"], d_item["district_court"])
                    return True

            return False

        def _apply_location(city: str, district: str, state: str, court: str, locality: Optional[str] = None):
            if city not in facts["locations_mentioned"]:
                facts["locations_mentioned"].append(city)
            if district and district not in facts["locations_mentioned"]:
                facts["locations_mentioned"].append(district)
            facts["detected_district"] = district
            facts["detected_state"] = state
            facts["detected_court"] = court
            if court and court not in facts["district_courts_mentioned"]:
                facts["district_courts_mentioned"].append(court)
            if locality and locality not in facts["localities_mentioned"]:
                facts["localities_mentioned"].append(locality)

        # First scan the current message
        found = find_location_in_string(text)

        # If not found in current message, scan previous user messages in history
        if not found and history:
            for msg in reversed(history):
                sender = msg.get("sender") or msg.get("role") or ""
                if sender in ["user", "citizen"]:
                    if find_location_in_string(msg.get("text", "")):
                        break

        return facts

    @classmethod
    def analyze(cls, text: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        category = cls.classify_category(text)
        facts = cls.extract_facts(text, history=history)
        
        missing_fields = []
        if not facts["monetary_amount"] and category in ["cheque_bounce", "consumer_dispute", "cyber_fraud"]:
            missing_fields.append("amount in dispute")
        if not facts["dates_mentioned"] and category in ["cheque_bounce", "property_rera"]:
            missing_fields.append("incident/memo date")
        if not facts["locations_mentioned"]:
            missing_fields.append("city / state of dispute")

        return {
            "category": category,
            "facts": facts,
            "missing_fields": missing_fields,
            "intake_complete": len(missing_fields) == 0
        }

