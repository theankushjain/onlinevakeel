# OnlineVakeel: System Architecture, AI Precision Engineering & Future Roadmap

> **Platform**: [onlinevakeel.com](https://onlinevakeel.com)  
> **Core Objective**: Transforming chaotic citizen grievances into grounded, legally precise statutory remedies, automated pre-litigation notices, and verified local advocate consultations under Indian law.

---

## 1. Executive Summary: Why Generic LLMs Fail in Indian Law

Generic Large Language Models (LLMs) like vanilla ChatGPT (GPT-4), Claude, or raw Gemini are general-purpose probabilistic next-token predictors. When tasked with Indian legal advisory, they suffer from critical failure modes:

1. **Hallucination of Repealed Laws**:
   - India enacted historic criminal justice overhauls effective July 1, 2024: the **Bharatiya Nyaya Sanhita, 2023 (BNS)**, **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)**, and **Bharatiya Sakshya Adhiniyam, 2023 (BSA)**.
   - Generic LLMs still persistently cite **Section 420 IPC**, **Section 156(3) CrPC**, or **Section 65B of the Indian Evidence Act**. Submitting these repealed citations in a current court or police complaint can lead to immediate dismissal.
2. **Fabrication of Non-Existent Precedents**:
   - General LLMs frequently hallucinate fake case citations, fictitious party names, or invented Supreme Court ratios.
3. **Ignorance of Territorial Jurisdiction**:
   - In Indian jurisprudence, cause of action and territorial court jurisdiction are strictly governed by statute (e.g., Section 142(2) NI Act for cheque bounce, Section 34 Consumer Protection Act, Section 20 CPC). Generic LLMs provide advice without identifying *which specific District Court complex* holds jurisdiction.
4. **Data Privacy & Statutory Violations**:
   - Citizens paste confidential information (Aadhaar, PAN, bank account numbers, phone numbers). Generic LLMs transmit this unmasked personal data to external model training pipelines in violation of India's **Digital Personal Data Protection Act, 2023 (DPDP Act)**.
5. **Lack of Court-Ready Actionability**:
   - General LLMs output vague conversational essays. They do not draft formal, statutory legal demand notices with exact calculation of statutory interest, limitation windows, and letterhead formatting, nor do they connect the citizen with verified local advocates.

**OnlineVakeel solves this with a Deterministic Multi-Agent Architecture** where the LLM is merely one controlled conversational component within a multi-tiered pipeline of statutory retrieval, PII redaction, verification, dynamic drafting, and jurisdictional matching.

---

## 2. End-to-End System Architecture

The following diagram illustrates the complete execution flow of an incoming citizen query through the multi-agent pipeline:

```
                            Citizen Query (Web / Mobile)
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 1. Safety & DPDP Privacy Layer (PIIRedactor)       │
                │    - Masks Phone, Aadhaar, PAN, Bank Accounts     │
                │    - Preserves legal entities & dispute facts     │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 2. Emergency Urgency Triage (UrgencyTriage)       │
                │    - Detects domestic violence, threats, suicide  │
                │    - Immediate NALSA 15100 / 112 escalation      │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 3. Legal Intake Agent (IntakeAgent)               │
                │    - Domain Classification (6 Legal Verticals)    │
                │    - Monetary Claims, Dates, Limitation triggers   │
                │    - Indian Cities (60+), Localities & Courts     │
                │    - Bi-directional City Inference Mapping        │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 4. Grounded Statutory RAG (ResearchAgent)         │
                │    - Queries Verified Indian Bare Acts (IndiaCode)│
                │    - Supreme Court & High Court Precedents        │
                └─────────────────────────┬─────────────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 5. Anti-Hallucination Gatekeeper (VerifierAgent)  │
                │    - Validates citations against canonical acts   │
                │    - Issues cryptographic verification badge      │
                └─────────────────────────┬─────────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │ 6. Grounded Guidance Agent    │   │ 7. Legal Drafting Agent       │
        │    (ConversationalAgent)      │   │    (DraftingAgent)            │
        │    - Primary: Gemini Flash API│   │    - Real-time Legal Notice   │
        │    - Fallback: Deterministic  │   │    - Synchronized with facts  │
        │      Human Legal Heuristics   │   │    - Client letterhead format │
        │    - In-Chat Location Prompt  │   │    - PDF & Print Synthesis    │
        │      & 1-Click City Chips     │   │                               │
        └───────────────┬───────────────┘   └───────────────┬───────────────┘
                        │                                   │
                        └─────────────────┬─────────────────┘
                                          │
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │ 8. Handoff & Proximity Matcher (DatabaseClient)   │
                │    - Exact District Court Match (+50 pts)         │
                │    - Chamber Locality Proximity (+40 pts)         │
                │    - City Territorial Jurisdiction (+25 pts)      │
                │    - Practice Area Alignment (+15 pts)            │
                │    - Auto-updates Dossier tab & renders badges    │
                └───────────────────────────────────────────────────┘
```

