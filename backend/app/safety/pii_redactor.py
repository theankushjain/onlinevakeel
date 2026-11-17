import re
from typing import Dict, Tuple

class PIIRedactor:
    """
    DPDP-compliant PII Redaction Engine.
    Masks Indian personal identifiers before prompt ingestion by external or hosted LLMs.
    """
    
    # Common Indian PII Regex Patterns
    AADHAAR_PATTERN = re.compile(r'\b[1-9]{1}[0-9]{3}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b')
    PAN_PATTERN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE)
    PHONE_PATTERN = re.compile(r'(\+91[\-\s]?)?[6789]\d{9}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    BANK_ACC_PATTERN = re.compile(r'\b\d{9,18}\b')  # Generic 9-18 digit account numbers
    
    @classmethod
    def redact(cls, text: str) -> Tuple[str, Dict[str, list]]:
        """
        Redacts sensitive tokens and returns the cleaned text along with redacted metadata.
        """
        redactions = {
            "aadhaar": [],
            "pan": [],
            "phone": [],
            "email": []
        }
        
        cleaned = text
        
        # 1. Aadhaar Masking
        for match in cls.AADHAAR_PATTERN.finditer(cleaned):
            redactions["aadhaar"].append(match.group())
        cleaned = cls.AADHAAR_PATTERN.sub("[AADHAAR_REDACTED]", cleaned)
        
        # 2. PAN Card Masking
        for match in cls.PAN_PATTERN.finditer(cleaned):
            redactions["pan"].append(match.group())
        cleaned = cls.PAN_PATTERN.sub("[PAN_REDACTED]", cleaned)
        
        # 3. Email Masking
        for match in cls.EMAIL_PATTERN.finditer(cleaned):
            redactions["email"].append(match.group())
        cleaned = cls.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", cleaned)
        
        # 4. Indian Phone Masking
        for match in cls.PHONE_PATTERN.finditer(cleaned):
            redactions["phone"].append(match.group())
        cleaned = cls.PHONE_PATTERN.sub("[PHONE_REDACTED]", cleaned)
        
        return cleaned, redactions

    @classmethod
    def is_pii_present(cls, text: str) -> bool:
        _, redactions = cls.redact(text)
        return any(len(v) > 0 for v in redactions.values())
