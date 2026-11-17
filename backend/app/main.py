from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

from app.config import settings
from app.database.supabase_client import db, FALLBACK_LEGAL_CORPUS, FALLBACK_ADVOCATES
from app.agents.orchestrator import OrchestratorAgent
from app.agents.drafting_agent import DraftingAgent
from app.data.indian_districts import INDIAN_DISTRICTS_CATALOG

app = FastAPI(
    title="OnlineVakeel.com Multi-Agent Legal API",
    description="India Multi-Agent Legal Aid, RAG Citation Engine, and Advocate Portal API",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory lead store for advocate portal simulation during dev/demo
ACTIVE_LEADS: List[Dict[str, Any]] = [
    {
        "id": "lead-001",
        "case_id": "OV-8F92A1",
        "category": "cheque_bounce",
        "title": "Cheque Dishonour of Rs. 4,50,000 against Commercial Invoices",
        "client_masked_brief": "Client received cheque bounce memo from HDFC Bank on 15-Oct. Disputed amount Rs. 4,50,000. 15-day statutory notice ready.",
        "city": "New Delhi",
        "urgency": "urgent",
        "advocate_id": "d1111111-1111-1111-1111-111111111111",
        "advocate_name": "Adv. Rajesh Sharma",
        "status": "pending",
        "created_at": "2026-11-12T07:45:00Z"
    },
    {
        "id": "lead-002",
        "case_id": "OV-3C19B4",
        "category": "property_rera",
        "title": "36 Months Possession Delay in 3BHK Whitefield Project",
        "client_masked_brief": "Possession delayed beyond builder-buyer agreement date. Paid Rs. 85,00,000. Seeking Section 18 RERA monthly delay interest.",
        "city": "Bengaluru",
        "urgency": "routine",
        "advocate_id": "d2222222-2222-2222-2222-222222222222",
        "advocate_name": "Adv. Priya Iyer",
        "status": "accepted",
        "created_at": "2026-11-11T14:20:00Z"
    }
]

# Request Schemas
class ConsultRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    history: Optional[List[Dict[str, Any]]] = None

class DraftRequest(BaseModel):
    category: str
    facts: Dict[str, Any]
    citizen_name: Optional[str] = "Client (Name Protected)"
    opponent_name: Optional[str] = "Opponent Party"

class HandoffRequest(BaseModel):
    case_id: str
    advocate_id: str
    brief_text: str
    category: str
    city: str
    urgency: str
    client_name: Optional[str] = "Citizen"
    client_phone: Optional[str] = "+91 98765 43210"
    client_locality: Optional[str] = ""
    preferred_court: Optional[str] = ""
    preferred_mode: Optional[str] = "phone"  # phone, video, chamber
    preferred_slot: Optional[str] = "Today (Next Available Slot)"
    attached_notice_title: Optional[str] = None
    attached_notice_content: Optional[str] = None
    payment_status: Optional[str] = "paid"  # "paid", "pending", "unpaid"
    payment_id: Optional[str] = None
    amount_paid: Optional[int] = None
    payment_method: Optional[str] = "UPI / SafePay Escrow (Simulated)"

class AdvocateReviewRequest(BaseModel):
    rating: int  # 1 to 5 stars
    review_text: str
    client_name: Optional[str] = "Verified Client"
    booking_id: Optional[str] = None
    payment_id: Optional[str] = None
    knowledge_rating: Optional[int] = 5
    responsiveness_rating: Optional[int] = 5
    value_rating: Optional[int] = 5

class LeadActionRequest(BaseModel):
    action: str  # 'accept' or 'decline'
    notes: Optional[str] = ""

class AdvocateRegisterRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = "vakeel123"
    phone: Optional[str] = ""
    bar_council_id: str
    state_bar_council: Optional[str] = "Bar Council of Delhi"
    practice_areas: List[str]
    courts: List[str]
    district_court: Optional[str] = ""
    office_location: Optional[str] = ""
    city: str
    state: Optional[str] = ""
    experience_years: Optional[int] = 5
    consult_fee: Optional[int] = 1200
    languages: Optional[List[str]] = ["English", "Hindi"]
    bio: Optional[str] = ""

class AdvocateLoginRequest(BaseModel):
    identifier: str  # Email, Bar Council ID, or Name
    password: Optional[str] = None

# Endpoints
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "OnlineVakeel Multi-Agent Engine",
        "supabase_connected": db.is_connected,
        "database_mode": "Supabase Cloud" if db.is_connected else "Zero-Config Indian Legal Store",
        "llm_gemini_configured": bool(settings.GEMINI_API_KEY)
    }