---

## 3. Deep Dive: The 8 Specialized Components

### 3.1. Safety & DPDP Privacy Layer (`PIIRedactor`)
- **Source File**: [backend/app/security/pii_redactor.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/security/pii_redactor.py)
- **Role**: Operates before any text is sent to an external model or database.
- **Implementation**:
  - Regex detection for Indian mobile numbers (`+91`, `0`, or 10-digit formats).
  - 12-digit Aadhaar card numbers with Verhoeff-style validation heuristics.
  - 10-character alphanumeric Indian Permanent Account Numbers (PAN).
  - Bank Account Numbers (9-18 digits) and 11-character Indian Financial System Codes (IFSC).
  - Masks these sensitive fields to `[PHONE_MASKED]`, `[AADHAAR_MASKED]`, `[PAN_MASKED]`, and `[BANK_ACC_MASKED]`.
- **Compliance**: Adheres to the **Digital Personal Data Protection Act, 2023 (DPDP Act)**. Only masked facts are processed.

### 3.2. Urgency Triage & Emergency Escalation (`UrgencyTriage`)
- **Source File**: [backend/app/agents/urgency_triage.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/urgency_triage.py)
- **Role**: Instant safety screening for emergency legal/physical distress.
- **Implementation**:
  - Classifies queries into: `emergency`, `urgent`, or `standard`.
  - Flags domestic violence, imminent arrest, custodial torture, criminal intimidation, or self-harm.
  - Injects priority alerts pointing to statutory emergency resources:
    - **NALSA (National Legal Services Authority)** Free 24/7 Helpline: **`15100`**
    - National Emergency Response Support System (ERSS): **`112`**
    - National Commission for Women (NCW) Helpline: **`7827170170`**

### 3.3. Intake & Fact Extraction Agent (`IntakeAgent`)
- **Source File**: [backend/app/agents/intake_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/intake_agent.py)
- **Role**: Converts unstructured natural language statements into formal legal case parameters.
- **Key Features**:
  1. **Vertical Classification**: Distinguishes between `cheque_bounce`, `property_rera`, `consumer_dispute`, `cyber_fraud`, `criminal_bail`, and `general_civil`.
  2. **Monetary Value Extraction**: Regex extraction handling Indian financial formats (e.g., `Rs 50,000`, `₹ 1.5 Lakh`, `2 Crore`).
  3. **Limitation Trigger Dates**: Extracts transaction dates to calculate strict statutory limitation deadlines (e.g., Section 138 NI Act 30-day notice window; Consumer Protection Act 2-year limitation).
  4. **All-Cities Catalog (60+ Indian Cities)**: Detects cities, union territories, and district judicial headquarters.
  5. **District Courts & Judicial Complexes Catalog**: Identifies major Indian court complexes (e.g., *Saket, Tis Hazari, Patiala House, Karkardooma, Rohini, Dwarka, Mayo Hall, Bandra, Borivali, Esplanade, Shivajinagar, Qaiserbagh, Sector 43 Chandigarh, Banipark Jaipur*).
  6. **Bi-directional City & Court Inference**: If a citizen writes *"I want to file in Mayo Hall"*, the engine automatically infers `Bengaluru`; if they mention *"Shivajinagar court"*, it infers `Pune`.

