from typing import Dict, Any

class UrgencyTriage:
    """
    Evaluates citizen queries for emergency legal scenarios and routes to
    national statutory helplines (NALSA, DLSA, Police 112, Women Helpline 1091, Cyber 1930).
    """

    # Matching is a plain substring test, so these have to cover how people
    # actually write. "threat to life" alone never fired on "threatened to kill
    # me", which is the far more common phrasing.
    EMERGENCY_KEYWORDS = [
        "arrest", "police custody", "police beating", "illegal detention", "threat to life",
        "suicide", "physical abuse", "domestic violence", "marpeet", "hathapai", "gun",
        "kidnap", "extortion", "dowry harassment", "fir filed", "chhaapa", "raid",
        # life-threat phrasings
        "threaten to kill", "threatened to kill", "threatening to kill", "kill me",
        "kill us", "jaan se mar", "jaan se khatra", "attempt to murder", "murder me",
        # violence and abuse
        "beat me", "beating me", "beaten me", "assault", "acid attack", "molest",
        "rape", "sexual harassment", "harassing me physically", "burn me",
        # self-harm
        "end my life", "self harm", "harm myself", "khudkushi",
    ]
    
    URGENT_KEYWORDS = [
        "notice expiring", "limitation period", "today is last date", "court tomorrow",
        "warrant", "summons", "account freeze", "cheque bounce 30 days", "eviction today"
    ]

    FREE_LEGAL_AID_HELPLINES = [
        {
            "name": "NALSA Free Legal Aid Toll-Free Helpline",
            "number": "15100",
            "scope": "24x7 Free legal assistance by legal services authorities under Legal Services Authorities Act, 1987",
            "eligible": "Women, children, SC/ST, custody persons, and citizens below state income thresholds"
        },
        {
            "name": "National Emergency Response Support System (ERSS)",
            "number": "112",
            "scope": "Immediate police, fire, and ambulance intervention across India",
            "eligible": "Any citizen facing immediate physical danger"
        },
        {
            "name": "National Women Helpline",
            "number": "1091 / 181",
            "scope": "24x7 emergency response for women facing domestic violence or harassment",
            "eligible": "Any woman in distress"
        },
        {
            "name": "National Cyber Crime Reporting Helpline",
            "number": "1930",
            "scope": "Immediate financial freeze in cyber banking frauds and UPI scams",
            "eligible": "Victims of financial online fraud within golden hours"
        },
        {
            "name": "Tele-Law Service (Govt. of India)",
            "number": "14430",
            "scope": "Free pre-litigation legal advice connecting citizens with Panel Lawyers",
            "eligible": "All citizens through Common Service Centres (CSC)"
        }
    ]

    @classmethod
    def evaluate(cls, user_text: str) -> Dict[str, Any]:
        lowered = user_text.lower()
        
        # Check emergency
        for kw in cls.EMERGENCY_KEYWORDS:
            if kw in lowered:
                return {
                    "urgency": "emergency",
                    "reason": f"Detected immediate safety or criminal custody keyword: '{kw}'",
                    "requires_escalation": True,
                    "helplines": cls.FREE_LEGAL_AID_HELPLINES
                }
                
        # Check urgent
        for kw in cls.URGENT_KEYWORDS:
            if kw in lowered:
                return {
                    "urgency": "urgent",
                    "reason": f"Detected time-sensitive procedural legal window: '{kw}'",
                    "requires_escalation": False,
                    "helplines": [cls.FREE_LEGAL_AID_HELPLINES[0], cls.FREE_LEGAL_AID_HELPLINES[4]]
                }
                
        return {
            "urgency": "routine",
            "reason": "Standard legal advisory query",
            "requires_escalation": False,
            "helplines": []
        }