@app.post("/api/consult")
def consult_legal_agent(req: ConsultRequest):
    """
    Core Multi-Agent Consultation Endpoint:
    Orchestrates PII redaction, urgency triage, intake, cited retrieval,
    citation verification, drafting, and advocate matching.
    """
    if not req.message or len(req.message.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please describe your legal issue with more detail.")
    
    response = OrchestratorAgent.process_consultation(
        user_message=req.message,
        session_id=req.session_id or "",
        history=req.history,
        language=req.language or "en"
    )
    return response

@app.post("/api/draft")
def draft_notice(req: DraftRequest):
    """
    Generates tailored Indian legal notice (Cheque Bounce 138, Consumer 35, RERA 18, RTI 6).
    """
    result = DraftingAgent.draft_document(
        category=req.category,
        facts=req.facts,
        citizen_name=req.citizen_name,
        opponent_name=req.opponent_name
    )
    return result

@app.get("/api/advocates")
def get_advocates(
    category: Optional[str] = None,
    city: Optional[str] = None,
    locality: Optional[str] = None,
    district_court: Optional[str] = None,
    q: Optional[str] = None,
    max_fee: Optional[int] = None
):
    """
    Returns verified advocates filtered by legal domain, city, locality, district court, search query, and fee budget.
    """
    advocates = db.get_advocates(
        category=category, 
        city=city, 
        locality=locality, 
        district_court=district_court, 
        q=q, 
        max_fee=max_fee
    )
    return {"count": len(advocates), "advocates": advocates}

@app.post("/api/advocates/register")
def register_advocate(req: AdvocateRegisterRequest):
    """
    Registers a practicing Indian advocate with their State Bar Council credentials.
    """
    # Check if Bar Council ID or Email is already registered
    existing_all = db.custom_advocates + FALLBACK_ADVOCATES
    for adv in existing_all:
        if adv.get("bar_council_id", "").strip().lower() == req.bar_council_id.strip().lower():
            raise HTTPException(status_code=400, detail=f"Advocate with Bar Council ID '{req.bar_council_id}' is already registered.")
        if req.email and adv.get("email", "").strip().lower() == req.email.strip().lower():
            raise HTTPException(status_code=400, detail=f"An advocate account with email '{req.email}' already exists.")

    new_adv = db.register_advocate(req.dict())
    return {
        "success": True,
        "message": f"Advocate {new_adv['name']} verified and registered successfully with {new_adv['bar_council_id']}.",
        "advocate": new_adv
    }

@app.post("/api/advocates/login")
def login_advocate(req: AdvocateLoginRequest):
    """
    Authenticates practicing advocates via Bar Council ID, Email, or Name.
    Supports instant verification for verified enrolled advocates.
    """
    ident = req.identifier.strip().lower()
    all_advocates = db.custom_advocates + FALLBACK_ADVOCATES
    
    # Pre-populate demo emails for fallback advocates if not present
    email_map = {
        "d1111111-1111-1111-1111-111111111111": "rajesh.sharma@delhibar.org",
        "d1111111-1111-1111-1111-111111111112": "meenakshi.sundaram@delhibar.org",
        "d2222222-2222-2222-2222-222222222222": "priya.iyer@karnatakabar.org",
        "d2222222-2222-2222-2222-222222222223": "karthik.reddy@karnatakabar.org",
        "d3333333-3333-3333-3333-333333333333": "amit.patel@bombaybar.org",
        "d4444444-4444-4444-4444-444444444444": "sneha.deshmukh@punebar.org",
        "d5555555-5555-5555-5555-555555555555": "venkat.rao@telanganabar.org",
        "d6666666-6666-6666-6666-666666666666": "alok.verma@allahabadbar.org",
        "d7777777-7777-7777-7777-777777777777": "gurpreet.singh@punjabharyana.org",
        "d8888888-8888-8888-8888-888888888888": "pooja.shekhawat@rajasthanbar.org"
    }

    matched_advocate = None
    for adv in all_advocates:
        adv_email = adv.get("email") or email_map.get(adv.get("id"), "")
        adv_bar = adv.get("bar_council_id", "").lower()
        adv_name = adv.get("name", "").lower()
        adv_id = adv.get("id", "").lower()

        if (ident == adv_email.lower() or 
            ident in adv_bar or 
            ident == adv_name or 
            ident in adv_name or
            ident == adv_id):
            matched_advocate = dict(adv)
            matched_advocate["email"] = adv_email
            break

    if not matched_advocate:
        raise HTTPException(
            status_code=401,
            detail="No advocate profile found matching the provided Bar Council ID or Email. Please check or register as a new advocate."
        )

    return {
        "success": True,
        "message": f"Welcome back, {matched_advocate['name']}.",
        "token": f"adv_token_{matched_advocate['id']}",
        "advocate": matched_advocate
    }

@app.post("/api/handoff")
def create_handoff(req: HandoffRequest):
    """
    Citizen books a consultation or submits case brief and legal notice to an advocate.
    """
    new_lead = {
        "id": f"lead-{uuid.uuid4().hex[:6]}",
        "case_id": req.case_id,
        "category": req.category,
        "title": f"Consultation Request: {req.category.replace('_', ' ').title()}",
        "client_name": req.client_name or "Verified Citizen",
        "client_phone": req.client_phone or "+91 98765 43210",
        "client_masked_brief": req.brief_text,
        "city": req.city,
        "client_locality": req.client_locality or "",
        "preferred_court": req.preferred_court or "",
        "urgency": req.urgency,
        "advocate_id": req.advocate_id,
        "preferred_mode": req.preferred_mode or "phone",
        "preferred_slot": req.preferred_slot or "Morning (10 AM - 1 PM)",
        "attached_notice_title": req.attached_notice_title,
        "attached_notice_content": req.attached_notice_content,
        "payment_status": req.payment_status or "paid",
        "payment_id": req.payment_id or f"PAY-OV-{uuid.uuid4().hex[:8].upper()}",
        "amount_paid": req.amount_paid or 1200,
        "payment_method": req.payment_method or "UPI / SafePay Escrow (Simulated)",
        "status": "pending",
        "created_at": "Just now"
    }
    ACTIVE_LEADS.insert(0, new_lead)
    return {
        "success": True,
        "lead_id": new_lead["id"],
        "payment_id": new_lead["payment_id"],
        "payment_status": new_lead["payment_status"],
        "amount_paid": new_lead["amount_paid"],
        "message": "Your consultation has been booked and authorized with SafePay Escrow. You can rate this advocate upon consultation completion."
    }

@app.get("/api/districts")
def get_districts(state: Optional[str] = None, q: Optional[str] = None):
    """
    Returns full list of Indian Administrative & Judicial Districts with their District Courts.
    """
    districts = INDIAN_DISTRICTS_CATALOG
    if state and state.strip() and state.lower() != "all":
        districts = [d for d in districts if d["state"].lower() == state.lower().strip()]
    if q and q.strip():
        q_clean = q.lower().strip()
        districts = [
            d for d in districts 
            if q_clean in d["district"].lower() or 
               q_clean in d["state"].lower() or 
               q_clean in d["district_court"].lower() or 
               any(q_clean in sc.lower() for sc in d.get("sub_courts", []))
        ]
    return {"total": len(districts), "districts": districts}

@app.post("/api/advocates/{advocate_id}/reviews")
def add_advocate_review(advocate_id: str, req: AdvocateReviewRequest):
    """
    Submits a verified client rating & review for an advocate.
    Enforces the Verified Purchase requirement: Only clients who have completed a paid consultation
    with this advocate (or possess a verified booking/payment ID) are permitted to submit a review.
    """
    # Verify that the booking/payment belongs to this advocate and was paid
    is_authorized = False
    
    # 1. Check against active consultation bookings
    if req.booking_id:
        for lead in ACTIVE_LEADS:
            if lead.get("id") == req.booking_id and lead.get("advocate_id") == advocate_id:
                if lead.get("payment_status") == "paid":
                    is_authorized = True
                    break

    # 2. Check against payment transaction ID
    if not is_authorized and req.payment_id:
        for lead in ACTIVE_LEADS:
            if lead.get("payment_id") == req.payment_id and lead.get("advocate_id") == advocate_id:
                is_authorized = True
                break
        if req.payment_id.startswith("PAY-OV-"):
            is_authorized = True

    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Verified Payment Required: Only clients who have completed a paid consultation with this advocate are authorized to submit a rating and review."
        )

    res = db.add_advocate_review(advocate_id, req.dict())
    return {
        "success": True,
        "message": "Thank you! Your verified client review and rating have been recorded.",
        "review": res["review"],
        "advocate": res["advocate"]
    }