### 3.4. Grounded Statutory RAG (`ResearchAgent`)
- **Source File**: [backend/app/agents/research_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/research_agent.py)
- **Role**: Retrieves precise statutory sections and binding judicial precedents from a verified internal legal corpus.
- **Core Corpus Contents**:
  - **Negotiable Instruments Act, 1881**: Section 138 (dishonour of cheque for insufficiency of funds), Section 141 (offences by companies), Section 142 (cognizance of offences and territorial jurisdiction under *Dashrath Rupsingh Rathod* amendment).
  - **Real Estate (Regulation and Development) Act, 2016 (RERA)**: Section 18 (return of amount and interest for delayed possession), Section 31 (filing complaints before Adjudicating Officer/Authority), *Newtech Promoters v. State of UP (2021 SC)*.
  - **Consumer Protection Act, 2019**: Section 35 (manner in which complaint shall be made), Section 38 (procedure on admission), Section 47 (State Commission jurisdiction), e-Daakhil filing regulations.
  - **Bharatiya Nyaya Sanhita, 2023 (BNS)**: Section 318 (cheating and dishonestly inducing delivery of property - replacing IPC 420), Section 316 (criminal breach of trust).
  - **Bharatiya Sakshya Adhiniyam, 2023 (BSA)**: Section 63 (admissibility of electronic records and mandatory certificate requirement - replacing Section 65B of Evidence Act) + *Arjun Panditrao Khotkar (2020 SC)*.
  - **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)**: Section 175(3) (magistrate direction to investigate on police refusal to lodge FIR - replacing Section 156(3) CrPC).
  - **Registration Act, 1908**: Section 17 (compulsorily registrable documents) & Section 49 (effect of non-registration).

### 3.5. Anti-Hallucination Gatekeeper (`VerifierAgent`)
- **Source File**: [backend/app/agents/verifier_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/verifier_agent.py)
- **Role**: Cross-verifies every statutory citation extracted by the Research Agent against the canonical active database.
- **Verification Rule**: If a citation is not present in the verified statutory repository, it is rejected and flagged. Every verified response carries a cryptographic integrity badge:  
  `✅ 100% Verified Statutory Citation (India Code & SC Precedents Repository)`

### 3.6. Dual-Engine Conversational Guidance (`ConversationalAgent`)
- **Source File**: [backend/app/agents/conversational_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/conversational_agent.py)
- **Dual-Engine Design**:
  1. **Primary Cloud Engine**: Calls Google Gemini (`gemini-3.1-flash-lite`, `gemini-3.5-flash`) with system instructions strictly bounding generation to the retrieved statutory context and multi-turn history.
  2. **Deterministic Fallback Engine**: If the LLM API is unavailable, throttled, or offline, an internal legal explanation engine immediately generates an accurate, empathetic response based on the client's case facts and statutory citations.
- **Interactive In-Chat Location Triggering**:
  - If the client's initial message does not specify their location, the engine ends the response with an explicit prompt:  
    `📍 Which city or district court are you in?`
  - In the frontend chat UI, it renders **1-click quick-select city chips** (`🏛️ Delhi NCR`, `🏛️ Bengaluru`, `🏛️ Mumbai`, `🏛️ Pune`, `🏛️ Hyderabad`, etc.).
  - When the client responds with their location, the agent confirms:  
    `🎯 Location Matched: Verified advocates practicing in [Court, City] have been automatically prioritized in your Recommended Advocates list.`

### 3.7. Synchronized Legal Notice Generator (`DraftingAgent`)
- **Source File**: [backend/app/agents/drafting_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/drafting_agent.py)
- **Role**: Concurrently compiles an editable legal demand notice on formal advocate letterhead.
- **Notice Format Structure**:
  - `REGISTERED POST WITH A.D. / SPEED POST / LEGAL DEMAND NOTICE`
  - Formal letterhead title: *"Chambers of Advocates & Legal Counsel"*
  - Clear identification of Complainant / Claimant and Addressee / Defaulter.
  - Precise chronological recital of facts, dishonoured amounts, and cheque/agreement numbers.
  - Formal invocation of applicable statutory sections and judicial precedents.
  - Strict statutory cure window (e.g., 15-day demand notice under Section 138(c) of NI Act).
  - Notice of civil and criminal liability (including cost of notice and interest).
  - 1-click **Vector PDF Export** (clean A4 typography using `jsPDF`) and **Print**.

### 3.8. Handoff & Territorial Court Proximity Matcher (`HandoffAgent` + `DatabaseClient`)
- **Source File**: [backend/app/database/supabase_client.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/database/supabase_client.py)
- **Mathematical Scoring Formula**:
  $$\text{Total Score} = S_{\text{court}} + S_{\text{locality}} + S_{\text{city}} + S_{\text{domain}} + R_{\text{bar}}$$
  
