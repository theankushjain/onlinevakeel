"use client";

import React, { useState, useRef, useCallback, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import {
  Scale, ShieldCheck, BookOpen, UserCheck, Award,
  FileText, Send, Clock, Check, Copy, Printer, Download,
  PhoneCall, MapPin, Building, Lock, Sparkles,
  AlertCircle, ChevronRight, ArrowRight, Search,
  UserPlus, LogIn, LogOut, Video, Phone, X, Briefcase, Calendar,
  Star, CreditCard
} from "lucide-react";
import { ALL_INDIAN_DISTRICTS, INDIAN_STATES, DistrictItem } from "@/data/indianDistricts";

/* ─── Types ─────────────────────────────────────────── */
interface AdvocateReview {
  id: string;
  advocate_id: string;
  client_name: string;
  rating: number;
  review_text: string;
  payment_id: string;
  booking_id?: string;
  knowledge_rating?: number;
  responsiveness_rating?: number;
  value_rating?: number;
  verified_paid: boolean;
  created_at: string;
}

interface PaidConsultationRecord {
  advocateId: string;
  advocateName: string;
  paymentId: string;
  leadId: string;
  amountPaid: number;
  bookedAt: string;
  rated?: boolean;
}

interface CitationRemedy {
  act_name: string;
  section: string;
  title: string;
  summary: string;
  limitation: string;
  penalties_or_relief?: string;
  statutory_cite: string;
}

interface Advocate {
  id: string;
  name: string;
  bar_council_id: string;
  state_bar_council?: string;
  practice_areas: string[];
  courts: string[];
  district_court?: string;
  office_location?: string;
  city: string;
  state: string;
  experience_years: number;
  languages: string[];
  consult_fee: number;
  rating: number;
  reviews: number;
  verified: boolean;
  bio: string;
  email?: string;
  phone?: string;
}

interface Lead {
  id: string;
  case_id: string;
  category: string;
  title: string;
  client_name?: string;
  client_phone?: string;
  client_locality?: string;
  preferred_court?: string;
  client_masked_brief: string;
  city: string;
  urgency: string;
  advocate_id?: string;
  advocate_name?: string;
  preferred_mode?: string;
  preferred_slot?: string;
  attached_notice_title?: string;
  attached_notice_content?: string;
  status: string;
  created_at: string;
  advocate_notes?: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  piiRedacted?: Record<string, string[]>;
  timestamp: string;
  askLocation?: boolean;
  locationMatched?: {
    city?: string;
    locality?: string;
    court?: string;
    count?: number;
  };
}

type DossierTab = "remedies" | "notice" | "advocates";
type MainTab    = "citizen" | "advocate" | "corpus";

/* ─── Constants ─────────────────────────────────────── */
const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const QUICK_PROMPTS = [
  { emoji: "💳", label: "Cheque bounce sec 138", query: "Someone gave me a cheque of ₹2,50,000 in New Delhi and it bounced yesterday. What legal notice do I issue and what are my rights?" },
  { emoji: "🏢", label: "Builder delay (RERA)", query: "My builder delayed flat handover in Bengaluru by 2 years after I paid ₹75 Lakhs. Can I claim RERA delay interest under Section 18?" },
  { emoji: "🛒", label: "Consumer complaint",  query: "An e-commerce portal delivered a damaged laptop worth ₹65,000 and refused replacement or refund. What can I do under the Consumer Protection Act?" },
  { emoji: "📄", label: "RTI filing",          query: "How do I file an RTI application regarding local municipal road tender funds? What sections apply?" },
];

const SAMPLE_LEADS = [
  {
    id: "lead-001", case_id: "OV-8F92A1",
    category: "cheque_bounce",
    title: "Cheque Dishonour of ₹4,50,000 — Commercial Invoices",
    client_masked_brief: "Client received cheque bounce memo from HDFC Bank on 15-Oct. Disputed amount ₹4,50,000. 15-day statutory notice ready. Drawer is a registered proprietorship in Nehru Place, Delhi.",
    city: "New Delhi", urgency: "urgent", status: "pending", created_at: "Today, 10:30 AM",
  },
  {
    id: "lead-002", case_id: "OV-3C19B4",
    category: "property_rera",
    title: "36-Month Possession Delay — 3BHK Whitefield Project",
    client_masked_brief: "Possession delayed beyond builder-buyer agreement date. Paid ₹85,00,000. Seeking Section 18 RERA monthly delay interest + refund option from Karnataka RERA authority.",
    city: "Bengaluru", urgency: "routine", status: "accepted", created_at: "Yesterday",
  },
];

const INDIAN_CITIES_CATALOG = [
  // Delhi NCR
  { city: "New Delhi", state: "Delhi", courts: ["Patiala House Court", "Rouse Avenue Court", "Delhi High Court"] },
  { city: "South Delhi (Saket)", state: "Delhi", courts: ["Saket District Court Complex"] },
  { city: "North Delhi (Tis Hazari)", state: "Delhi", courts: ["Tis Hazari Courts", "Rohini District Court"] },
  { city: "East Delhi (Karkardooma)", state: "Delhi", courts: ["Karkardooma Court Complex"] },
  { city: "South West Delhi (Dwarka)", state: "Delhi", courts: ["Dwarka District Court"] },
  { city: "Noida / Greater Noida", state: "Uttar Pradesh", courts: ["District Court Surajpur (Gautam Buddha Nagar)"] },
  { city: "Gurugram", state: "Haryana", courts: ["District & Sessions Court Gurugram"] },
  { city: "Faridabad", state: "Haryana", courts: ["District & Sessions Court Faridabad"] },
  { city: "Ghaziabad", state: "Uttar Pradesh", courts: ["District & Sessions Court Ghaziabad"] },
  // Maharashtra
  { city: "Mumbai", state: "Maharashtra", courts: ["City Civil & Sessions Court (Fort)", "Bombay High Court", "Esplanade Court"] },
  { city: "Mumbai Suburban (Bandra)", state: "Maharashtra", courts: ["Bandra Metropolitan Magistrate Court", "Borivali Court", "Andheri Court"] },
  { city: "Navi Mumbai / Thane", state: "Maharashtra", courts: ["Thane District & Sessions Court", "Belapur Court"] },
  { city: "Pune", state: "Maharashtra", courts: ["Pune District & Sessions Court (Shivajinagar)", "Cantonment Court"] },
  { city: "Nagpur", state: "Maharashtra", courts: ["District & Sessions Court Nagpur", "Bombay High Court (Nagpur Bench)"] },
  { city: "Nashik", state: "Maharashtra", courts: ["District & Sessions Court Nashik"] },
  { city: "Chhatrapati Sambhajinagar (Aurangabad)", state: "Maharashtra", courts: ["District & Sessions Court", "Bombay High Court (Aurangabad Bench)"] },
  { city: "Kolhapur", state: "Maharashtra", courts: ["Kolhapur District Court"] },
  { city: "Solapur", state: "Maharashtra", courts: ["Solapur District Court"] },
  // Karnataka
  { city: "Bengaluru", state: "Karnataka", courts: ["City Civil Court (Mayohall / Mayo Hall)", "Bengaluru City Civil & Sessions Court", "Karnataka High Court"] },
  { city: "Bengaluru (Rural)", state: "Karnataka", courts: ["Bangalore Rural District Court"] },
  { city: "Mysuru", state: "Karnataka", courts: ["Mysuru District & Sessions Court"] },
  { city: "Mangaluru", state: "Karnataka", courts: ["Dakshina Kannada District Court Mangaluru"] },
  { city: "Hubballi-Dharwad", state: "Karnataka", courts: ["Dharwad District Court", "Karnataka High Court (Dharwad Bench)"] },
  { city: "Belagavi", state: "Karnataka", courts: ["Belagavi District Court"] },
  { city: "Kalaburagi", state: "Karnataka", courts: ["Kalaburagi District Court", "Karnataka High Court (Kalaburagi Bench)"] },
  // Telangana & Andhra Pradesh
  { city: "Hyderabad", state: "Telangana", courts: ["City Civil Court Hyderabad (Purani Haveli)", "Nampally Criminal Courts", "Telangana High Court"] },
  { city: "Secunderabad", state: "Telangana", courts: ["Secunderabad Court Complex"] },
  { city: "Warangal", state: "Telangana", courts: ["Warangal District Court"] },
  { city: "Visakhapatnam", state: "Andhra Pradesh", courts: ["Visakhapatnam District Court"] },
  { city: "Vijayawada", state: "Andhra Pradesh", courts: ["NTR District Court Vijayawada"] },
  { city: "Guntur", state: "Andhra Pradesh", courts: ["Guntur District Court"] },
  { city: "Tirupati", state: "Andhra Pradesh", courts: ["Tirupati District Court"] },
  // Tamil Nadu
  { city: "Chennai", state: "Tamil Nadu", courts: ["City Civil Court Chennai (High Court Campus)", "Egmore Court", "Saidapet Court"] },
  { city: "Coimbatore", state: "Tamil Nadu", courts: ["Coimbatore District & Sessions Court"] },
  { city: "Madurai", state: "Tamil Nadu", courts: ["Madurai District Court", "Madras High Court (Madurai Bench)"] },
  { city: "Tiruchirappalli", state: "Tamil Nadu", courts: ["Trichy District Court"] },
  { city: "Salem", state: "Tamil Nadu", courts: ["Salem District Court"] },
  // Uttar Pradesh
  { city: "Lucknow", state: "Uttar Pradesh", courts: ["District & Sessions Court Lucknow (Qaiserbagh)", "Allahabad High Court (Lucknow Bench)"] },
  { city: "Kanpur", state: "Uttar Pradesh", courts: ["Kanpur Nagar District & Sessions Court"] },
  { city: "Prayagraj (Allahabad)", state: "Uttar Pradesh", courts: ["District Court Prayagraj", "Allahabad High Court"] },
  { city: "Varanasi", state: "Uttar Pradesh", courts: ["Varanasi District & Sessions Court"] },
  { city: "Agra", state: "Uttar Pradesh", courts: ["Agra District Court"] },
  { city: "Meerut", state: "Uttar Pradesh", courts: ["Meerut District Court"] },
  { city: "Bareilly", state: "Uttar Pradesh", courts: ["Bareilly District Court"] },
  { city: "Gorakhpur", state: "Uttar Pradesh", courts: ["Gorakhpur District Court"] },
  // Gujarat
  { city: "Ahmedabad", state: "Gujarat", courts: ["City Civil & Sessions Court Bhadra", "Mirzapur Rural Court", "Gujarat High Court"] },
  { city: "Surat", state: "Gujarat", courts: ["Surat District & Sessions Court (Athwalines)"] },
  { city: "Vadodara", state: "Gujarat", courts: ["Vadodara District Court"] },
  { city: "Rajkot", state: "Gujarat", courts: ["Rajkot District Court"] },
  { city: "Gandhinagar", state: "Gujarat", courts: ["Gandhinagar District Court"] },
  // West Bengal
  { city: "Kolkata", state: "West Bengal", courts: ["City Civil Court (Bankshall)", "Calcutta High Court", "Alipore District Court", "Sealdah Court"] },
  { city: "Howrah", state: "West Bengal", courts: ["Howrah District Court"] },
  { city: "Siliguri / Darjeeling", state: "West Bengal", courts: ["Siliguri Sub-divisional Court", "Darjeeling District Court"] },
  { city: "Asansol / Durgapur", state: "West Bengal", courts: ["Asansol Sub-divisional Court"] },
  // Rajasthan
  { city: "Jaipur", state: "Rajasthan", courts: ["District & Sessions Court Jaipur (Collectorate Circle Banipark)", "Rajasthan High Court Bench"] },
  { city: "Jodhpur", state: "Rajasthan", courts: ["District Court Jodhpur", "Rajasthan High Court Principal Seat"] },
  { city: "Udaipur", state: "Rajasthan", courts: ["Udaipur District Court"] },
  { city: "Kota", state: "Rajasthan", courts: ["Kota District Court"] },
  // Punjab, Haryana & Chandigarh
  { city: "Chandigarh", state: "Chandigarh", courts: ["District Courts Complex Sector 43 Chandigarh", "Punjab & Haryana High Court"] },
  { city: "Ludhiana", state: "Punjab", courts: ["District & Sessions Court Ludhiana"] },
  { city: "Amritsar", state: "Punjab", courts: ["Amritsar District Court"] },
  { city: "Jalandhar", state: "Punjab", courts: ["Jalandhar District Court"] },
  { city: "Mohali (SAS Nagar)", state: "Punjab", courts: ["District Courts Complex Sector 76 Mohali"] },
  { city: "Panchkula", state: "Haryana", courts: ["District Court Sector 1 Panchkula"] },
  // Kerala
  { city: "Kochi", state: "Kerala", courts: ["Ernakulam District & Sessions Court", "Kerala High Court"] },
  { city: "Thiruvananthapuram", state: "Kerala", courts: ["District Court Vanchiyoor"] },
  { city: "Kozhikode", state: "Kerala", courts: ["Kozhikode District Court"] },
  // Madhya Pradesh
  { city: "Bhopal", state: "Madhya Pradesh", courts: ["District & Sessions Court Bhopal"] },
  { city: "Indore", state: "Madhya Pradesh", courts: ["District Court Indore", "Madhya Pradesh High Court Bench"] },
  { city: "Jabalpur", state: "Madhya Pradesh", courts: ["District Court Jabalpur", "Madhya Pradesh High Court Principal Seat"] },
  { city: "Gwalior", state: "Madhya Pradesh", courts: ["District Court Gwalior", "Madhya Pradesh High Court Bench"] },
  // Bihar & Jharkhand
  { city: "Patna", state: "Bihar", courts: ["Patna Civil Court", "Patna High Court"] },
  { city: "Ranchi", state: "Jharkhand", courts: ["Ranchi Civil Court", "Jharkhand High Court"] },
  { city: "Jamshedpur", state: "Jharkhand", courts: ["Jamshedpur Civil Court"] },
  { city: "Dhanbad", state: "Jharkhand", courts: ["Dhanbad District Court"] },
  // Odisha, Assam, Uttarakhand & Others
  { city: "Bhubaneswar", state: "Odisha", courts: ["Bhubaneswar District & Sessions Court"] },
  { city: "Cuttack", state: "Odisha", courts: ["Cuttack District Court", "Orissa High Court"] },
  { city: "Guwahati", state: "Assam", courts: ["Kamrup Metro District Court", "Gauhati High Court"] },
  { city: "Dehradun", state: "Uttarakhand", courts: ["District & Sessions Court Dehradun"] },
  { city: "Shimla", state: "Himachal Pradesh", courts: ["District Court Chakkar Shimla", "HP High Court"] },
  { city: "Srinagar", state: "Jammu & Kashmir", courts: ["District Court Srinagar", "J&K High Court"] },
  { city: "Jammu", state: "Jammu & Kashmir", courts: ["District Court Janipur Jammu", "J&K High Court"] },
  { city: "Panaji / Goa", state: "Goa", courts: ["North Goa District Court Panaji", "Bombay High Court (Goa Bench)"] }
];

/* ─── Component ─────────────────────────────────────── */
/**
 * Agent replies are kept short by the backend, but a language model can still
 * run long. Anything past this many characters is clamped with a toggle so the
 * conversation stays scannable — the full statutory detail is in the Dossier
 * panel on the right regardless.
 */
const LONG_REPLY_CHARS = 700;

function CounselMessage({ text, clamp = true }: { text: string; clamp?: boolean }) {
  const [open, setOpen] = useState(false);

  if (!clamp || text.length <= LONG_REPLY_CHARS) {
    return (
      <div className="md-body">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
    );
  }

  // Cut on a line break where possible so a bullet is never sliced in half.
  const head = text.slice(0, LONG_REPLY_CHARS);
  const breakAt = head.lastIndexOf("\n");
  const preview = (breakAt > 250 ? head.slice(0, breakAt) : head).trimEnd() + " …";

  return (
    <div className="md-body">
      <ReactMarkdown>{open ? text : preview}</ReactMarkdown>
      <button
        type="button"
        className="reply-toggle"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        {open ? "Show less" : "Read the full explanation"}
      </button>
    </div>
  );
}

function ConsultDesk() {
  const [mainTab,     setMainTab]     = useState<MainTab>("citizen");
  const [dossierTab,  setDossierTab]  = useState<DossierTab>("remedies");
  const [language,    setLanguage]    = useState<"en" | "hi">("en");
  const [step,        setStep]        = useState(1);
  const [caseId,      setCaseId]      = useState("");
  const [inputText,   setInputText]   = useState("");
  const [submitting,  setSubmitting]  = useState(false);
  const [copiedNotice,setCopiedNotice]= useState(false);
  const [booking,     setBooking]     = useState<Record<string, string>>({});
  const [leads,       setLeads]       = useState<Lead[]>(SAMPLE_LEADS as any);
  const [selectedLead,setSelectedLead]= useState<Lead | null>(SAMPLE_LEADS[0] as any);
  const [corpusItems, setCorpusItems] = useState<any[]>([]);
  const [verifyBadge, setVerifyBadge] = useState("Verified");
  const [remedies,    setRemedies]    = useState<CitationRemedy[]>([]);
  const [draftNotice, setDraftNotice] = useState<any>(null);
  const [advocates,   setAdvocates]   = useState<Advocate[]>([]);
  const [currentCategory, setCurrentCategory] = useState<string>("general_civil");

  /* ── Advocate Search & Location Filtering State ── */
  const [advSearchQuery, setAdvSearchQuery] = useState("");
  const [selectedCityFilter, setSelectedCityFilter] = useState("all");
  const [detectedCity, setDetectedCity] = useState("");
  const [clientLocality, setClientLocality] = useState("");
  const [clientCourt, setClientCourt] = useState("");
  const [locationUpdatedBanner, setLocationUpdatedBanner] = useState<string | null>(null);

  /* ── Intuitive District Selector State (754 Indian Districts) ── */
  const [districtSearchQuery, setDistrictSearchQuery] = useState("");
  const [selectedStateFilter, setSelectedStateFilter] = useState("all");
  const [showDistrictDropdown, setShowDistrictDropdown] = useState(false);
  const [activeDistrictItem, setActiveDistrictItem] = useState<DistrictItem | null>(null);
  const districtDropdownRef = useRef<HTMLDivElement>(null);

  // Close district dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (districtDropdownRef.current && !districtDropdownRef.current.contains(event.target as Node)) {
        setShowDistrictDropdown(false);
      }
    };
    if (showDistrictDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showDistrictDropdown]);

  /* ── Paid Consultations & Rating System State ── */
  const [paidConsultations, setPaidConsultations] = useState<PaidConsultationRecord[]>([]);
  const [ratingModalAdvocate, setRatingModalAdvocate] = useState<Advocate | null>(null);
  const [ratingLockedModalAdvocate, setRatingLockedModalAdvocate] = useState<Advocate | null>(null);
  const [reviewsModalAdvocate, setReviewsModalAdvocate] = useState<Advocate | null>(null);
  const [advocateReviewsList, setAdvocateReviewsList] = useState<AdvocateReview[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [userStars, setUserStars] = useState(5);
  const [userReviewText, setUserReviewText] = useState("");
  const [userKnowledge, setUserKnowledge] = useState(5);
  const [userResponsiveness, setUserResponsiveness] = useState(5);
  const [userValue, setUserValue] = useState(5);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccessMessage, setReviewSuccessMessage] = useState<string | null>(null);

  // Load verified paid consultations on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("ov_paid_consultations");
      if (saved) {
        setPaidConsultations(JSON.parse(saved));
      } else {
        const demoPaid: PaidConsultationRecord[] = [
          {
            advocateId: "d1111111-1111-1111-1111-111111111111",
            advocateName: "Adv. Rajesh Sharma",
            paymentId: "PAY-OV-88A912B1",
            leadId: "lead-001",
            amountPaid: 1500,
            bookedAt: "Yesterday",
            rated: false
          }
        ];
        setPaidConsultations(demoPaid);
        localStorage.setItem("ov_paid_consultations", JSON.stringify(demoPaid));
      }
    } catch {}
  }, []);

  /* ── Systematic Consultation Booking Modal State ── */
  const [bookingModalAdvocate, setBookingModalAdvocate] = useState<Advocate | null>(null);
  const [bookingForm, setBookingForm] = useState({
    client_name: "",
    client_phone: "",
    preferred_mode: "phone",
    preferred_slot: "Today (Next Available Slot)",
    attach_notice: true,
    notes: ""
  });
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);
  const [activeNoticePreview, setActiveNoticePreview] = useState<string | null>(null);

  /* ── Advocate Portal Authentication State ── */
  const [advocateUser, setAdvocateUser] = useState<Advocate | null>(null);
  const [advAuthMode, setAdvAuthMode] = useState<"login" | "register">("login");
  const [advLoginForm, setAdvLoginForm] = useState({ identifier: "", password: "" });
  const [advRegForm, setAdvRegForm] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    bar_council_id: "",
    state_bar_council: "Bar Council of Delhi",
    practice_areas: ["cheque_bounce", "criminal_bail"],
    courts: "Delhi High Court, District Courts",
    district_court: "Saket District Court (South Delhi)",
    office_location: "Chamber 412, Lawyers Block, Saket District Court Complex",
    city: "New Delhi",
    state: "Delhi",
    experience_years: 7,
    consult_fee: 1500,
    languages: "English, Hindi",
    bio: ""
  });
  const [advAuthError, setAdvAuthError] = useState("");
  const [advAuthLoading, setAdvAuthLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "agent",
      text: `Namaste. I am your **OnlineVakeel AI Legal Counsel** — trained on the complete corpus of Indian Bare Acts, including the Bharatiya Nyaya Sanhita (BNS), Negotiable Instruments Act, RERA, Consumer Protection Act, and over 40 central legislations.\n\nYou may describe your legal situation in plain, everyday language. I will:\n\n- **Identify** the applicable laws and your legal rights\n- **Cite** the exact Act, section, and statutory remedy\n- **Draft** a formal legal notice if required\n- **Connect** you with a verified advocate in your city\n\nAll personal identifiers (Aadhaar, PAN, phone) are automatically masked under the **DPDP Act, 2023** before any AI processing.\n\n> *What legal matter can I help you with today?*`,
      timestamp: "Just now",
    },
  ]);

  const chatEndRef  = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const searchParams = useSearchParams();
  const autoSentRef  = useRef(false);

  /* Load stored advocate session on mount */
  useEffect(() => {
    try {
      const stored = localStorage.getItem("ov_advocate_session");
      if (stored) {
        const parsed = JSON.parse(stored);
        setAdvocateUser(parsed);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, submitting]);

  /* Pre-populate corpus & all advocates directory */
  useEffect(() => {
    fetch(`${BACKEND}/api/corpus`)
      .then(r => r.json())
      .then(d => { if (d?.sections) setCorpusItems(d.sections); })
      .catch(() => {});

    fetch(`${BACKEND}/api/advocates`)
      .then(r => r.json())
      .then(d => { if (d?.advocates) setAdvocates(d.advocates); })
      .catch(() => {});

    fetchLeads();
  }, []);

  /* Fetch live leads for advocate portal */
  const fetchLeads = (advId?: string) => {
    const url = advId ? `${BACKEND}/api/advocate/leads?advocate_id=${advId}` : `${BACKEND}/api/advocate/leads`;
    fetch(url)
      .then(r => r.json())
      .then(d => {
        if (d?.leads && d.leads.length > 0) {
          setLeads(d.leads);
          setSelectedLead(d.leads[0]);
        }
      })
      .catch(() => {});
  };

  /* When advocate user logs in/changes, reload their leads */
  useEffect(() => {
    if (advocateUser) {
      fetchLeads(advocateUser.id);
    }
  }, [advocateUser]);

  /* Auto-resize textarea */
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  /* Send message */
  const sendMessage = useCallback(async (textOverride?: string) => {
    const text = (textOverride || inputText).trim();
    if (!text || submitting) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setSubmitting(true);

    try {
      const history = messages
        .filter(m => m.id !== "welcome")
        .map(m => ({ sender: m.sender, text: m.text }));

      const res = await fetch(`${BACKEND}/api/consult`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: caseId, language, history }),
      });

      if (!res.ok) throw new Error("API error");

      const data = await res.json();
      setCaseId(data.case_id || caseId);
      setRemedies(data.statutory_remedies || []);
      setDraftNotice(data.draft_document || null);
      if (data.matched_advocates && data.matched_advocates.length > 0) {
        setAdvocates(data.matched_advocates);
      }
      if (data.category || data.intake?.category) {
        setCurrentCategory(data.category || data.intake.category);
      }
      // Check if location was recognized in facts or backend response
      const factsObj = data.facts_extracted || data.intake?.facts || {};
      const targetDistrictName = data.detected_district || factsObj.detected_district || "";
      const targetState = data.detected_state || factsObj.detected_state || "";
      const targetCity = data.detected_city || factsObj.locations_mentioned?.[0] || "";
      const targetCourt = data.detected_court || factsObj.district_courts_mentioned?.[0] || "";
      const targetLocality = factsObj.localities_mentioned?.[0] || "";

      let matchedDistrict: DistrictItem | null = null;
      if (targetDistrictName) {
        matchedDistrict = ALL_INDIAN_DISTRICTS.find(d => 
          d.district.toLowerCase() === targetDistrictName.toLowerCase()
        ) || null;
      }
      if (!matchedDistrict && targetCity) {
        const cLow = targetCity.toLowerCase();
        matchedDistrict = ALL_INDIAN_DISTRICTS.find(d => 
          d.district.toLowerCase() === cLow ||
          cLow.includes(d.district.toLowerCase()) ||
          d.district.toLowerCase().includes(cLow) ||
          (cLow.includes("noida") && d.district.toLowerCase().includes("gautam")) ||
          (cLow.includes("gurgaon") && d.district.toLowerCase().includes("gurugram")) ||
          (cLow.includes("bangalore") && d.district.toLowerCase().includes("bengaluru")) ||
          (cLow.includes("bombay") && d.district.toLowerCase().includes("mumbai")) ||
          d.districtCourt.toLowerCase().includes(cLow) ||
          d.subCourts.some(sc => sc.toLowerCase().includes(cLow) || cLow.includes(sc.toLowerCase()))
        ) || null;
      }

      let newlyDetectedLoc = Boolean(data.newly_detected_location || matchedDistrict || targetCity);
      let matchedLocSummary = "";

      if (matchedDistrict) {
        setActiveDistrictItem(matchedDistrict);
        setSelectedCityFilter(matchedDistrict.district);
        setSelectedStateFilter(matchedDistrict.state);
        setDistrictSearchQuery(`${matchedDistrict.district}, ${matchedDistrict.state}`);
        setClientCourt(matchedDistrict.districtCourt);
        setDetectedCity(matchedDistrict.district);
        if (targetLocality) setClientLocality(targetLocality);
        matchedLocSummary = `${matchedDistrict.district}, ${matchedDistrict.state} (${matchedDistrict.districtCourt})`;
        setLocationUpdatedBanner(`🎯 Advocates panel automatically updated for ${matchedLocSummary}`);
        setDossierTab("advocates");
      } else if (targetCity) {
        setDetectedCity(targetCity);
        setSelectedCityFilter(targetCity);
        if (targetCourt) setClientCourt(targetCourt);
        if (targetLocality) setClientLocality(targetLocality);
        if (targetState) setSelectedStateFilter(targetState);
        matchedLocSummary = targetCourt ? `${targetCourt} · ${targetCity}` : targetCity;
        setLocationUpdatedBanner(`🎯 Advocates panel automatically updated for ${matchedLocSummary}`);
        setDossierTab("advocates");
      }

      const hasLoc = Boolean(
        matchedDistrict ||
        targetDistrictName ||
        targetCity ||
        (factsObj.locations_mentioned && factsObj.locations_mentioned.length > 0) ||
        (factsObj.district_courts_mentioned && factsObj.district_courts_mentioned.length > 0)
      );

      const guidanceText = data.guidance || "";
      const asksForLocation = !hasLoc && Boolean(
        guidanceText && (
          guidanceText.toLowerCase().includes("which city") ||
          guidanceText.toLowerCase().includes("what city") ||
          guidanceText.toLowerCase().includes("which district") ||
          guidanceText.toLowerCase().includes("location check") ||
          guidanceText.includes("शहर") ||
          guidanceText.includes("ज़िला न्यायालय")
        )
      );

      if (data.verification?.verification_badge) setVerifyBadge(data.verification.verification_badge);
      setStep(3);

      // Calculate true number of advocates practicing in this specific location
      const locCity = (matchedDistrict?.district || targetDistrictName || targetCity || factsObj.locations_mentioned?.[0] || "").toLowerCase();
      const locCourt = (matchedDistrict?.districtCourt || targetCourt || factsObj.district_courts_mentioned?.[0] || "").toLowerCase();
      const locArea = (targetLocality || "").toLowerCase();

      const candidateList = (data.matched_advocates && data.matched_advocates.length > 0) ? data.matched_advocates : advocates;
      
      let locationCount = 0;
      if (data.location_matched_count !== undefined && data.location_matched_count > 0) {
        locationCount = data.location_matched_count;
      } else {
        const matches = candidateList.filter((adv: Advocate) => {
          const aCity = (adv.city || "").toLowerCase();
          const aCourt = (adv.district_court || "").toLowerCase();
          const aCourtsAll = (adv.courts || []).map(c => c.toLowerCase()).join(" ");
          const aOffice = (adv.office_location || "").toLowerCase();
          
          if (locCity && (aCity.includes(locCity) || locCity.includes(aCity) || aCourt.includes(locCity) || aCourtsAll.includes(locCity))) return true;
          if (locCourt && (aCourt.includes(locCourt) || locCourt.includes(aCourt) || aCourtsAll.includes(locCourt))) return true;
          if (locArea && (aOffice.includes(locArea) || locArea.includes(aOffice))) return true;
          if ((locCity.includes("noida") || locCity.includes("gautam")) && (aCity.includes("gautam") || aCourt.includes("surajpur") || aCourt.includes("noida"))) return true;
          if (locCity.includes("gurgaon") && aCity.includes("gurugram")) return true;
          if (locCity.includes("bangalore") && aCity.includes("bengaluru")) return true;
          if (locCity.includes("bombay") && aCity.includes("mumbai")) return true;
          return false;
        });
        locationCount = matches.length > 0 ? matches.length : 1;
      }

      setMessages(prev => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: "agent",
          text: data.guidance || "I have reviewed your situation. Please find the applicable statutes in the panel on the right.",
          piiRedacted: data.pii_redacted,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          askLocation: asksForLocation,
          locationMatched: newlyDetectedLoc && matchedLocSummary ? {
            city: matchedDistrict?.district || targetDistrictName || targetCity || factsObj.locations_mentioned?.[0],
            locality: targetLocality,
            court: matchedDistrict?.districtCourt || targetCourt || factsObj.district_courts_mentioned?.[0],
            count: locationCount
          } : undefined,
        },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: `a-err-${Date.now()}`,
          sender: "agent",
          text: `I encountered a temporary issue reaching the backend. Please ensure the backend server is running at \`${BACKEND}\`.\n\nIn the meantime, here is some general guidance:\n\n- **Cheque Bounce (NI Act, Sec 138):** You have 30 days from receiving the dishonour memo to send a 15-day demand notice via registered post.\n- **RERA (Sec 18):** You are entitled to interest at the SBI MCLR rate on amounts paid, for each month of delay.\n- **Consumer Forum:** File online at edaakhil.nic.in within 2 years of cause of action.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setSubmitting(false);
    }
  }, [inputText, submitting, caseId, language, messages]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* Auto-send the ?q= param passed from the landing page */
  useEffect(() => {
    if (autoSentRef.current) return;
    const q = searchParams.get("q");
    if (q && q.trim()) {
      autoSentRef.current = true;
      // Small delay so the welcome message renders first
      setTimeout(() => sendMessage(q.trim()), 300);
    }
  }, [searchParams, sendMessage]);


  const copyNotice = () => {
    if (!draftNotice?.content) return;
    navigator.clipboard.writeText(draftNotice.content);
    setCopiedNotice(true);
    setTimeout(() => setCopiedNotice(false), 2500);
  };

  const downloadNoticePdf = async () => {
    if (!draftNotice?.content) return;
    try {
      const { jsPDF } = await import("jspdf");
      const doc = new jsPDF({ format: "a4", unit: "mm" });
      const margin = 20;
      const pageWidth = 210;
      const contentWidth = pageWidth - (margin * 2);
      let y = 22;

      // Letterhead
      doc.setFont("times", "bold");
      doc.setFontSize(13);
      doc.text("CHAMBERS OF ADVOCATES & LEGAL COUNSEL", 105, y, { align: "center" });
      y += 5.5;

      doc.setFont("times", "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(80, 80, 80);
      doc.text("HIGH COURT & DISTRICT COURTS PRACTICE · INDIA", 105, y, { align: "center" });
      y += 4;

      doc.setDrawColor(40, 40, 40);
      doc.setLineWidth(0.4);
      doc.line(margin, y, pageWidth - margin, y);
      y += 10;

      doc.setTextColor(20, 20, 20);
      doc.setFontSize(10.5);

      const cleanText = draftNotice.content.replace(/\*\*/g, "");
      const paragraphs = cleanText.split("\n");

      for (const p of paragraphs) {
        if (!p.trim()) {
          y += 4.5;
          continue;
        }
        const trimmed = p.trim();
        const isHeading = trimmed.startsWith("#") || (trimmed.toUpperCase() === trimmed && trimmed.length < 80);
        const isSubject = trimmed.startsWith("Subject:") || trimmed.startsWith("SUB:") || trimmed.startsWith("Sub:");

        if (isHeading || isSubject) {
          doc.setFont("times", "bold");
        } else {
          doc.setFont("times", "normal");
        }

        const textToPrint = p.replace(/^#+\s*/, "");
        const lines = doc.splitTextToSize(textToPrint, contentWidth);

        if (y + (lines.length * 5) > 275) {
          doc.addPage();
          y = 22;
        }

        doc.text(lines, margin, y);
        y += (lines.length * 5.2) + 2;
      }

      const fileName = `${(draftNotice.title || "Legal_Notice").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 35)}.pdf`;
      doc.save(fileName);
    } catch (err) {
      console.error("PDF generation error, falling back to print:", err);
      printNotice();
    }
  };

  const printNotice = () => {
    if (!draftNotice?.content) return;
    const printElem = document.getElementById("printable-legal-notice");
    if (!printElem) {
      window.print();
      return;
    }

    const existingFrame = document.getElementById("notice-print-frame");
    if (existingFrame) existingFrame.remove();

    const iframe = document.createElement("iframe");
    iframe.id = "notice-print-frame";
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "none";
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow?.document;
    if (!doc) {
      window.print();
      return;
    }

    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${draftNotice.title || "Legal Demand Notice"}</title>
          <style>
            @page {
              size: A4 portrait;
              margin: 20mm;
            }
            body {
              font-family: 'Times New Roman', Times, Georgia, serif;
              color: #000;
              background: #fff;
              margin: 0;
              padding: 0;
              font-size: 11pt;
              line-height: 1.7;
            }
            .notice-letterhead {
              text-align: center;
              border-bottom: 2px solid #000;
              padding-bottom: 12px;
              margin-bottom: 22px;
            }
            .notice-letterhead-title {
              font-size: 14pt;
              font-weight: bold;
              text-transform: uppercase;
              letter-spacing: 1px;
            }
            .notice-letterhead-sub {
              font-size: 9pt;
              color: #333;
              text-transform: uppercase;
              margin-top: 4px;
            }
            .notice-letterhead svg {
              display: none;
            }
            .md-notice h1, .md-notice h2, .md-notice h3, .md-notice h4 {
              text-align: center;
              font-size: 12pt;
              font-weight: bold;
              margin: 16px 0 10px 0;
              text-transform: uppercase;
              color: #000;
            }
            .md-notice p {
              margin-bottom: 12px;
              text-align: justify;
              color: #000;
            }
            .md-notice ol, .md-notice ul {
              padding-left: 24px;
              margin-bottom: 12px;
            }
            .md-notice li {
              margin-bottom: 6px;
              text-align: justify;
              color: #000;
            }
            .md-notice strong, .md-notice b {
              font-weight: bold;
              color: #000;
            }
          </style>
        </head>
        <body>
          ${printElem.innerHTML}
        </body>
      </html>
    `);
    doc.close();

    setTimeout(() => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
    }, 200);
  };

  /* ── Advocate Auth Handlers ── */
  const handleAdvLogin = async (identOverride?: string) => {
    setAdvAuthError("");
    setAdvAuthLoading(true);
    const identifier = identOverride || advLoginForm.identifier;
    try {
      const res = await fetch(`${BACKEND}/api/advocates/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, password: advLoginForm.password || undefined })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed. Please verify credentials.");
      }
      setAdvocateUser(data.advocate);
      localStorage.setItem("ov_advocate_session", JSON.stringify(data.advocate));
      fetchLeads(data.advocate.id);
    } catch (err: any) {
      setAdvAuthError(err.message || "Login failed");
    } finally {
      setAdvAuthLoading(false);
    }
  };

  const handleAdvRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdvAuthError("");
    setAdvAuthLoading(true);
    try {
      const payload = {
        name: advRegForm.name,
        email: advRegForm.email,
        password: advRegForm.password || "vakeel123",
        phone: advRegForm.phone,
        bar_council_id: advRegForm.bar_council_id,
        state_bar_council: advRegForm.state_bar_council,
        practice_areas: advRegForm.practice_areas,
        courts: advRegForm.courts.split(",").map(c => c.trim()).filter(Boolean),
        district_court: advRegForm.district_court.trim() || advRegForm.courts.split(",")[0]?.trim() || "District Court",
        office_location: advRegForm.office_location.trim() || `Chamber Office, ${advRegForm.city}`,
        city: advRegForm.city,
        state: advRegForm.state,
        experience_years: Number(advRegForm.experience_years) || 5,
        consult_fee: Number(advRegForm.consult_fee) || 1200,
        languages: advRegForm.languages.split(",").map(l => l.trim()).filter(Boolean),
        bio: advRegForm.bio
      };

      const res = await fetch(`${BACKEND}/api/advocates/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration failed. Check inputs.");
      }

      setAdvocateUser(data.advocate);
      localStorage.setItem("ov_advocate_session", JSON.stringify(data.advocate));
      fetchLeads(data.advocate.id);
      // Also update global advocates list so the newly registered advocate appears in citizen search!
      setAdvocates(prev => [data.advocate, ...prev]);
    } catch (err: any) {
      setAdvAuthError(err.message || "Registration failed");
    } finally {
      setAdvAuthLoading(false);
    }
  };

  const handleAdvLogout = () => {
    setAdvocateUser(null);
    localStorage.removeItem("ov_advocate_session");
  };

  /* ── Citizen Consultation Booking Handlers ── */
  const openBookingModal = (adv: Advocate) => {
    setBookingModalAdvocate(adv);
    setBookingSuccess(null);
  };

  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingModalAdvocate) return;
    setBookingLoading(true);

    try {
      // Find summary of client issue from messages
      const userMsgs = messages.filter(m => m.sender === "user").map(m => m.text);
      const briefSummary = userMsgs.length > 0 ? userMsgs.join(" | ") : "Citizen consultation request from OnlineVakeel.";

      const payload = {
        case_id: caseId || `OV-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
        advocate_id: bookingModalAdvocate.id,
        brief_text: briefSummary,
        category: currentCategory || "general_civil",
        city: bookingModalAdvocate.city,
        client_locality: clientLocality.trim() || "",
        preferred_court: clientCourt.trim() || bookingModalAdvocate.district_court || "",
        urgency: "urgent",
        client_name: bookingForm.client_name.trim() || "Citizen (Verified)",
        client_phone: bookingForm.client_phone.trim() || "+91 98765 43210",
        preferred_mode: bookingForm.preferred_mode,
        preferred_slot: bookingForm.preferred_slot,
        attached_notice_title: bookingForm.attach_notice && draftNotice ? (draftNotice.title || "Pre-Litigation Demand Notice") : null,
        attached_notice_content: bookingForm.attach_notice && draftNotice ? draftNotice.content : null,
        payment_status: "paid",
        amount_paid: bookingModalAdvocate.consult_fee || 1200
      };

      const res = await fetch(`${BACKEND}/api/handoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Booking failed");

      // Record verified paid consultation to authorize client ratings
      const paymentId = data.payment_id || `PAY-OV-${Math.random().toString(36).substring(2, 10).toUpperCase()}`;
      const newPaidRecord: PaidConsultationRecord = {
        advocateId: bookingModalAdvocate.id,
        advocateName: bookingModalAdvocate.name,
        paymentId: paymentId,
        leadId: data.lead_id || "LEAD-CONFIRMED",
        amountPaid: bookingModalAdvocate.consult_fee || 1200,
        bookedAt: "Just now",
        rated: false
      };

      setPaidConsultations(prev => {
        const next = [newPaidRecord, ...prev.filter(p => p.advocateId !== bookingModalAdvocate.id)];
        try {
          localStorage.setItem("ov_paid_consultations", JSON.stringify(next));
        } catch {}
        return next;
      });

      setBookingSuccess(data.lead_id || "LEAD-CONFIRMED");
      setBooking(prev => ({ ...prev, [bookingModalAdvocate.id]: "✓ Booked & Paid" }));
      setStep(4);
      fetchLeads();
    } catch (err: any) {
      alert("Failed to submit booking: " + (err.message || "Server error"));
    } finally {
      setBookingLoading(false);
    }
  };

  /* ── Rating & Verified Reviews Handlers ── */
  const openRatingModal = (adv: Advocate) => {
    // Check if client has a verified paid consultation with this advocate
    const isPaid = paidConsultations.some(p => p.advocateId === adv.id);
    if (!isPaid) {
      setRatingLockedModalAdvocate(adv);
      return;
    }
    setRatingModalAdvocate(adv);
    setUserStars(5);
    setUserReviewText("");
    setUserKnowledge(5);
    setUserResponsiveness(5);
    setUserValue(5);
    setReviewSuccessMessage(null);
  };

  const submitAdvocateReview = async () => {
    if (!ratingModalAdvocate) return;
    const paidRec = paidConsultations.find(p => p.advocateId === ratingModalAdvocate.id);
    if (!paidRec) {
      alert("Verified Payment Authorization Required: Only clients who have completed a paid consultation with this advocate can submit a rating.");
      return;
    }
    if (!userReviewText.trim()) {
      alert("Please provide a brief review detailing your legal advice or consultation experience.");
      return;
    }

    setSubmittingReview(true);
    try {
      const res = await fetch(`${BACKEND}/api/advocates/${ratingModalAdvocate.id}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating: userStars,
          review_text: userReviewText.trim(),
          client_name: "Verified Client",
          booking_id: paidRec.leadId,
          payment_id: paidRec.paymentId,
          knowledge_rating: userKnowledge,
          responsiveness_rating: userResponsiveness,
          value_rating: userValue
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to submit review");

      // Mark consultation as rated
      setPaidConsultations(prev => {
        const next = prev.map(p => p.advocateId === ratingModalAdvocate.id ? { ...p, rated: true } : p);
        try {
          localStorage.setItem("ov_paid_consultations", JSON.stringify(next));
        } catch {}
        return next;
      });

      // Update aggregate rating in advocate list
      if (data.advocate) {
        setAdvocates(prev => prev.map(a => a.id === ratingModalAdvocate.id ? { ...a, rating: data.advocate.rating, reviews: data.advocate.reviews } : a));
      }

      setReviewSuccessMessage("Thank you! Your verified client review and rating have been recorded.");
      setTimeout(() => {
        setRatingModalAdvocate(null);
        setReviewSuccessMessage(null);
      }, 2000);
    } catch (err: any) {
      alert(err.message || "Failed to submit review.");
    } finally {
      setSubmittingReview(false);
    }
  };

  const openReviewsDrawer = async (adv: Advocate) => {
    setReviewsModalAdvocate(adv);
    setReviewsLoading(true);
    try {
      const res = await fetch(`${BACKEND}/api/advocates/${adv.id}/reviews`);
      const data = await res.json();
      if (res.ok && data.reviews) {
        setAdvocateReviewsList(data.reviews);
      } else {
        setAdvocateReviewsList([]);
      }
    } catch {
      setAdvocateReviewsList([]);
    } finally {
      setReviewsLoading(false);
    }
  };

  /* ── Lead Management Handlers ── */
  const updateLead = async (action: "accept" | "decline") => {
    if (!selectedLead) return;
    const status = action === "accept" ? "accepted" : "declined";
    try {
      await fetch(`${BACKEND}/api/advocate/leads/${selectedLead.id}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, notes: `Consultation ${status} by counsel.` })
      });
    } catch {
      // ignore
    }
    setLeads(prev => prev.map(l => l.id === selectedLead.id ? { ...l, status } : l));
    setSelectedLead(prev => prev ? { ...prev, status } : null);
  };

  /* ── Step helper ── */
  const stepStatus = (n: number) => {
    if (step > n) return "done";
    if (step === n) return "active";
    return "";
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--bg)" }}>

      {/* ── TRUST STRIP ── */}
      <div className="trust-strip">
        <div className="trust-strip-items">
          <div className="trust-strip-item">
            <Lock size={11} />
            <span>DPDP Act, 2023 • <strong>Pre-LLM PII masking</strong></span>
          </div>
          <div className="trust-strip-item">
            <ShieldCheck size={11} />
            <span><strong>Bar Council of India</strong> verified advocate network</span>
          </div>
          <div className="trust-strip-item">
            <BookOpen size={11} />
            <span>Grounded in <strong>India Code & Bharatiya Nyaya Sanhita</strong></span>
          </div>
        </div>
        <div className="trust-strip-right">
          NALSA Toll-Free: <strong>15100</strong>
        </div>
      </div>

      {/* ── HEADER ── */}
      <header className="site-header">
        <Link href="/" className="brand" style={{ textDecoration: "none" }}>
          <div className="brand-seal">
            <Scale size={18} />
          </div>
          <div>
            <div className="brand-name">
              OnlineVakeel<span className="tld">.com</span>
            </div>
            <span className="brand-tagline">AI Legal Counsel · Advocate Network · India</span>
          </div>
        </Link>

        <nav className="nav-tabs">
          {(["citizen", "advocate", "corpus"] as MainTab[]).map(tab => (
            <button
              key={tab}
              className={`nav-tab ${mainTab === tab ? "active" : ""}`}
              onClick={() => setMainTab(tab)}
            >
              {tab === "citizen"   && <ShieldCheck size={14} />}
              {tab === "advocate"  && <UserCheck   size={14} />}
              {tab === "corpus"    && <BookOpen    size={14} />}
              {tab === "citizen"  ? "Legal Desk" : tab === "advocate" ? "Advocate Portal" : "Bare Acts Library"}
            </button>
          ))}
        </nav>

        <div className="nav-right">
          <button className="lang-btn" onClick={() => setLanguage(l => l === "en" ? "hi" : "en")}>
            {language === "en" ? "🇮🇳 हिन्दी" : "🇬🇧 English"}
          </button>
        </div>
      </header>

      {/* ── STEP TRACKER (Citizen only) ── */}
      {mainTab === "citizen" && (
        <div className="progress-track-wrap">
          <div className="progress-track">
            {[
              { n: 1, label: "Case Intake" },
              { n: 2, label: "Bare Act Research" },
              { n: 3, label: "Notice Draft" },
              { n: 4, label: "Advocate Handoff" },
            ].map(({ n, label }, idx, arr) => (
              <React.Fragment key={n}>
                <div className={`step-node ${stepStatus(n)}`}>
                  <div className="step-dot">
                    {step > n ? <Check size={12} /> : n}
                  </div>
                  <span className="step-node-label">{label}</span>
                </div>
                {idx < arr.length - 1 && <div className="step-line" />}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* ── MAIN CONTENT ── */}
      <main style={{ flex: 1 }}>

        {/* CITIZEN VIEW */}
        {mainTab === "citizen" && (
          <div className="workspace">

            {/* LEFT: CHAT */}
            <section className="chat-panel">
              {/* Chat header */}
              <div className="chat-header">
                <div className="chat-identity">
                  <div className="chat-avatar">
                    <Scale size={16} />
                    <span className="online-dot" />
                  </div>
                  <div>
                    <div className="chat-identity-name">OnlineVakeel Legal Counsel</div>
                    <div className="chat-identity-status">
                      <Sparkles size={11} style={{ color: "var(--brand)" }} />
                      Grounded in verified Indian Bare Acts
                    </div>
                  </div>
                </div>
                {caseId && (
                  <span className="session-badge">{caseId}</span>
                )}
              </div>

              {/* Messages */}
              <div className="chat-messages">
                {messages.map(msg => (
                  <div key={msg.id} className={`msg-row ${msg.sender === "user" ? "user-row" : ""}`}>
                    <div className={`msg-avatar ${msg.sender === "agent" ? "counsel-av" : "user-av"}`}>
                      {msg.sender === "agent" ? <Scale size={14} /> : "You"}
                    </div>
                    <div className="msg-body">
                      <div className="msg-meta">
                        {msg.sender === "agent" ? "OnlineVakeel AI Counsel" : "You"}
                        <span>·</span>
                        <span>{msg.timestamp}</span>
                      </div>
                      <div className={`bubble ${msg.sender === "agent" ? "counsel-bubble" : "user-bubble"}`}>
                        {msg.sender === "agent" ? (
                          <CounselMessage text={msg.text} clamp={msg.id !== "welcome"} />
                        ) : (
                          <span>{msg.text}</span>
                        )}
                        {msg.piiRedacted && Object.values(msg.piiRedacted).some((a: any) => a.length > 0) && (
                          <div className="pii-notice">
                            <Lock size={11} />
                            Personal identifiers masked under DPDP Act, 2023 prior to AI processing
                          </div>
                        )}
                        {msg.sender === "agent" && msg.id !== "welcome" && draftNotice && (
                          <button
                            className="view-notice-pill-btn"
                            onClick={() => setDossierTab("notice")}
                          >
                            <FileText size={12} />
                            <span>View Updated Legal Notice</span>
                            <ArrowRight size={11} />
                          </button>
                        )}
                        {msg.sender === "agent" && msg.locationMatched && (
                          <button
                            className="view-notice-pill-btn view-advocates-pill-btn"
                            onClick={() => {
                              if (msg.locationMatched?.city) {
                                setSelectedCityFilter(msg.locationMatched.city);
                                const matchItem = ALL_INDIAN_DISTRICTS.find(cat => 
                                  cat.district.toLowerCase() === msg.locationMatched!.city!.toLowerCase() ||
                                  msg.locationMatched!.city!.toLowerCase().includes(cat.district.toLowerCase())
                                );
                                if (matchItem) {
                                  setActiveDistrictItem(matchItem);
                                  setClientCourt(matchItem.districtCourt);
                                  setDistrictSearchQuery(`${matchItem.district}, ${matchItem.state}`);
                                  setSelectedStateFilter(matchItem.state);
                                }
                              }
                              setDossierTab("advocates");
                            }}
                            style={{ marginLeft: "0.4rem" }}
                          >
                            <Award size={12} />
                            <span>
                              🎯 View Advocates in {msg.locationMatched.court || msg.locationMatched.locality || msg.locationMatched.city}
                              {msg.locationMatched.count ? ` (${msg.locationMatched.count})` : ""}
                            </span>
                            <ArrowRight size={11} />
                          </button>
                        )}
                        {msg.sender === "agent" && msg.askLocation && (
                          <div className="msg-location-quick-chips">
                            <span className="msg-location-chip-title">📍 Quick-Select Your Practice City / Jurisdiction:</span>
                            <div className="msg-location-chip-list">
                              {[
                                "Delhi NCR", "Bengaluru", "Mumbai", "Pune",
                                "Hyderabad", "Chennai", "Jaipur", "Chandigarh", "Lucknow", "Kolkata"
                              ].map(city => (
                                <button
                                  key={city}
                                  type="button"
                                  className="msg-location-chip-btn"
                                  onClick={() => sendMessage(`I am located in ${city}`)}
                                >
                                  🏛️ {city}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {submitting && (
                  <div className="thinking-row">
                    <div className="msg-avatar counsel-av">
                      <Scale size={14} />
                    </div>
                    <div className="thinking-bubble">
                      <div className="typing-dots">
                        <span /><span /><span />
                      </div>
                      Researching applicable statutes and drafting response…
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Quick chips */}
              <div className="quick-chips">
                {QUICK_PROMPTS.map(p => (
                  <button key={p.label} className="chip" onClick={() => sendMessage(p.query)}>
                    {p.emoji} {p.label}
                  </button>
                ))}
              </div>

              {/* Input */}
              <div className="chat-input-area">
                <div className="chat-input-row">
                  <textarea
                    ref={textareaRef}
                    className="chat-textarea"
                    placeholder="Describe your legal situation — amount, dates, city, what happened…"
                    value={inputText}
                    onChange={handleTextareaChange}
                    onKeyDown={handleKeyDown}
                    rows={1}
                  />
                  <button
                    className="send-btn"
                    onClick={() => sendMessage()}
                    disabled={submitting || !inputText.trim()}
                  >
                    <Send size={15} />
                  </button>
                </div>
                <div className="input-hint">Press Enter to send · Shift+Enter for new line</div>
              </div>
            </section>

            {/* RIGHT: DOSSIER */}
            <aside className="dossier-panel">
              {/* Tab bar */}
              <div className="dossier-tabs">
                <button
                  className={`dossier-tab ${dossierTab === "remedies" ? "active" : ""}`}
                  onClick={() => setDossierTab("remedies")}
                >
                  <BookOpen size={14} />
                  Statutes
                  <span className="dossier-count">{remedies.length}</span>
                </button>
                <button
                  className={`dossier-tab ${dossierTab === "notice" ? "active" : ""}`}
                  onClick={() => setDossierTab("notice")}
                >
                  <FileText size={14} />
                  Legal Notice
                  {draftNotice && <span className="notice-updated-pill">Updated from chat</span>}
                </button>
                <button
                  className={`dossier-tab ${dossierTab === "advocates" ? "active" : ""}`}
                  onClick={() => setDossierTab("advocates")}
                >
                  <Award size={14} />
                  Advocates
                  <span className="dossier-count">{advocates.length}</span>
                  {locationUpdatedBanner && (
                    <span className="notice-updated-pill" style={{ background: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0" }}>
                      Updated
                    </span>
                  )}
                </button>
              </div>

              <div className="dossier-body">
                {locationUpdatedBanner && (
                  <div className="location-updated-banner">
                    <span>{locationUpdatedBanner}</span>
                    <button
                      className="location-updated-banner-close"
                      onClick={() => setLocationUpdatedBanner(null)}
                      title="Dismiss"
                    >
                      ✕
                    </button>
                  </div>
                )}

                {/* STATUTES TAB */}
                {dossierTab === "remedies" && (
                  <>
                    {remedies.length === 0 ? (
                      <div className="empty-state">
                        <div className="empty-icon">
                          <BookOpen size={24} />
                        </div>
                        <div className="empty-title">Applicable Statutes</div>
                        <p className="empty-desc">
                          Describe your legal situation on the left. The Research Agent will cite exact Bare Act sections, filing deadlines, and court-awarded penalties here.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--ink-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                            Applicable Bare Act Sections
                          </span>
                          <span style={{ fontSize: "0.68rem", color: "var(--emerald)", background: "var(--emerald-bg)", border: "1px solid var(--emerald-border)", padding: "0.18rem 0.55rem", borderRadius: "var(--radius-pill)", fontWeight: 700 }}>
                            {verifyBadge}
                          </span>
                        </div>
                        {remedies.map((r, i) => (
                          <div key={i} className="statute-card">
                            <div className="statute-act-pill">{r.act_name}</div>
                            <div className="statute-title">Section {r.section}: {r.title}</div>
                            <p className="statute-summary">{r.summary}</p>
                            <div className="statute-meta-row">
                              <span className="limitation-tag">
                                <Clock size={11} />
                                Limitation: {r.limitation}
                              </span>
                              {r.penalties_or_relief && (
                                <span className="relief-tag">
                                  <Check size={11} />
                                  {r.penalties_or_relief}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </>
                    )}
                  </>
                )}

                {/* NOTICE TAB */}
                {dossierTab === "notice" && (
                  <>
                    {!draftNotice ? (
                      <div className="empty-state">
                        <div className="empty-icon">
                          <FileText size={24} />
                        </div>
                        <div className="empty-title">Pre-Litigation Notice Drafter</div>
                        <p className="empty-desc">
                          Once your case details are submitted, the Drafting Agent will generate a formal statutory notice formatted to Indian procedural law.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="notice-toolbar">
                          <div>
                            <span className="notice-toolbar-label">15-Day Statutory Legal Demand Notice</span>
                            {draftNotice.last_updated && (
                              <div style={{ fontSize: "0.72rem", color: "var(--ink-muted)", marginTop: "0.15rem" }}>
                                Synchronized with chat · Last updated {draftNotice.last_updated}
                              </div>
                            )}
                          </div>
                          <div className="notice-actions">
                            <button className="action-btn" onClick={copyNotice} title="Copy Notice Text">
                              {copiedNotice ? <Check size={12} style={{ color: "var(--emerald)" }} /> : <Copy size={12} />}
                              {copiedNotice ? "Copied" : "Copy"}
                            </button>
                            <button className="action-btn action-btn-primary" onClick={downloadNoticePdf} title="Download Formal PDF File">
                              <Download size={12} />
                              Download PDF
                            </button>
                            <button className="action-btn" onClick={printNotice} title="Print Notice">
                              <Printer size={12} />
                              Print
                            </button>
                          </div>
                        </div>

                        {draftNotice.incorporated_facts && draftNotice.incorporated_facts.length > 0 && (
                          <div className="notice-facts-badge-row">
                            <span className="facts-badge-title">Incorporated from Chat:</span>
                            {draftNotice.incorporated_facts.map((fact: string, idx: number) => (
                              <span key={idx} className="facts-badge-pill">
                                ✓ {fact}
                              </span>
                            ))}
                          </div>
                        )}
                        <div className="notice-document" id="printable-legal-notice">
                          <div className="notice-letterhead">
                            <Scale size={20} style={{ color: "rgba(255,255,255,0.75)", marginBottom: "0.4rem" }} />
                            <div className="notice-letterhead-title">Chambers of Advocates & Legal Counsel</div>
                            <div className="notice-letterhead-sub">High Court & District Courts Practice · India</div>
                          </div>
                          <div className="notice-body-text md-notice">
                            <ReactMarkdown>{draftNotice.content}</ReactMarkdown>
                          </div>
                        </div>
                        <div className="notice-serving-tip">
                          💡 <strong>How to serve:</strong> Print on legal paper, have it signed by an enrolled advocate, and dispatch via <strong>Registered Post A.D. or Speed Post</strong>. Retain the postal receipt as conclusive evidence of service.
                        </div>
                      </>
                    )}
                  </>
                )}

                {/* ADVOCATES TAB */}
                {dossierTab === "advocates" && (
                  <>
                    {/* Search & Jurisdiction Toolbar */}
                    <div className="adv-search-toolbar">
                      <div className="adv-search-input-wrap">
                        <Search size={14} style={{ color: "var(--ink-muted)", flexShrink: 0 }} />
                        <input
                          type="text"
                          className="adv-search-input"
                          placeholder="Search advocates by name, court, office, or legal specialty..."
                          value={advSearchQuery}
                          onChange={e => setAdvSearchQuery(e.target.value)}
                        />
                        {advSearchQuery && (
                          <button
                            onClick={() => setAdvSearchQuery("")}
                            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-muted)" }}
                          >
                            <X size={12} />
                          </button>
                        )}
                      </div>

                      {/* Quick Metro Jurisdictions */}
                      <div className="adv-city-chips-wrap">
                        <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "var(--ink-muted)", textTransform: "uppercase", marginRight: "0.2rem" }}>
                          Quick Hubs:
                        </span>
                        {[
                          { id: "all", label: "All Districts" },
                          { id: "New Delhi", label: "📍 Delhi Central" },
                          { id: "South Delhi", label: "📍 Saket (Delhi)" },
                          { id: "Bengaluru Urban", label: "📍 Bengaluru" },
                          { id: "Mumbai City", label: "📍 Mumbai Fort" },
                          { id: "Pune", label: "📍 Pune" },
                          { id: "Hyderabad", label: "📍 Hyderabad" },
                          { id: "Gautam Buddha Nagar", label: "📍 Noida / Surajpur" },
                          { id: "Gurugram", label: "📍 Gurugram" },
                          { id: "Lucknow", label: "📍 Lucknow" },
                          { id: "Chandigarh", label: "📍 Chandigarh" },
                          { id: "Jaipur", label: "📍 Jaipur" }
                        ].map(c => (
                          <button
                            key={c.id}
                            className={`adv-city-chip ${selectedCityFilter.toLowerCase() === c.id.toLowerCase() ? "active" : ""}`}
                            onClick={() => {
                              setSelectedCityFilter(c.id);
                              const matchItem = ALL_INDIAN_DISTRICTS.find(cat => cat.district.toLowerCase() === c.id.toLowerCase());
                              if (matchItem) {
                                setActiveDistrictItem(matchItem);
                                setClientCourt(matchItem.districtCourt);
                                setDistrictSearchQuery(`${matchItem.district}, ${matchItem.state}`);
                              } else if (c.id === "all") {
                                setActiveDistrictItem(null);
                                setClientCourt("");
                                setDistrictSearchQuery("");
                              }
                            }}
                          >
                            {c.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* 📍 Interactive Intuitive District & Court Selector (All 754 Districts) */}
                    <div className="client-loc-matcher">
                      <div className="client-loc-header">
                        <span className="client-loc-title">
                          <MapPin size={13} /> District Court & Jurisdiction Locator (All 754 Districts)
                        </span>
                        {detectedCity && (
                          <span style={{ fontSize: "0.68rem", color: "var(--brand)", fontWeight: 600 }}>
                            📍 Detected from chat: <strong>{detectedCity}</strong>
                          </span>
                        )}
                      </div>

                      {/* Search Bar + State Filter + Autocomplete Popover */}
                      <div className="intuitive-district-selector">
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: "0.5rem", marginBottom: "0.5rem" }}>
                          <div style={{ position: "relative" }}>
                            <div className="district-search-bar">
                              <Search size={14} style={{ color: "var(--ink-muted)", flexShrink: 0 }} />
                              <input
                                type="text"
                                className="district-search-input"
                                placeholder="🔍 Search district or court (e.g. Gautam Buddha Nagar, Saket, Ernakulam, Satara...)"
                                value={districtSearchQuery}
                                onChange={(e) => {
                                  setDistrictSearchQuery(e.target.value);
                                  setShowDistrictDropdown(true);
                                }}
                                onFocus={() => setShowDistrictDropdown(true)}
                              />
                              {districtSearchQuery && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    setDistrictSearchQuery("");
                                    setShowDistrictDropdown(false);
                                  }}
                                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-muted)", padding: "2px" }}
                                >
                                  <X size={14} />
                                </button>
                              )}
                            </div>

                            {/* Dropdown Popover */}
                            {showDistrictDropdown && (
                              <div className="district-autocomplete-dropdown" ref={districtDropdownRef}>
                                <div className="district-dropdown-header">
                                  <div className="district-dropdown-title">
                                    <Scale size={13} style={{ color: "var(--gold)" }} />
                                    <span>754 OFFICIAL DISTRICT &amp; SESSIONS COURTS</span>
                                  </div>
                                  <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                                    {(() => {
                                      const q = districtSearchQuery.trim().toLowerCase();
                                      const stateFilt = selectedStateFilter;
                                      const count = ALL_INDIAN_DISTRICTS.filter(d => {
                                        const matchState = stateFilt === "all" || d.state === stateFilt;
                                        const matchQ = !q ||
                                          d.district.toLowerCase().includes(q) ||
                                          d.districtCourt.toLowerCase().includes(q) ||
                                          d.state.toLowerCase().includes(q) ||
                                          d.subCourts.some(sc => sc.toLowerCase().includes(q));
                                        return matchState && matchQ;
                                      }).length;
                                      return (
                                        <span className="district-dropdown-count">
                                          {count} Courts
                                        </span>
                                      );
                                    })()}
                                    <button
                                      type="button"
                                      onClick={() => setShowDistrictDropdown(false)}
                                      style={{ background: "none", border: "none", fontSize: "0.75rem", color: "rgba(255,255,255,0.75)", cursor: "pointer", fontWeight: 700, padding: "2px 4px" }}
                                      title="Close dropdown"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                </div>
                                <div className="district-dropdown-scroll">
                                  {(() => {
                                    const q = districtSearchQuery.trim().toLowerCase();
                                    const stateFilt = selectedStateFilter;
                                    const filteredDistricts = ALL_INDIAN_DISTRICTS.filter(d => {
                                      const matchState = stateFilt === "all" || d.state === stateFilt;
                                      const matchQ = !q ||
                                        d.district.toLowerCase().includes(q) ||
                                        d.districtCourt.toLowerCase().includes(q) ||
                                        d.state.toLowerCase().includes(q) ||
                                        d.subCourts.some(sc => sc.toLowerCase().includes(q));
                                      return matchState && matchQ;
                                    }).slice(0, 45);

                                    if (filteredDistricts.length === 0) {
                                      return (
                                        <div style={{ padding: "1.25rem", fontSize: "0.78rem", color: "var(--ink-muted)", textAlign: "center" }}>
                                          No district found matching &quot;{districtSearchQuery}&quot;. Try searching another spelling or selecting your State.
                                        </div>
                                      );
                                    }

                                    return filteredDistricts.map((d, i) => (
                                      <div
                                        key={i}
                                        className="district-autocomplete-item"
                                        onClick={() => {
                                          setActiveDistrictItem(d);
                                          setSelectedCityFilter(d.district);
                                          setClientCourt(d.districtCourt);
                                          setShowDistrictDropdown(false);
                                          setDistrictSearchQuery(`${d.district}, ${d.state}`);
                                        }}
                                      >
                                        <div className="district-item-main">
                                          <div className="district-item-name">
                                            <span>{d.district}</span>
                                            <span className="district-state-badge">{d.state}</span>
                                          </div>
                                          <div className="district-item-court">
                                            <Building size={11} style={{ flexShrink: 0 }} />
                                            <span>{d.districtCourt}</span>
                                          </div>
                                          {d.subCourts.length > 0 && (
                                            <div className="district-subcourts-preview">
                                              {d.subCourts.slice(0, 3).map((sc, scIdx) => (
                                                <span key={scIdx} className="district-subcourt-mini-chip">
                                                  {sc}
                                                </span>
                                              ))}
                                              {d.subCourts.length > 3 && (
                                                <span className="district-subcourt-mini-chip">+{d.subCourts.length - 3} more</span>
                                              )}
                                            </div>
                                          )}
                                        </div>
                                        <div className="district-item-action">
                                          <ChevronRight size={14} />
                                        </div>
                                      </div>
                                    ));
                                  })()}
                                </div>
                              </div>
                            )}
                          </div>

                          {/* State Filter Dropdown */}
                          <div>
                            <select
                              className="client-loc-select"
                              style={{ height: "38px" }}
                              value={selectedStateFilter}
                              onChange={(e) => {
                                setSelectedStateFilter(e.target.value);
                                setShowDistrictDropdown(true);
                              }}
                            >
                              <option value="all">🇮🇳 All 36 States &amp; UTs</option>
                              {INDIAN_STATES.map((s, idx) => (
                                <option key={idx} value={s}>{s}</option>
                              ))}
                            </select>
                          </div>
                        </div>

                        {/* Active Selected District Card */}
                        {activeDistrictItem && (
                          <div className="active-district-card">
                            <div className="active-district-card-top">
                              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                                <div className="active-district-seal">
                                  <Scale size={18} />
                                </div>
                                <div>
                                  <div className="active-district-title">
                                    {activeDistrictItem.district} District Court Jurisdiction
                                  </div>
                                  <div className="active-district-state">
                                    {activeDistrictItem.state} · Principal Judicial District
                                  </div>
                                </div>
                              </div>
                              <button
                                type="button"
                                className="active-district-clear"
                                onClick={() => {
                                  setActiveDistrictItem(null);
                                  setSelectedCityFilter("all");
                                  setClientCourt("");
                                  setDistrictSearchQuery("");
                                }}
                                title="Clear or switch district court"
                              >
                                <X size={12} /> Change District
                              </button>
                            </div>

                            <div className="active-district-court-box">
                              <div className="active-district-court-name">
                                🏛️ <strong>Principal Court Complex:</strong> {activeDistrictItem.districtCourt}
                              </div>
                              {activeDistrictItem.subCourts.length > 0 && (
                                <div style={{ marginTop: "0.45rem" }}>
                                  <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "var(--ink-secondary)", marginBottom: "0.3rem" }}>
                                    SUB-COURT TALUKAS &amp; MAGISTRATE COMPLEXES:
                                  </div>
                                  <div className="active-district-subcourts">
                                    {activeDistrictItem.subCourts.map((sc, i) => {
                                      const isCourtActive = clientCourt.toLowerCase() === sc.toLowerCase();
                                      return (
                                        <button
                                          key={i}
                                          type="button"
                                          className={`active-subcourt-pill ${isCourtActive ? "selected" : ""}`}
                                          onClick={() => setClientCourt(sc)}
                                        >
                                          {isCourtActive ? "✓ " : "+ "}{sc}
                                        </button>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Locality & Court Override Inputs */}
                        <div className="client-loc-grid" style={{ marginTop: "0.5rem" }}>
                          <div>
                            <label style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--ink-secondary)", display: "block", marginBottom: 3 }}>
                              YOUR LOCALITY / SECTOR / COLONY:
                            </label>
                            <input
                              type="text"
                              className="client-loc-input"
                              placeholder="e.g. Sector 62, Indiranagar, Connaught Place, Koramangala..."
                              value={clientLocality}
                              onChange={e => setClientLocality(e.target.value)}
                            />
                          </div>

                          <div>
                            <label style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--ink-secondary)", display: "block", marginBottom: 3 }}>
                              ACTIVE MATCHED DISTRICT COURT:
                            </label>
                            <input
                              type="text"
                              className="client-loc-input"
                              placeholder="e.g. Saket District Court, Mayo Hall Court, Tis Hazari Court..."
                              value={clientCourt}
                              onChange={e => setClientCourt(e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Filter and Rank Advocates with Exact Location Matching */}
                    {(() => {
                      const query = advSearchQuery.trim().toLowerCase();
                      const cityFilt = selectedCityFilter.toLowerCase();
                      const userLoc = clientLocality.trim().toLowerCase();
                      const userCourt = clientCourt.trim().toLowerCase();
                      
                      const filtered = advocates.filter(adv => {
                        const matchQuery = !query || 
                          adv.name.toLowerCase().includes(query) ||
                          adv.bio.toLowerCase().includes(query) ||
                          (adv.district_court && adv.district_court.toLowerCase().includes(query)) ||
                          (adv.office_location && adv.office_location.toLowerCase().includes(query)) ||
                          adv.courts.some(c => c.toLowerCase().includes(query)) ||
                          adv.practice_areas.some(p => p.toLowerCase().includes(query));

                        const isNcrAllFilt = cityFilt === "delhi ncr";
                        const isAdvNcr = (
                          adv.city.toLowerCase().includes("delhi") || 
                          adv.city.toLowerCase().includes("gautam") || 
                          adv.city.toLowerCase().includes("gurugram") || 
                          adv.city.toLowerCase().includes("ghaziabad") ||
                          adv.city.toLowerCase().includes("faridabad")
                        );

                        const matchCity = cityFilt === "all" ||
                          adv.city.toLowerCase().includes(cityFilt) ||
                          cityFilt.includes(adv.city.toLowerCase()) ||
                          adv.state.toLowerCase() === cityFilt ||
                          (adv.district_court && adv.district_court.toLowerCase().includes(cityFilt)) ||
                          (userCourt && (adv.district_court?.toLowerCase().includes(userCourt) || adv.courts.some(c => c.toLowerCase().includes(userCourt)))) ||
                          (isNcrAllFilt && isAdvNcr);

                        return matchQuery && matchCity;
                      });

                      let displayList = filtered;
                      let isJurisdictionFallback = false;
                      if (filtered.length === 0 && advocates.length > 0) {
                        // Graceful State or Regional Jurisdiction Fallback
                        const stateMatches = advocates.filter(adv => 
                          activeDistrictItem && adv.state.toLowerCase() === activeDistrictItem.state.toLowerCase()
                        );
                        if (stateMatches.length > 0) {
                          displayList = stateMatches;
                          isJurisdictionFallback = true;
                        } else {
                          displayList = advocates.slice(0, 6);
                          isJurisdictionFallback = true;
                        }
                      }

                      if (displayList.length === 0) {
                        return (
                          <div className="empty-state">
                            <div className="empty-icon">
                              <Award size={24} />
                            </div>
                            <div className="empty-title">No Advocates Found for Selected Location</div>
                            <p className="empty-desc">
                              Try selecting &quot;All Districts&quot; or clearing your district court / locality filter.
                            </p>
                            <button
                              className="action-btn"
                              style={{ marginTop: "0.75rem" }}
                              onClick={() => { setSelectedCityFilter("all"); setActiveDistrictItem(null); setAdvSearchQuery(""); setClientLocality(""); setClientCourt(""); setDistrictSearchQuery(""); }}
                            >
                              Reset Location Filters
                            </button>
                          </div>
                        );
                      }

                      // Dynamic scoring for court, office, and case match
                      const scoredAdvocates = displayList.map(adv => {
                        let score = 0;
                        const advCourt = (adv.district_court || "").toLowerCase();
                        const advCourtsAll = adv.courts.map(c => c.toLowerCase()).join(" ");
                        const advOffice = (adv.office_location || "").toLowerCase();
                        const advCity = adv.city.toLowerCase();

                        const isCourtMatch = Boolean(userCourt && (advCourt.includes(userCourt) || userCourt.includes(advCourt) || advCourtsAll.includes(userCourt)));
                        const isLocalityMatch = Boolean(userLoc && (advOffice.includes(userLoc) || userLoc.includes(advOffice) || advCity.includes(userLoc)));
                        const isCityMatch = Boolean(cityFilt !== "all" && (advCity.includes(cityFilt) || cityFilt.includes(advCity)));
                        const isDomainMatch = adv.practice_areas.includes(currentCategory);

                        if (isCourtMatch) score += 50;
                        if (isLocalityMatch) score += 40;
                        if (isCityMatch) score += 25;
                        if (isDomainMatch) score += 15;
                        score += (adv.rating || 4.5);

                        return {
                          ...adv,
                          score,
                          isCourtMatch,
                          isLocalityMatch,
                          isCityMatch,
                          isDomainMatch
                        };
                      });

                      scoredAdvocates.sort((a, b) => b.score - a.score);

                      return (
                        <>
                          {isJurisdictionFallback && (
                            <div style={{
                              background: "rgba(184, 134, 11, 0.08)",
                              border: "1px solid rgba(184, 134, 11, 0.3)",
                              borderRadius: "8px",
                              padding: "0.6rem 0.85rem",
                              marginBottom: "0.85rem",
                              fontSize: "0.76rem",
                              color: "var(--brand)",
                              display: "flex",
                              alignItems: "center",
                              gap: "0.5rem"
                            }}>
                              <Building size={14} style={{ flexShrink: 0 }} />
                              <span>Showing verified advocates with High Court &amp; Regional jurisdiction practicing for <strong>{activeDistrictItem?.district || selectedCityFilter}</strong> ({activeDistrictItem?.state || "State Jurisdiction"}).</span>
                            </div>
                          )}

                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.85rem" }}>
                            <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "var(--ink-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                              Verified Enrolled Advocates ({scoredAdvocates.length})
                            </span>
                            {(userCourt || userLoc || selectedCityFilter !== "all") && (
                              <span style={{ fontSize: "0.7rem", color: "var(--brand)", fontWeight: 650 }}>
                                🎯 Matching {userCourt || userLoc || selectedCityFilter}
                              </span>
                            )}
                          </div>

                          {scoredAdvocates.map(adv => (
                            <div key={adv.id} className="advocate-card">
                              {/* Location & Specialty Badges */}
                              {adv.isCourtMatch && adv.isLocalityMatch ? (
                                <div className="adv-exact-match-badge">
                                  <Sparkles size={11} /> 🎯 100% Exact Court & Chamber Proximity Match
                                </div>
                              ) : adv.isCourtMatch ? (
                                <div className="adv-exact-match-badge">
                                  <Scale size={11} /> 🏛️ Exact District Court Match: {adv.district_court}
                                </div>
                              ) : adv.isLocalityMatch ? (
                                <div className="adv-exact-match-badge">
                                  <MapPin size={11} /> 🏢 Nearest Chamber in {adv.office_location}
                                </div>
                              ) : adv.isCityMatch ? (
                                <div className="adv-best-match-pill">
                                  <MapPin size={10} /> Local Court Jurisdiction · {adv.city}
                                </div>
                              ) : adv.isDomainMatch ? (
                                <div className="adv-best-match-pill">
                                  <Sparkles size={10} /> Specialist in {currentCategory.replace("_", " ")}
                                </div>
                              ) : null}

                              <div className="advocate-card-top">
                                <div className="advocate-name-block">
                                  <div className="advocate-name">{adv.name}</div>
                                  <div className="advocate-bar">
                                    <Building size={11} style={{ display: "inline", marginRight: 3 }} />
                                    {adv.bar_council_id} · {adv.experience_years} yrs standing
                                  </div>
                                </div>
                                <div>
                                  <div className="advocate-fee">₹{adv.consult_fee}</div>
                                  <div className="advocate-fee-label">/ consult</div>
                                </div>
                              </div>

                              {/* Prominent District Court and Office Location Pills */}
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginBottom: "0.6rem" }}>
                                <span className="adv-court-pill" title="District Court Jurisdiction">
                                  <Scale size={11} />
                                  <strong>Court:</strong> {adv.district_court || adv.courts[0] || "District Court"}
                                </span>
                                <span className="adv-office-pill" title="Physical Chamber Address">
                                  <Building size={11} />
                                  <strong>Office:</strong> {adv.office_location || `${adv.city} Court Chambers`}
                                </span>
                              </div>

                              {/* ⭐ Advocate Rating & Verified Client Review Action */}
                              <div className="advocate-rating-row">
                                <button
                                  type="button"
                                  className="advocate-rating-pill"
                                  onClick={() => openReviewsDrawer(adv)}
                                  title="View verified client reviews and ratings"
                                >
                                  <Star size={13} fill="#f59e0b" color="#f59e0b" />
                                  <span className="rating-score">{adv.rating ? adv.rating.toFixed(1) : "5.0"}</span>
                                  <span className="rating-count">({adv.reviews || 0} reviews)</span>
                                </button>
                                
                                {paidConsultations.some(p => p.advocateId === adv.id) ? (
                                  <button
                                    type="button"
                                    className="rate-adv-btn active-rate-btn"
                                    onClick={() => openRatingModal(adv)}
                                    title="Verified Client: Rate this advocate"
                                  >
                                    <Star size={12} fill="currentColor" />
                                    <span>Rate Consultation (Verified Client)</span>
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    className="rate-adv-btn locked-rate-btn"
                                    onClick={() => setRatingLockedModalAdvocate(adv)}
                                    title="Ratings restricted to clients who have completed payment"
                                  >
                                    <Lock size={11} />
                                    <span>Rate Advocate (Paid Clients Only)</span>
                                  </button>
                                )}
                              </div>

                              <div className="advocate-tags">
                                {adv.practice_areas.map((p, i) => (
                                  <span key={i} className="adv-tag">{p.replace("_", " ")}</span>
                                ))}
                              </div>
                              <p className="advocate-bio">{adv.bio}</p>

                              <button
                                className="handoff-btn"
                                onClick={() => openBookingModal(adv)}
                              >
                                <PhoneCall size={14} />
                                {booking[adv.id] || "Connect & Book Consultation"}
                              </button>
                            </div>
                          ))}
                        </>
                      );
                    })()}
                  </>
                )}
              </div>
            </aside>
          </div>
        )}

        {/* ADVOCATE PORTAL VIEW */}
        {mainTab === "advocate" && (
          <div className="portal-wrapper">
            {!advocateUser ? (
              /* Advocate Authentication Hub (Login or Register) */
              <div className="adv-auth-container">
                <div className="adv-auth-header">
                  <Scale size={32} style={{ margin: "0 auto", color: "#fbbf24" }} />
                  <h2 className="adv-auth-title">Advocate Practice Portal</h2>
                  <p className="adv-auth-sub">
                    Enrolled Bar Council Advocate Sign In & Verified Onboarding
                  </p>
                </div>

                <div className="adv-auth-tabs">
                  <button
                    className={`adv-auth-tab ${advAuthMode === "login" ? "active" : ""}`}
                    onClick={() => { setAdvAuthMode("login"); setAdvAuthError(""); }}
                  >
                    <LogIn size={15} style={{ display: "inline", marginRight: 6 }} />
                    Advocate Sign In
                  </button>
                  <button
                    className={`adv-auth-tab ${advAuthMode === "register" ? "active" : ""}`}
                    onClick={() => { setAdvAuthMode("register"); setAdvAuthError(""); }}
                  >
                    <UserPlus size={15} style={{ display: "inline", marginRight: 6 }} />
                    Register as Advocate
                  </button>
                </div>

                <div className="adv-auth-body">
                  {advAuthError && (
                    <div style={{ background: "#fef2f2", border: "1px solid #fecaca", padding: "0.75rem 1rem", borderRadius: "6px", color: "#b91c1c", fontSize: "0.82rem", marginBottom: "1.25rem" }}>
                      ⚠️ {advAuthError}
                    </div>
                  )}

                  {advAuthMode === "login" ? (
                    <div>
                      {/* One-Click Quick Logins for Testing */}
                      <div className="adv-quick-login-box">
                        <div className="adv-quick-login-title">
                          ⚡ Instant Demo Logins (1-Click Verification):
                        </div>
                        <div className="adv-quick-login-chips">
                          {[
                            { name: "Adv. Rajesh Sharma (Delhi Bar)", id: "rajesh.sharma@delhibar.org" },
                            { name: "Adv. Priya Iyer (Karnataka Bar)", id: "priya.iyer@karnatakabar.org" },
                            { name: "Adv. Amit Patel (Bombay Bar)", id: "amit.patel@bombaybar.org" },
                            { name: "Adv. Vikram Malhotra (Delhi Bar)", id: "vikram.malhotra@delhibar.org" }
                          ].map(demo => (
                            <button
                              key={demo.id}
                              type="button"
                              className="adv-quick-chip"
                              onClick={() => {
                                setAdvLoginForm({ identifier: demo.id, password: "vakeel123" });
                                handleAdvLogin(demo.id);
                              }}
                            >
                              ✓ {demo.name}
                            </button>
                          ))}
                        </div>
                      </div>

                      <form onSubmit={(e) => { e.preventDefault(); handleAdvLogin(); }}>
                        <div className="adv-form-group">
                          <label className="adv-form-label">Bar Council Enrollment ID or Registered Email</label>
                          <input
                            type="text"
                            required
                            className="adv-form-input"
                            placeholder="e.g. D/1420/2012 or rajesh.sharma@delhibar.org"
                            value={advLoginForm.identifier}
                            onChange={e => setAdvLoginForm(prev => ({ ...prev, identifier: e.target.value }))}
                          />
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Password</label>
                          <input
                            type="password"
                            className="adv-form-input"
                            placeholder="Enter password"
                            value={advLoginForm.password}
                            onChange={e => setAdvLoginForm(prev => ({ ...prev, password: e.target.value }))}
                          />
                        </div>

                        <button type="submit" className="adv-submit-btn" disabled={advAuthLoading}>
                          {advAuthLoading ? "Verifying Credentials..." : "Sign In to Advocate Chamber"}
                        </button>
                      </form>
                    </div>
                  ) : (
                    /* Advocate Registration Form */
                    <form onSubmit={handleAdvRegister}>
                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">Full Legal Name</label>
                          <input
                            type="text"
                            required
                            className="adv-form-input"
                            placeholder="Adv. Ananya Sharma"
                            value={advRegForm.name}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, name: e.target.value }))}
                          />
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Bar Council Enrollment Number</label>
                          <input
                            type="text"
                            required
                            className="adv-form-input"
                            placeholder="e.g. D/3420/2018 or MAH/4120/2015"
                            value={advRegForm.bar_council_id}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, bar_council_id: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">State Bar Council</label>
                          <select
                            className="adv-form-select"
                            value={advRegForm.state_bar_council}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, state_bar_council: e.target.value }))}
                          >
                            <option value="Bar Council of Delhi">Bar Council of Delhi</option>
                            <option value="Karnataka State Bar Council">Karnataka State Bar Council</option>
                            <option value="Bar Council of Maharashtra & Goa">Bar Council of Maharashtra & Goa</option>
                            <option value="Bar Council of Uttar Pradesh">Bar Council of Uttar Pradesh</option>
                            <option value="Bar Council of Punjab & Haryana">Bar Council of Punjab & Haryana</option>
                            <option value="Bar Council of Telangana">Bar Council of Telangana</option>
                            <option value="Bar Council of Rajasthan">Bar Council of Rajasthan</option>
                            <option value="Bar Council of Tamil Nadu">Bar Council of Tamil Nadu</option>
                          </select>
                        </div>
                      </div>

                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">Primary Practice District / Court Jurisdiction (754 Districts)</label>
                          <select
                            className="adv-form-select"
                            value={advRegForm.city}
                            onChange={(e) => {
                              const selected = e.target.value;
                              const matched = ALL_INDIAN_DISTRICTS.find(d => d.district.toLowerCase() === selected.toLowerCase());
                              setAdvRegForm(prev => ({
                                ...prev,
                                city: selected,
                                state: matched?.state || prev.state,
                                district_court: matched?.districtCourt || prev.district_court
                              }));
                            }}
                          >
                            {ALL_INDIAN_DISTRICTS.map((d, i) => (
                              <option key={i} value={d.district}>
                                {d.district} ({d.state}) — {d.districtCourt}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Primary District Court</label>
                          <input
                            type="text"
                            required
                            className="adv-form-input"
                            placeholder="e.g. Saket District Court, Mayo Hall Court, Tis Hazari Court"
                            value={advRegForm.district_court}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, district_court: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">Chamber / Office Location (Physical Address)</label>
                          <input
                            type="text"
                            required
                            className="adv-form-input"
                            placeholder="e.g. Chamber No. 412, Lawyers Block, Saket District Court Complex"
                            value={advRegForm.office_location}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, office_location: e.target.value }))}
                          />
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Other Practicing Courts (Comma separated)</label>
                          <input
                            type="text"
                            className="adv-form-input"
                            placeholder="e.g. High Court, RERA Tribunal, NCLT"
                            value={advRegForm.courts}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, courts: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">Years of Standing at Bar</label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            className="adv-form-input"
                            value={advRegForm.experience_years}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, experience_years: Number(e.target.value) }))}
                          />
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Consultation Fee (₹ / session)</label>
                          <input
                            type="number"
                            min="500"
                            step="100"
                            className="adv-form-input"
                            value={advRegForm.consult_fee}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, consult_fee: Number(e.target.value) }))}
                          />
                        </div>
                      </div>

                      <div className="adv-form-grid-2">
                        <div className="adv-form-group">
                          <label className="adv-form-label">Official Email</label>
                          <input
                            type="email"
                            required
                            className="adv-form-input"
                            placeholder="advocate@bar.org"
                            value={advRegForm.email}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, email: e.target.value }))}
                          />
                        </div>

                        <div className="adv-form-group">
                          <label className="adv-form-label">Contact Phone / Chamber Mobile</label>
                          <input
                            type="tel"
                            className="adv-form-input"
                            placeholder="+91 98765 43210"
                            value={advRegForm.phone}
                            onChange={e => setAdvRegForm(prev => ({ ...prev, phone: e.target.value }))}
                          />
                        </div>
                      </div>

                      <div className="adv-form-group">
                        <label className="adv-form-label">Chamber Bio & Experience Summary</label>
                        <textarea
                          rows={2}
                          className="adv-form-textarea"
                          placeholder="Brief description of trial court litigation experience, statutory practice, and specialized chambers."
                          value={advRegForm.bio}
                          onChange={e => setAdvRegForm(prev => ({ ...prev, bio: e.target.value }))}
                        />
                      </div>

                      <button type="submit" className="adv-submit-btn" disabled={advAuthLoading}>
                        {advAuthLoading ? "Registering with Bar Registry..." : "Complete Bar Council Registration"}
                      </button>
                    </form>
                  )}
                </div>
              </div>
            ) : (
              /* Logged-In Advocate Dashboard */
              <div>
                <div className="portal-header">
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <h2 className="portal-title">{advocateUser.name}</h2>
                      <span className="status-badge">✓ Bar Council Verified Counsel</span>
                    </div>
                    <p className="portal-sub">
                      {advocateUser.bar_council_id} · {advocateUser.city}, {advocateUser.state} · Courts: {advocateUser.courts.join(", ")} · Fee: ₹{advocateUser.consult_fee}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "0.6rem" }}>
                    <button
                      className="action-btn"
                      onClick={() => fetchLeads(advocateUser.id)}
                      title="Refresh Leads"
                    >
                      <Clock size={12} /> Refresh
                    </button>
                    <button
                      className="action-btn"
                      onClick={handleAdvLogout}
                      style={{ color: "var(--rose)" }}
                    >
                      <LogOut size={12} /> Sign Out
                    </button>
                  </div>
                </div>

                <div className="portal-grid">
                  {/* Lead list */}
                  <div className="card-box">
                    <div className="card-box-title">
                      <Clock size={15} />
                      Incoming Client Consultation Handoffs ({leads.length})
                    </div>
                    {leads.length === 0 ? (
                      <div style={{ padding: "2rem", textAlign: "center", color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                        No new consultation handoffs yet. As citizens in {advocateUser.city} request counsel, they will appear here in real-time.
                      </div>
                    ) : (
                      leads.map(lead => (
                        <div
                          key={lead.id}
                          className={`lead-item ${selectedLead?.id === lead.id ? "selected" : ""}`}
                          onClick={() => setSelectedLead(lead)}
                        >
                          <div className="lead-top">
                            <span className="lead-id">{lead.case_id}</span>
                            <span className={`lead-urgency ${lead.urgency}`}>{lead.urgency}</span>
                          </div>
                          <div className="lead-title">{lead.title}</div>
                          <div className="lead-meta">
                            <span>
                              <MapPin size={11} style={{ display: "inline", marginRight: 2 }} />
                              {lead.city}
                            </span>
                            <span style={{ color: lead.status === "accepted" ? "var(--emerald)" : "var(--brand)", fontWeight: 600 }}>
                              {lead.status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Lead detail */}
                  {selectedLead && (
                    <div className="card-box">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.6rem" }}>
                        <div>
                          <div className="lead-detail-title">{selectedLead.title}</div>
                          <div style={{ fontSize: "0.74rem", color: "var(--ink-muted)", marginTop: "2px" }}>
                            Submitted {selectedLead.created_at} · Jurisdiction: {selectedLead.city}
                          </div>
                        </div>
                        <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "var(--brand)", background: "var(--brand-soft)", border: "1px solid var(--brand-border)", padding: "0.18rem 0.5rem", borderRadius: "4px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                          {selectedLead.category.replace("_", " ")}
                        </span>
                      </div>

                      {/* Consultation Mode, Time Slot & Client Location Pill */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", margin: "0.75rem 0" }}>
                        <span style={{ fontSize: "0.72rem", background: "var(--bg)", border: "1px solid var(--border)", padding: "0.25rem 0.6rem", borderRadius: "4px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                          {selectedLead.preferred_mode === "video" ? <Video size={12} /> : selectedLead.preferred_mode === "chamber" ? <Building size={12} /> : <Phone size={12} />}
                          Mode: <strong>{selectedLead.preferred_mode ? selectedLead.preferred_mode.toUpperCase() : "PHONE CALL"}</strong>
                        </span>
                        <span style={{ fontSize: "0.72rem", background: "var(--bg)", border: "1px solid var(--border)", padding: "0.25rem 0.6rem", borderRadius: "4px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                          <Calendar size={12} />
                          Slot: <strong>{selectedLead.preferred_slot || "Today (Next Available Slot)"}</strong>
                        </span>
                        {selectedLead.client_locality && (
                          <span style={{ fontSize: "0.72rem", background: "#eff6ff", border: "1px solid #bfdbfe", color: "#1e3a8a", padding: "0.25rem 0.6rem", borderRadius: "4px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                            <MapPin size={12} />
                            Client Locality: <strong>{selectedLead.client_locality}</strong>
                          </span>
                        )}
                        {selectedLead.preferred_court && (
                          <span style={{ fontSize: "0.72rem", background: "#fef3c7", border: "1px solid #fde68a", color: "#92400e", padding: "0.25rem 0.6rem", borderRadius: "4px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                            <Scale size={12} />
                            Court: <strong>{selectedLead.preferred_court}</strong>
                          </span>
                        )}
                      </div>

                      {/* Client Contact Details (Revealed or Masked) */}
                      <div style={{ background: selectedLead.status === "accepted" ? "rgba(16, 185, 129, 0.08)" : "var(--bg)", border: "1px solid " + (selectedLead.status === "accepted" ? "rgba(16, 185, 129, 0.3)" : "var(--border)"), borderRadius: "6px", padding: "0.85rem 1rem", margin: "0.75rem 0" }}>
                        <div style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", color: selectedLead.status === "accepted" ? "var(--emerald)" : "var(--ink-secondary)", marginBottom: "0.25rem" }}>
                          Client Identity & Telephonic Line
                        </div>
                        {selectedLead.status === "accepted" ? (
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div>
                              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)" }}>{selectedLead.client_name || "Client Verified"}</div>
                              <div style={{ fontSize: "0.84rem", color: "var(--brand)", marginTop: "2px" }}>
                                📞 <a href={`tel:${selectedLead.client_phone || "+919876543210"}`} style={{ color: "inherit", textDecoration: "underline" }}>
                                  {selectedLead.client_phone || "+91 98765 43210"}
                                </a>
                              </div>
                            </div>
                            <a
                              href={`tel:${selectedLead.client_phone || "+919876543210"}`}
                              className="action-btn action-btn-primary"
                              style={{ textDecoration: "none" }}
                            >
                              <PhoneCall size={12} /> Call Citizen Now
                            </a>
                          </div>
                        ) : (
                          <div style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                            🔒 <strong>Protected under DPDP Act:</strong> Citizen name &amp; direct telephone contact will be revealed immediately once you click &quot;Accept Consultation&quot;.
                          </div>
                        )}
                      </div>

                      {/* Case Brief */}
                      <div className="case-brief-block">
                        <div className="case-brief-label">DPDP Protected Case Brief</div>
                        {selectedLead.client_masked_brief}
                      </div>

                      {/* Attached Notice Preview if available */}
                      {selectedLead.attached_notice_title && (
                        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1.25rem" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div>
                              <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--brand)", textTransform: "uppercase" }}>📎 Attached Document</div>
                              <div style={{ fontSize: "0.84rem", fontWeight: 600, color: "var(--ink)" }}>{selectedLead.attached_notice_title}</div>
                            </div>
                            {selectedLead.attached_notice_content && (
                              <button
                                className="action-btn"
                                onClick={() => setActiveNoticePreview(selectedLead.attached_notice_content || "")}
                              >
                                View Notice Text
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="lead-actions">
                        <button
                          className="accept-btn"
                          onClick={() => updateLead("accept")}
                          disabled={selectedLead.status === "accepted"}
                        >
                          <Check size={14} />
                          {selectedLead.status === "accepted" ? "Consultation Accepted" : "Accept Consultation"}
                        </button>
                        <button
                          className="decline-btn"
                          onClick={() => updateLead("decline")}
                          disabled={selectedLead.status === "declined"}
                        >
                          Decline / Court Conflict
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* BARE ACTS LIBRARY VIEW */}
        {mainTab === "corpus" && (
          <div className="library-wrapper">
            <div className="library-header">
              <h2 className="library-title">Indian Bare Acts Library</h2>
              <p className="library-sub">Verbatim provisions indexed in Supabase pgvector for instant hybrid RAG search</p>
            </div>
            {corpusItems.length === 0 ? (
              <div style={{ textAlign: "center", padding: "5rem 2rem", color: "var(--ink-muted)" }}>
                <BookOpen size={40} style={{ marginBottom: "0.75rem", opacity: 0.3 }} />
                <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--ink)", marginBottom: "0.4rem" }}>Corpus Loading…</div>
                <p style={{ fontSize: "0.84rem" }}>Legal corpus sections appear here once the backend is connected and the Supabase pgvector DB is seeded.</p>
              </div>
            ) : (
              <div className="library-grid">
                {corpusItems.map(item => (
                  <div key={item.id} className="corpus-card">
                    <div className="corpus-card-top">
                      <span className="corpus-act-code">{item.act_code}</span>
                      <span style={{ fontSize: "0.68rem", color: "var(--ink-faint)" }}>{item.bailable_status}</span>
                    </div>
                    <div className="corpus-section-title">Section {item.section_number}: {item.section_title}</div>
                    <div className="corpus-act-name">{item.act_name} · {item.chapter}</div>
                    <p className="corpus-summary">{item.plain_summary}</p>
                    <div className="corpus-footer">
                      <div><strong>Limitation:</strong> {item.limitation_period}</div>
                      <div><strong>Penalty:</strong> {item.penalties}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── EMERGENCY AID BANNER ── */}
      <div className="aid-banner">
        <div className="aid-banner-inner">
          <div className="aid-banner-left">
            <AlertCircle size={15} style={{ color: "var(--brand)", flexShrink: 0 }} />
            <span>
              <strong>Free legal aid guaranteed</strong> under Legal Services Authorities Act, 1987 for eligible citizens
            </span>
          </div>
          <div className="aid-links">
            <a href="tel:15100" className="aid-link"><PhoneCall size={12} /> NALSA: 15100</a>
            <a href="tel:1930"  className="aid-link"><PhoneCall size={12} /> Cyber: 1930</a>
            <a href="tel:1091"  className="aid-link"><PhoneCall size={12} /> Women: 1091</a>
            <a href="tel:112"   className="aid-link"><PhoneCall size={12} /> Police: 112</a>
          </div>
        </div>
      </div>

      {/* ── CONSULTATION BOOKING MODAL (CITIZEN -> ADVOCATE) ── */}
      {bookingModalAdvocate && (
        <div className="booking-modal-overlay" onClick={() => !bookingLoading && setBookingModalAdvocate(null)}>
          <div className="booking-modal" onClick={e => e.stopPropagation()}>
            <div className="booking-modal-header">
              <div>
                <h3 className="booking-modal-title">Book Advocate Consultation</h3>
                <p className="booking-modal-sub">
                  Systematic connection with verified counsel practicing before your local jurisdiction.
                </p>
              </div>
              <button
                onClick={() => setBookingModalAdvocate(null)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-muted)" }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="booking-modal-body">
              {/* Advocate preview */}
              <div className="booking-adv-summary">
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)" }}>{bookingModalAdvocate.name}</div>
                  <div style={{ fontSize: "0.74rem", color: "var(--ink-muted)", marginTop: "2px" }}>
                    {bookingModalAdvocate.bar_council_id} · {bookingModalAdvocate.city}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--ink-secondary)", marginTop: "2px" }}>
                    Courts: {bookingModalAdvocate.courts.join(", ")}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--brand)" }}>₹{bookingModalAdvocate.consult_fee}</div>
                  <div style={{ fontSize: "0.68rem", color: "var(--ink-faint)" }}>/ consultation</div>
                </div>
              </div>

              {bookingSuccess ? (
                <div style={{ textAlign: "center", padding: "1.5rem 0" }}>
                  <div style={{ width: 48, height: 48, borderRadius: "50%", background: "var(--emerald-bg)", border: "1px solid var(--emerald-border)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1rem", color: "var(--emerald)" }}>
                    <Check size={24} />
                  </div>
                  <h4 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--ink)", marginBottom: "0.35rem" }}>
                    Consultation Request Confirmed!
                  </h4>
                  <p style={{ fontSize: "0.84rem", color: "var(--ink-secondary)", maxWidth: "400px", margin: "0 auto 1rem", lineHeight: 1.5 }}>
                    Your case brief has been transmitted to <strong>{bookingModalAdvocate.name}</strong>. The advocate will review your facts and connect with you as per your chosen slot.
                  </p>
                  <div style={{ fontSize: "0.75rem", background: "var(--bg)", border: "1px solid var(--border)", display: "inline-block", padding: "0.3rem 0.8rem", borderRadius: "4px", color: "var(--ink-muted)", marginBottom: "1.25rem" }}>
                    Booking Ref: <strong>{bookingSuccess}</strong>
                  </div>
                  <div>
                    <button
                      className="adv-submit-btn"
                      style={{ maxWidth: 200, margin: "0 auto" }}
                      onClick={() => {
                        setBookingModalAdvocate(null);
                        setBookingSuccess(null);
                      }}
                    >
                      Done
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleBookingSubmit}>
                  {/* Client name & phone */}
                  <div className="adv-form-grid-2">
                    <div className="adv-form-group">
                      <label className="adv-form-label">Your Name</label>
                      <input
                        type="text"
                        required
                        className="adv-form-input"
                        placeholder="e.g. Arun Kumar"
                        value={bookingForm.client_name}
                        onChange={e => setBookingForm(prev => ({ ...prev, client_name: e.target.value }))}
                      />
                    </div>
                    <div className="adv-form-group">
                      <label className="adv-form-label">Direct Contact Phone Number</label>
                      <input
                        type="tel"
                        required
                        className="adv-form-input"
                        placeholder="+91 98765 43210"
                        value={bookingForm.client_phone}
                        onChange={e => setBookingForm(prev => ({ ...prev, client_phone: e.target.value }))}
                      />
                    </div>
                  </div>

                  {/* Client locality & preferred court */}
                  <div className="adv-form-grid-2">
                    <div className="adv-form-group">
                      <label className="adv-form-label">Your Locality / Area</label>
                      <input
                        type="text"
                        className="adv-form-input"
                        placeholder="e.g. Saket, Bandra, Whitefield, Indiranagar"
                        value={clientLocality}
                        onChange={e => setClientLocality(e.target.value)}
                      />
                    </div>
                    <div className="adv-form-group">
                      <label className="adv-form-label">Preferred District Court</label>
                      <input
                        type="text"
                        className="adv-form-input"
                        placeholder="e.g. Saket District Court, Mayo Hall Court"
                        value={clientCourt || bookingModalAdvocate.district_court || ""}
                        onChange={e => setClientCourt(e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Consultation Mode Selector */}
                  <div className="adv-form-group">
                    <label className="adv-form-label">Preferred Consultation Mode</label>
                    <div className="booking-mode-selector">
                      {[
                        { id: "phone", title: "Phone Call", desc: "Direct 1-on-1 audio briefing", icon: <Phone size={16} /> },
                        { id: "video", title: "Video Consult", desc: "Screen share & document review", icon: <Video size={16} /> },
                        { id: "chamber", title: "Chamber Visit", desc: "In-person at court chamber", icon: <Building size={16} /> },
                      ].map(m => (
                        <div
                          key={m.id}
                          className={`booking-mode-card ${bookingForm.preferred_mode === m.id ? "selected" : ""}`}
                          onClick={() => setBookingForm(prev => ({ ...prev, preferred_mode: m.id }))}
                        >
                          <div style={{ color: "var(--brand)" }}>{m.icon}</div>
                          <div className="booking-mode-title">{m.title}</div>
                          <div className="booking-mode-desc">{m.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preferred Time Slot */}
                  <div className="adv-form-group">
                    <label className="adv-form-label">Preferred Time Window</label>
                    <select
                      className="adv-form-select"
                      value={bookingForm.preferred_slot}
                      onChange={e => setBookingForm(prev => ({ ...prev, preferred_slot: e.target.value }))}
                    >
                      <option value="Today (Next Available Slot)">Today (Next Available Slot)</option>
                      <option value="Tomorrow Morning (10:00 AM - 1:00 PM)">Tomorrow Morning (10:00 AM - 1:00 PM)</option>
                      <option value="Tomorrow Afternoon (2:00 PM - 5:00 PM)">Tomorrow Afternoon (2:00 PM - 5:00 PM)</option>
                      <option value="Tomorrow Evening (5:00 PM - 8:00 PM)">Tomorrow Evening (5:00 PM - 8:00 PM)</option>
                      <option value="Weekend (Saturday/Sunday)">Weekend (Saturday/Sunday)</option>
                    </select>
                  </div>

                  {/* Option to attach generated Legal Notice */}
                  {draftNotice && (
                    <div style={{ background: "var(--brand-soft)", border: "1px solid var(--brand-border)", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1.25rem" }}>
                      <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.82rem", color: "var(--ink)", fontWeight: 600 }}>
                        <input
                          type="checkbox"
                          checked={bookingForm.attach_notice}
                          onChange={e => setBookingForm(prev => ({ ...prev, attach_notice: e.target.checked }))}
                        />
                        <span>Attach synchronized Legal Notice to pre-brief counsel</span>
                      </label>
                      <div style={{ fontSize: "0.72rem", color: "var(--ink-muted)", marginTop: "0.25rem", paddingLeft: "1.45rem" }}>
                        The advocate will be able to review and inspect your 15-day statutory legal notice drafted from your chat.
                      </div>
                    </div>
                  )}

                  <div className="booking-modal-footer">
                    <button
                      type="button"
                      className="action-btn"
                      onClick={() => setBookingModalAdvocate(null)}
                      disabled={bookingLoading}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="adv-submit-btn"
                      style={{ marginTop: 0, width: "auto", padding: "0.6rem 1.4rem" }}
                      disabled={bookingLoading}
                    >
                      {bookingLoading ? "Submitting Request..." : "Confirm & Send Request"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── ATTACHED NOTICE VIEWER MODAL (FOR ADVOCATE DASHBOARD) ── */}
      {activeNoticePreview && (
        <div className="booking-modal-overlay" onClick={() => setActiveNoticePreview(null)}>
          <div className="booking-modal" style={{ maxWidth: 750 }} onClick={e => e.stopPropagation()}>
            <div className="booking-modal-header">
              <div>
                <h3 className="booking-modal-title">Attached Legal Notice</h3>
                <p className="booking-modal-sub">Drafted &amp; Synchronized from Citizen Consultation Chat</p>
              </div>
              <button
                onClick={() => setActiveNoticePreview(null)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink-muted)" }}
              >
                <X size={18} />
              </button>
            </div>
            <div className="booking-modal-body" style={{ maxHeight: "65vh", overflowY: "auto" }}>
              <div className="notice-document">
                <div className="notice-letterhead">
                  <Scale size={20} style={{ color: "rgba(255,255,255,0.75)", marginBottom: "0.4rem" }} />
                  <div className="notice-letterhead-title">Chambers of Advocates &amp; Legal Counsel</div>
                  <div className="notice-letterhead-sub">High Court &amp; District Courts Practice · India</div>
                </div>
                <div className="notice-body-text md-notice">
                  <ReactMarkdown>{activeNoticePreview}</ReactMarkdown>
                </div>
              </div>
            </div>
            <div className="booking-modal-footer">
              <button className="action-btn" onClick={() => setActiveNoticePreview(null)}>
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── VERIFIED CLIENT RATING & REVIEW MODAL ── */}
      {ratingModalAdvocate && (
        <div className="rating-modal-overlay" onClick={() => !submittingReview && setRatingModalAdvocate(null)}>
          <div className="rating-modal-card" onClick={e => e.stopPropagation()}>
            <div className="rating-modal-header">
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <div style={{ background: "rgba(245, 158, 11, 0.15)", padding: 6, borderRadius: 6, color: "#d97706" }}>
                  <Star size={18} fill="#d97706" />
                </div>
                <div>
                  <h3 className="rating-modal-title">Rate Verified Legal Services</h3>
                  <p className="rating-modal-sub">
                    Authorized client evaluation for <strong>{ratingModalAdvocate.name}</strong> ({ratingModalAdvocate.bar_council_id})
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => !submittingReview && setRatingModalAdvocate(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="rating-modal-body">
              {reviewSuccessMessage ? (
                <div className="review-success-banner">
                  <Check size={20} style={{ color: "#16a34a", margin: "0 auto 0.5rem" }} />
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#15803d" }}>Review Verified &amp; Recorded</div>
                  <p style={{ fontSize: "0.8rem", color: "#166534", marginTop: 4 }}>
                    {reviewSuccessMessage}
                  </p>
                </div>
              ) : (
                <>
                  {/* Verified Payment Escrow Badge */}
                  {(() => {
                    const paidRec = paidConsultations.find(p => p.advocateId === ratingModalAdvocate.id);
                    return (
                      <div className="verified-escrow-badge">
                        <ShieldCheck size={14} style={{ color: "#059669", flexShrink: 0 }} />
                        <div>
                          <strong>Verified Paid Consultation:</strong> Payment ID <code>{paidRec?.paymentId || "PAY-OV-CONFIRMED"}</code>
                          <span style={{ display: "block", fontSize: "0.68rem", color: "#065f46" }}>
                            Paid ₹{paidRec?.amountPaid || ratingModalAdvocate.consult_fee} via SafePay Escrow Authorization
                          </span>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Star Rating Selector */}
                  <div className="interactive-stars-row">
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--ink-secondary)", display: "block", marginBottom: "0.35rem" }}>
                      OVERALL ADVOCATE RATING (1-5 STARS):
                    </span>
                    <div className="star-buttons-wrap">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className="star-click-btn"
                          onClick={() => setUserStars(star)}
                          title={`${star} Star${star > 1 ? "s" : ""}`}
                        >
                          <Star
                            size={26}
                            fill={userStars >= star ? "#f59e0b" : "none"}
                            color={userStars >= star ? "#f59e0b" : "#cbd5e1"}
                          />
                        </button>
                      ))}
                      <span className="star-label-desc">
                        {userStars === 5 && "⭐⭐⭐⭐⭐ Outstanding Legal Counsel & Court Guidance"}
                        {userStars === 4 && "⭐⭐⭐⭐ Very Good Consultation & Prompt Advice"}
                        {userStars === 3 && "⭐⭐⭐ Satisfactory Service"}
                        {userStars === 2 && "⭐⭐ Needs Improvement"}
                        {userStars === 1 && "⭐ Unsatisfactory"}
                      </span>
                    </div>
                  </div>

                  {/* Sub-Criteria Sliders/Ratings */}
                  <div className="sub-ratings-grid">
                    <div className="sub-rating-item">
                      <div className="sub-rating-label">
                        <span>Legal Knowledge &amp; Strategy</span>
                        <strong>{userKnowledge}/5</strong>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={userKnowledge}
                        onChange={e => setUserKnowledge(Number(e.target.value))}
                        className="sub-rating-slider"
                      />
                    </div>
                    <div className="sub-rating-item">
                      <div className="sub-rating-label">
                        <span>Responsiveness &amp; Court Time</span>
                        <strong>{userResponsiveness}/5</strong>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={userResponsiveness}
                        onChange={e => setUserResponsiveness(Number(e.target.value))}
                        className="sub-rating-slider"
                      />
                    </div>
                    <div className="sub-rating-item">
                      <div className="sub-rating-label">
                        <span>Value for Consultation Fee</span>
                        <strong>{userValue}/5</strong>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={userValue}
                        onChange={e => setUserValue(Number(e.target.value))}
                        className="sub-rating-slider"
                      />
                    </div>
                  </div>

                  {/* Review Text */}
                  <div style={{ marginTop: "0.85rem" }}>
                    <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--ink)", display: "block", marginBottom: "0.35rem" }}>
                      CLIENT REVIEW &amp; CONSULTATION EXPERIENCE:
                    </label>
                    <textarea
                      className="review-textarea"
                      rows={3}
                      placeholder="Share specifics of how the advocate assisted you, their court insights, clarification of legal notice or case remedies..."
                      value={userReviewText}
                      onChange={e => setUserReviewText(e.target.value)}
                    />
                  </div>

                  <div className="rating-compliance-note">
                    <Lock size={12} style={{ flexShrink: 0 }} />
                    <span>
                      <strong>DPDP Act, 2023 &amp; BCI Transparency:</strong> Ratings are strictly verified against authenticated consultation payment IDs to eliminate fabricated reviews and protect advocate integrity.
                    </span>
                  </div>

                  <div className="rating-modal-footer">
                    <button
                      type="button"
                      className="action-btn"
                      onClick={() => setRatingModalAdvocate(null)}
                      disabled={submittingReview}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="adv-submit-btn"
                      style={{ marginTop: 0, width: "auto", padding: "0.6rem 1.4rem" }}
                      onClick={submitAdvocateReview}
                      disabled={submittingReview}
                    >
                      {submittingReview ? "Verifying & Submitting..." : "Submit Verified Rating"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── RATING LOCKED MODAL (FOR UNPAID / UNVERIFIED USERS) ── */}
      {ratingLockedModalAdvocate && (
        <div className="rating-modal-overlay" onClick={() => setRatingLockedModalAdvocate(null)}>
          <div className="rating-modal-card" style={{ maxWidth: 480 }} onClick={e => e.stopPropagation()}>
            <div className="rating-locked-box">
              <div className="rating-locked-icon-wrap">
                <Lock size={28} />
              </div>
              <h3 className="rating-locked-title">Verified Payment Required to Rate</h3>
              <p className="rating-locked-desc">
                Under OnlineVakeel&apos;s anti-tamper rating policy, clients can only rate an advocate after <strong>purchasing their legal consultation services</strong>.
              </p>

              <div className="advocate-fee-card-preview">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)" }}>{ratingLockedModalAdvocate.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--ink-secondary)" }}>
                      {ratingLockedModalAdvocate.bar_council_id} · {ratingLockedModalAdvocate.district_court || ratingLockedModalAdvocate.city}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--brand)" }}>₹{ratingLockedModalAdvocate.consult_fee}</div>
                    <div style={{ fontSize: "0.68rem", color: "var(--ink-muted)" }}>per consultation</div>
                  </div>
                </div>
              </div>

              <div style={{ fontSize: "0.74rem", color: "var(--ink-secondary)", background: "#f8fafc", padding: "0.75rem", borderRadius: "6px", border: "1px solid #e2e8f0", textAlign: "left", marginBottom: "1.25rem" }}>
                🔒 <strong>Why is this restricted?</strong> Fake and unverified reviews violate Bar Council ethical transparency. OnlineVakeel ensures 100% of published ratings originate from authenticated citizens with verified payment escrows.
              </div>

              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="action-btn"
                  onClick={() => setRatingLockedModalAdvocate(null)}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="adv-submit-btn"
                  style={{ marginTop: 0, width: "auto", padding: "0.6rem 1.25rem" }}
                  onClick={() => {
                    const target = ratingLockedModalAdvocate;
                    setRatingLockedModalAdvocate(null);
                    openBookingModal(target);
                  }}
                >
                  <CreditCard size={14} style={{ marginRight: 6 }} />
                  Book &amp; Authorize Consultation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── VERIFIED CLIENT REVIEWS LIST DRAWER ── */}
      {reviewsModalAdvocate && (
        <div className="rating-modal-overlay" onClick={() => setReviewsModalAdvocate(null)}>
          <div className="verified-reviews-drawer" onClick={e => e.stopPropagation()}>
            <div className="reviews-drawer-header">
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <Star size={16} fill="#f59e0b" color="#f59e0b" />
                  <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--ink)" }}>
                    {reviewsModalAdvocate.rating ? reviewsModalAdvocate.rating.toFixed(1) : "5.0"}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                    ({reviewsModalAdvocate.reviews || advocateReviewsList.length} verified ratings)
                  </span>
                </div>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--ink)", marginTop: 2 }}>
                  Client Reviews: {reviewsModalAdvocate.name}
                </h3>
                <p style={{ fontSize: "0.72rem", color: "var(--ink-muted)" }}>
                  {reviewsModalAdvocate.bar_council_id} · {reviewsModalAdvocate.district_court || reviewsModalAdvocate.city}
                </p>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setReviewsModalAdvocate(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="reviews-drawer-body">
              {reviewsLoading ? (
                <div style={{ textAlign: "center", padding: "2rem", color: "var(--ink-muted)", fontSize: "0.85rem" }}>
                  Loading verified advocate reviews...
                </div>
              ) : advocateReviewsList.length === 0 ? (
                <div style={{ textAlign: "center", padding: "2rem", color: "var(--ink-muted)" }}>
                  <Star size={24} style={{ color: "#cbd5e1", margin: "0 auto 0.5rem" }} />
                  <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>No Reviews Yet</div>
                  <p style={{ fontSize: "0.75rem", marginTop: 4 }}>
                    Only clients who have booked and paid for a consultation with Adv. {reviewsModalAdvocate.name} are eligible to leave verified reviews.
                  </p>
                </div>
              ) : (
                <div className="reviews-list-stack">
                  {advocateReviewsList.map(rev => (
                    <div key={rev.id} className="verified-review-card">
                      <div className="review-card-top">
                        <div>
                          <span className="review-client-name">{rev.client_name}</span>
                          <span className="review-date-tag">{rev.created_at}</span>
                        </div>
                        <div className="verified-paid-tag">
                          <Check size={11} /> Verified Paid Consultation
                        </div>
                      </div>

                      <div className="review-stars-row">
                        {[1, 2, 3, 4, 5].map(s => (
                          <Star
                            key={s}
                            size={13}
                            fill={rev.rating >= s ? "#f59e0b" : "none"}
                            color={rev.rating >= s ? "#f59e0b" : "#cbd5e1"}
                          />
                        ))}
                        <span className="review-stars-score">{rev.rating.toFixed(1)} / 5.0</span>
                      </div>

                      <p className="review-text-body">&quot;{rev.review_text}&quot;</p>

                      {(rev.knowledge_rating || rev.responsiveness_rating || rev.value_rating) && (
                        <div className="review-breakdown-tags">
                          {rev.knowledge_rating && (
                            <span className="review-mini-tag">Knowledge: {rev.knowledge_rating}/5</span>
                          )}
                          {rev.responsiveness_rating && (
                            <span className="review-mini-tag">Responsiveness: {rev.responsiveness_rating}/5</span>
                          )}
                          {rev.value_rating && (
                            <span className="review-mini-tag">Value: {rev.value_rating}/5</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="reviews-drawer-footer">
              <button
                type="button"
                className="action-btn"
                style={{ width: "100%" }}
                onClick={() => setReviewsModalAdvocate(null)}
              >
                Close Reviews
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── FOOTER ── */}
      <footer className="site-footer">
        <strong>OnlineVakeel.com</strong> · DPDP Act, 2023 Compliant · Supabase pgvector Legal RAG
        <div style={{ marginTop: "0.3rem", color: "var(--ink-ghost)" }}>
          Disclaimer: This platform provides pre-litigation informational guidance grounded in public Indian Bare Acts. It does not constitute legal advice. Consultation handoffs connect citizens with independent enrolled advocates.
        </div>
      </footer>
    </div>
  );
}

/**
 * useSearchParams() opts the tree into client-side rendering, which Next.js
 * requires to sit behind a Suspense boundary. Without this wrapper the
 * production build fails while prerendering /consult.
 */
export default function ConsultPage() {
  return (
    <Suspense fallback={null}>
      <ConsultDesk />
    </Suspense>
  );
}