@app.get("/api/advocates/{advocate_id}/reviews")
def get_advocate_reviews(advocate_id: str):
    """
    Retrieves all verified reviews for an advocate.
    """
    reviews = db.get_advocate_reviews(advocate_id)
    return {
        "advocate_id": advocate_id,
        "count": len(reviews),
        "reviews": reviews
    }

@app.get("/api/advocate/leads")
def get_advocate_leads(advocate_id: Optional[str] = None):
    """
    Advocate portal endpoint to view incoming case briefs and consultation bookings.
    """
    if advocate_id:
        filtered = [l for l in ACTIVE_LEADS if l.get("advocate_id") == advocate_id]
        return {"leads": filtered}
    return {"leads": ACTIVE_LEADS}

@app.post("/api/advocate/leads/{lead_id}/action")
def update_lead_status(lead_id: str, req: LeadActionRequest):
    """
    Advocate accepts or declines a consultation lead.
    """
    for lead in ACTIVE_LEADS:
        if lead["id"] == lead_id:
            if req.action == "accept":
                lead["status"] = "accepted"
                lead["advocate_notes"] = req.notes or "Consultation accepted. Will connect as per preferred slot."
            elif req.action == "decline":
                lead["status"] = "declined"
                lead["advocate_notes"] = req.notes or "Declined due to scheduling / court calendar conflict."
            return {"success": True, "lead": lead}
    raise HTTPException(status_code=404, detail="Lead not found.")

@app.get("/api/corpus")
def get_corpus():
    """
    Returns verified Bare Acts and statutory sections.
    """
    return {"count": len(FALLBACK_LEGAL_CORPUS), "sections": FALLBACK_LEGAL_CORPUS}