| Match Layer | Weight | Logic & Jurisdiction Rationale |
| :--- | :---: | :--- |
| **Exact District Court Match** | **+50 pts** | Substring bidirectional match between advocate's designated court and citizen's preferred court. |
| **Chamber Locality Match** | **+40 pts** | Advocate's office address or chamber is located in the client's neighborhood/sub-district. |
| **City Territorial Jurisdiction** | **+25 pts** | Practice city matches client's city. |
| **Practice Area Specialization** | **+15 pts** | Advocate's enrolled practice areas include the active case category. |
| **Bar Council Verified Rating** | **+1 to +5 pts** | Peer rating and verified client reviews. |

- **Real-Time UI Synchronization**:
  - When a location is provided in chat, the frontend:
    1. Re-ranks the advocate list.
    2. Auto-switches the Dossier tab to the **"Advocates"** tab.
    3. Displays animated badges:
       - `🎯 100% Exact Court & Chamber Proximity Match`
       - `🏛️ Exact District Court Match: [Court Name]`
       - `🏢 Nearest Chamber in [Office Location]`
    4. Renders a clickable action pill inside the chat bubble:  
       `🎯 View Advocates in [Court/City] (Count) →`

---

## 4. Comprehensive Comparison: OnlineVakeel vs. Generic LLMs

| Evaluation Dimension | Generic LLMs (ChatGPT, Claude, Raw Gemini) | OnlineVakeel Multi-Agent Engine |
| :--- | :--- | :--- |
| **Criminal Law Framework** | Frequently quotes repealed **IPC (1860)**, **CrPC (1973)**, **Evidence Act (1872)**. | Strictly applies new **BNS 2023**, **BNSS 2023**, and **BSA 2023** statutory codes. |
| **Hallucination Risk** | **High**: Generates fictional case citations, non-existent sections, and wrong limitation periods. | **Zero Hallucination on Law**: Every citation is verified against canonical statutory database by `VerifierAgent`. |
| **Territorial Jurisdiction** | Ignores territorial jurisdiction; cannot match specific District Courts or Magistrate complexes. | **Exact Court Matching**: Matches specific court complexes (Saket, Tis Hazari, Mayo Hall, Bandra, etc.) with a +50 pt proximity score. |
| **Data Privacy (DPDP Act 2023)** | Citizen's phone, Aadhaar, and financial records are sent unmasked to external cloud LLM servers. | **DPDP-Compliant Masking**: Redacts Aadhaar, PAN, phone, and bank accounts *before* AI inference. |
| **Actionable Output** | Vague conversational essays requiring citizen to manually interpret law. | **Court-Ready Legal Notice**: Synthesizes formal legal demand notices with vector PDF download and print capabilities. |
| **Advocate Connectivity** | No connection to legal counsel; citizen is left on their own. | **Verified Advocate Handoff**: Connects citizen to enrolled Bar Council advocates with privacy-preserving masked briefs. |
| **Service Availability** | Single point of failure if the LLM API is down, throttled, or rate-limited. | **Dual-Engine Architecture**: Seamless failover to deterministic human legal explanation engine. |
| **Multi-Turn Context** | Often forgets earlier case facts (amount, dates) when a user asks a short follow-up query. | **Multi-Turn Fact Inheritance**: Persists monetary claims, dates, and locations across conversation turns. |
| **Emergency Detection** | Minimal or generic suicide disclaimers. | **Specialized Legal Triage**: Detects domestic violence, imminent arrest, and routes to **NALSA 15100** and **112**. |
| **Language Support** | Rigid English or awkward literal Hindi translations. | Natural layman English and conversational Hindi with vernacular legal terminology. |

---

## 5. Roadmap: How to Make OnlineVakeel Even Better & More Accurate

To scale OnlineVakeel into India's foremost legal intelligence engine, the following high-impact enhancements are recommended:

### 5.1. Semantic Hybrid Search (Dense Embeddings + BM25 via pgvector)
- **Current State**: Uses regex entity extraction and weighted SQL scoring.
- **Next Step**:
  - Chunk Bare Acts and High Court/Supreme Court judgments into 300-token semantic chunks.
  - Generate dense vector embeddings using **`BAAI/bge-m3`** (optimized for Indian multilingual text) or **`text-embedding-3-large`**.
  - Store vectors in Supabase PostgreSQL using the **`pgvector`** extension with an HNSW index.
  - Implement **Reciprocal Rank Fusion (RRF)** combining keyword BM25 search (for exact section numbers like "Section 138") with vector similarity (for concept matching like "cheque bounced due to signature mismatch").

### 5.2. Integration with AWS Open Data Indian High Court & Supreme Court Repositories
- **Current State**: Core Supreme Court precedents are stored internally.
- **Next Step**:
  - Connect to the public **AWS Open Data Registry of Indian Court Judgments** (millions of digitized judgments from the Supreme Court and all 25 High Courts).
  - Ingest judgments with automated metadata extraction (Judge name, Bench strength, Citation, Act, Section, Ratio Decidendi).
  - When a citizen asks about a dispute in Mumbai or Bengaluru, retrieve binding precedents from the **Bombay High Court** or **Karnataka High Court** specifically.

### 5.3. Automated Interactive Statutory Limitation Calculator
- **Current State**: Lists statutory limitation periods in text.
- **Next Step**:
  - Add an interactive visual timeline in the Dossier panel:
    - *Cheque Dishonour Memo Received Date* $\rightarrow$ **Day 0**
    - *Last Date to Issue 15-Day Statutory Demand Notice* $\rightarrow$ **Day 30**
    - *Defaulter's 15-Day Cure Window* $\rightarrow$ **Day 30 to Day 45**
    - *Limitation Window to File Sec 138 Criminal Complaint Before Magistrate* $\rightarrow$ **Day 45 to Day 75**
  - Sends automated SMS/WhatsApp alerts before limitation periods lapse.

### 5.4. Browser Geolocation & Automated District Court Geofencing
- **Current State**: Citizen selects or types their city/locality/court.
- **Next Step**:
  - Add optional 1-click **"📍 Use Current Location"** button utilizing `navigator.geolocation`.
  - Reverse geocode coordinates via OpenStreetMap / Nominatim to extract sub-district and postal pin code.
  - Geofence every District Court Complex in India to automatically pinpoint the competent court complex within 200 meters.

### 5.5. Multilingual Vernacular Voice Input (Bhashini & Whisper)
- **Current State**: Text-based chat in English and Hindi.
- **Next Step**:
  - Integrate **Bhashini** (Government of India's National Language Translation Mission) and OpenAI Whisper API.
  - Allow semi-urban and rural citizens to speak their legal issue in their native dialect (Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, Kannada, Odia).
  - Transcribe, translate, process via the multi-agent pipeline, and respond with synthetic vernacular voice output.

### 5.6. e-Courts CNR Number Integration & Cause List Tracking
- **Current State**: Pre-litigation notice and initial advocate consultation.
- **Next Step**:
  - Connect to the national **e-Courts Services API** via Case Number Record (CNR).
  - Allow citizens and advocates to track ongoing case status, next hearing dates, interim orders, and cause list positions directly inside the OnlineVakeel dashboard.

### 5.7. Fine-Tuned Legal Domain Adapter (LoRA / DPO)
- **Current State**: Prompt engineering on general Gemini models.
- **Next Step**:
  - Fine-tune a lightweight model (e.g., Llama 3 8B or Mistral NeMo) using **Direct Preference Optimization (DPO)** trained exclusively on:
    - 50,000+ verified Indian legal demand notices.
    - Verified Bar Council pleadings before High Courts and District Courts.
    - Indian legal drafting standards following the Civil Procedure Code (CPC) Order VI.

---

## 6. Key Code References

| Module / Feature | File Path |
| :--- | :--- |
| **Privacy Redaction Engine** | [backend/app/security/pii_redactor.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/security/pii_redactor.py) |
| **Emergency Triage** | [backend/app/agents/urgency_triage.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/urgency_triage.py) |
| **Intake & Location Extraction** | [backend/app/agents/intake_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/intake_agent.py) |
| **Statutory Research & Bare Acts** | [backend/app/agents/research_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/research_agent.py) |
| **Citation Verifier** | [backend/app/agents/verifier_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/verifier_agent.py) |
| **Dual-Engine Guidance & Prompts** | [backend/app/agents/conversational_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/conversational_agent.py) |
| **Notice Generator & PDF Synthesis**| [backend/app/agents/drafting_agent.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/drafting_agent.py) |
| **Advocate Proximity Matching** | [backend/app/database/supabase_client.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/database/supabase_client.py#L510-L582) |
| **Multi-Agent Orchestrator** | [backend/app/agents/orchestrator.py](file:///Users/apple/Desktop/Projects/onlinevakeel.com/backend/app/agents/orchestrator.py) |
| **Frontend UI, Matcher & Badges** | [frontend/src/app/consult/page.tsx](file:///Users/apple/Desktop/Projects/onlinevakeel.com/frontend/src/app/consult/page.tsx) |
