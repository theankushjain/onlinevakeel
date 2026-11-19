# OnlineVakeel — High-Level System Design

OnlineVakeel helps a person in India describe a legal problem in plain language, get an answer grounded in Indian statutes and known judgments, receive a draft pre-litigation document, and book a local advocate.

It is a **multi-agent application in the practical sense**: one coordinator runs a fixed sequence of specialist steps. The specialists do not chat with each other. Each step reads the case so far, does one job, and passes a structured result forward.

This document describes the system as it is built today (FastAPI backend, Next.js frontend). It uses simple language. Diagrams show who talks to whom.

---

## 1. What the system does

A citizen types a question such as “My builder in Bengaluru delayed my flat by two years after I paid ₹75 lakhs.”

The system then:

1. Hides personal identifiers (phone, Aadhaar, PAN, email) before anything else sees the text.
2. Checks whether the situation is an emergency (arrest, violence, suicide) or a deadline that is about to expire.
3. Turns the sentence into a case: legal category, money, dates, city, district, and court.
4. Looks up matching Bare Act sections and known judgments from a legal library.
5. Checks that those citations exist in the trusted library.
6. Writes a plain-language explanation (English or Hindi).
7. Drafts a legal notice that updates as the conversation continues.
8. Ranks verified advocates by practice area, city, locality, and district court.
9. Lets the citizen book a call, video, or chamber visit. The advocate sees a masked brief until they accept.

The product is **legal information and document preparation**, plus a path to a human lawyer. It is not a substitute for a court filing or a licensed opinion.

---

## 2. Who uses it

| User | What they do | Where they work |
| --- | --- | --- |
| Citizen | Asks a question, reads guidance, reviews the notice, books a lawyer | Landing page and Consultation Desk |
| Advocate | Registers with a Bar Council ID, signs in, accepts or declines leads, sees contact details only after acceptance | Advocate portal on the same Consultation Desk |
| Operator / developer | Ingests Bare Act PDFs and court judgments into the library | Offline scripts, not the live chat |

---

## 3. The big picture

Three layers sit between the user and the legal library.

```mermaid
flowchart LR
    Citizen[Citizen browser]
    Advocate[Advocate browser]

    subgraph FE["Frontend — Next.js"]
        Home[Landing page]
        Desk[Consultation Desk]
    end

    subgraph BE["Backend — FastAPI"]
        API[REST API]
        Orch[Orchestrator]
    end

    subgraph DATA["Knowledge and records"]
        Corpus[Legal corpus]
        Lawyers[Advocate directory]
        Leads[Consultation leads]
    end

    subgraph MODELS["Optional language models"]
        Gemini[Gemini]
        Qwen[Qwen]
        BGE[BGE embeddings]
    end

    Citizen --> Home
    Citizen --> Desk
    Advocate --> Desk
    Home -->|opens consult with the question| Desk
    Desk -->|HTTPS JSON| API
    API --> Orch
    Orch --> Corpus
    Orch --> Lawyers
    API --> Leads
    Orch -.-> Gemini
    Orch -.-> Qwen
    Corpus -.-> BGE
```

If a language-model key is missing, the chat and the notice still work. The system falls back to written templates and keyword rules. The legal library also works without a cloud database: a built-in set of Bare Acts and landmark cases is always available.

---

## 4. Main building blocks

```mermaid
flowchart TB
    subgraph Client
        LP[page.tsx<br/>ask a question]
        CP[consult/page.tsx<br/>chat, notice, advocates, portal]
    end

    subgraph API["app/main.py"]
        Consult["POST /api/consult"]
        Draft["POST /api/draft"]
        Adv["Advocate register, login, search, reviews"]
        Hand["POST /api/handoff"]
        Lead["Leads list and accept or decline"]
        Dist["GET /api/districts"]
        Corp["GET /api/corpus"]
    end

    subgraph Pipeline["One consultation"]
        PII[PII redactor]
        Triage[Urgency triage]
        Intake[Intake agent]
        Research[Research agent]
        Verify[Verifier agent]
        DraftA[Drafting agent]
        Handoff[Handoff agent]
        Talk[Conversational agent]
        Coord[Orchestrator]
    end

    subgraph Store
        DB[Database client<br/>Supabase or in-memory corpus]
        Sess[Session memory<br/>in the API process]
        LeadMem[Lead memory<br/>in the API process]
    end

    LP --> CP
    CP --> Consult
    CP --> Adv
    CP --> Hand
    CP --> Lead
    Consult --> Coord
    Coord --> PII --> Triage --> Intake --> Research --> Verify
    Coord --> DraftA
    Coord --> Handoff
    Coord --> Talk
    Research --> DB
    Handoff --> DB
    Verify --> DB
    Coord --> Sess
    Hand --> LeadMem
```

| Piece | Job in one sentence |
| --- | --- |
| Landing page | Collects the first question and opens the desk with that text. |
| Consultation Desk | Chat, dossier (laws, notice, advocates), and the advocate login. |
| FastAPI | The only door the browser uses. Validates requests and returns JSON. |
| Orchestrator | Runs the steps in order and keeps the case for follow-up messages. |
| Safety | Masks personal data, then labels emergency / urgent / routine. |
| Intake | Classifies the dispute and pulls out facts and place. |
| Research | Finds up to three matching sections from the library. |
| Verifier | Accepts a citation only if that section is in the trusted list. |
| Conversational agent | Turns those sections into a human reply. This is the only step that calls a chat model. |
| Drafting agent | Builds or refreshes the notice from the same facts. May call Gemini; otherwise uses a template. |
| Handoff agent | Writes a short brief and asks the directory for ranked lawyers. |
| Database client | Searches laws and lawyers. Uses Supabase when configured, otherwise the built-in lists. |

---

## 5. How one question is answered

Every message to `POST /api/consult` walks the same path. Later messages in the same session reuse facts already collected (money, dates, city, category) so the user does not have to repeat them.

```mermaid
sequenceDiagram
    actor User
    participant UI as Consultation Desk
    participant API as FastAPI
    participant O as Orchestrator
    participant S as Safety
    participant I as Intake
    participant R as Research
    participant V as Verifier
    participant D as Drafting
    participant H as Handoff
    participant C as Conversational
    participant Lib as Legal library

    User->>UI: Describes the problem
    UI->>API: message, session id, chat history
    API->>O: process consultation

    O->>S: redact personal data
    S-->>O: masked text
    O->>S: check urgency
    S-->>O: routine, urgent, or emergency

    O->>I: classify and extract facts
    I-->>O: category, amount, dates, city, court
    Note over O: Merge with earlier facts for this case id

    O->>R: category + masked question + facts
    R->>Lib: hybrid search, top 3
    Lib-->>R: sections and summaries
    R-->>O: remedies and a suggested next step

    O->>V: check each citation
    V->>Lib: compare to trusted Bare Acts
    V-->>O: passed, or needs advocate review

    O->>D: draft or refresh the notice
    D-->>O: title and notice text

    O->>H: brief + match lawyers
    H->>Lib: rank by court, locality, city, practice
    H-->>O: brief and advocate list

    O->>C: write the reply from verified remedies
    C-->>O: plain-language guidance

    O-->>API: one response packet
    API-->>UI: guidance, laws, notice, lawyers, badges
    UI-->>User: chat reply plus updated dossier
```

The reply packet always contains the same kinds of fields: case id, category, urgency, extracted facts, guidance text, statutory remedies, verification result, draft notice, advocate brief, and matched advocates.

### What “session” means

The orchestrator keeps cases in memory, keyed by case id. The browser sends that id back as `session_id`.

On a follow-up:

- If the new message looks like a general remark, the earlier legal category is kept.
- New amounts, dates, parties, city, locality, and court fill in blanks or replace older place names when the user states them again.
- The notice is regenerated from the full chat, so a later sentence (“I have a video recording”) can add the electronic-evidence paragraph.

Restarting the API clears this memory. Leads booked with an advocate live in a separate in-memory list on the API, also cleared on restart, unless a real database is wired later.

---

## 6. The agents, and how they depend on each other

They are specialists behind one coordinator. Arrows mean “this step’s output is an input to the next.” There is no agent-to-agent conversation.

```mermaid
flowchart TD
    Q[Citizen message]

    Q --> PII[1. PII redactor<br/>mask phone, Aadhaar, PAN, email]
    PII --> U[2. Urgency triage<br/>emergency, urgent, or routine]
    U --> IN[3. Intake<br/>category and facts]
    IN --> RS[4. Research<br/>up to 3 library hits]
    RS --> VF[5. Verifier<br/>keep only known sections]

    VF --> DR[6. Drafting<br/>notice text]
    VF --> HO[7. Handoff<br/>brief and lawyer ranking]
    VF --> CV[8. Conversational<br/>the words the user reads]

    U --> CV
    IN --> DR
    IN --> HO
    IN --> CV

    DR --> OUT[Single JSON response]
    HO --> OUT
    CV --> OUT
    VF --> OUT
```

| Step | Reads | Produces | Uses a language model? |
| --- | --- | --- | --- |
| PII redactor | Raw message | Masked text and a list of what was hidden | No. Pattern matching. |
| Urgency triage | Masked text | `emergency`, `urgent`, or `routine`, plus helplines when needed | No. Keyword lists. |
| Intake | Masked text and prior chat | One of 8 categories, money, dates, parties, district, state, court | No. Keywords plus a district catalog. |
| Research | Category, question, facts | Remedies: Act, section, plain summary, limitation, relief | No for the decision. Optional embedding model only to rank library rows. |
| Verifier | Those remedies | Pass, or “needs advocate review,” plus a badge | No. Exact match against the built-in corpus. |
| Drafting | Category, facts, full user chat, remedies | Notice title and body | Gemini if a key exists; otherwise a fixed notice template. |
| Handoff | Case, category, facts, remedies, urgency | Confidential brief and ranked advocates | No. |
| Conversational | Masked question, facts, remedies, triage, history | The chat answer | Hindi prefers Qwen, then Gemini, then Qwen again, then a written explanation. English prefers Gemini, then Qwen, then the written explanation. |

### Intake categories

The intake step picks the first matching theme:

- Cheque bounce
- Consumer dispute
- Property and RERA
- Cyber fraud
- Employment and labour
- Criminal bail
- RTI and public authorities
- General civil, when none of the above match

Place is resolved from aliases (for example “Whitefield” or “Mayo Hall”) and from a catalog of Indian districts and their courts. Mentioning a court can fill in the city; mentioning a city can fill in a default court complex.

### Safety behaviour

Emergency language (arrest, custody, domestic violence, threat to life, and similar phrases) does **not** stop the pipeline. The conversational reply is instructed to lead with helplines: NALSA 15100, police 112, women 1091 / 181, cyber crime 1930, and Tele-Law 14430. Urgent language (limitation about to expire, summons, eviction today) marks the case urgent and still returns legal guidance.

Personal data is masked **before** intake, search, drafting, and any model call. The masks look like `[PHONE_REDACTED]`. The original numbers are not sent to Gemini, Qwen, or the embedding service.

---

## 7. How the answer stays tied to real law

The design goal is: the model may explain, but it may not invent the statute.

```mermaid
flowchart LR
    Query[Question plus category]

    subgraph Retrieval
        Emb[Optional BGE vector<br/>meaning match]
        Key[Keyword and Act boosts<br/>cheque, RERA, video, FIR...]
        RPC[Supabase match_legal_sections<br/>only if cloud DB is on]
    end

    Lib[(Trusted sections<br/>Bare Acts and landmark cases)]

    Query --> Emb
    Query --> Key
    Query --> RPC
    Lib --> Emb
    Lib --> Key
    RPC --> Hits[Top matches]
    Emb --> Hits
    Key --> Hits

    Hits --> Gate{Section exists<br/>in the trusted list?}
    Gate -->|yes| Show[Show to citizen<br/>and allow in the notice]
    Gate -->|no| Flag[Flag for advocate review]
```

Search order:

1. If Supabase is connected, call the database function `match_legal_sections` (vector plus text). Use that result when it returns rows.
2. Otherwise score the built-in library: embedding similarity when the embedding service is configured, plus strong keyword boosts (for example “builder” and “possession” raise RERA; “video” and “recording” raise the electronic-evidence section).
3. Return the best few rows. If nothing scores, return the first two library entries so the user still sees something known rather than a blank answer.

The verifier then checks section number and Act name against that same built-in list. A hit that is not in the list is marked for a human lawyer. The badge the user sees is either “Verified by Indian Bare Acts Engine” or “Pending Advocate Review.”

The library that ships with the app covers, among others: Negotiable Instruments Act (cheque bounce), Consumer Protection Act, RERA, Bharatiya Nyaya Sanhita (cheating), Bharatiya Sakshya Adhiniyam (electronic records), Bharatiya Nagarik Suraksha Sanhita (police investigation), Registration Act, RTI Act, and a handful of Supreme Court and High Court landmarks (including delayed-possession, cheque jurisdiction, electronic evidence, and a cyber-fraud illustration).

Two offline scripts grow that library when a database is configured:

- `ingest_pdf.py` — read a Bare Act PDF, split sections, optionally summarise with Gemini, store rows.
- `sync_aws_court_data.py` — pull public Supreme Court and High Court judgment PDFs from AWS Open Data and store holdings. No AWS account is required for the public buckets.

---

## 8. How the notice is created

The notice is a second product of the same turn, not a separate conversation.

```mermaid
flowchart TD
    Chat[All user messages so far]
    Facts[Structured facts<br/>amount, dates, city]
    Laws[Verified remedies]

    Chat --> Signals{Extra facts in the words?}
    Signals -->|video or audio| BSA[Add electronic evidence note]
    Signals -->|stamp paper or unregistered agreement| REG[Add registration note]
    Signals -->|cheque| NI[Cheque-bounce notice shape]
    Signals -->|builder or flat| RERA[RERA delay notice shape]
    Signals -->|consumer or refund| CPA[Consumer notice shape]

    Facts --> Body
    Laws --> Body
    BSA --> Body[Notice body]
    REG --> Body
    NI --> Body
    RERA --> Body
    CPA --> Body

    Gemini{Gemini key present?}
    Body --> Gemini
    Gemini -->|yes, and the call succeeds| LLM[Model-written notice<br/>still fed only these facts and sections]
    Gemini -->|no, or the call fails| TPL[Template notice for that category]

    LLM --> Panel[Notice tab: read, print, download PDF]
    TPL --> Panel
```

The browser renders the notice, prints it in a clean frame (without the rest of the website), and can download a PDF. The PDF is made in the browser. The server returns the text.

---

## 9. From answer to a human lawyer

Matching is a score, not a separate AI agent. Higher score means a closer fit. Filters (search text, maximum fee) remove people first; ranking orders who remains.

```mermaid
flowchart TD
    Citizen[Citizen on Advocates tab]
    Match[Ranked list from handoff]

    Citizen --> Match
    Match --> Pick[Chooses a lawyer]
    Pick --> Book[Booking form<br/>name, phone, mode, time, notice attachment]
    Book --> Pay[Recorded as a paid booking<br/>escrow is simulated in this build]
    Pay --> Lead[Lead stored for that advocate]

    Lead --> Portal[Advocate portal]
    Portal --> Decision{Accept or decline?}
    Decision -->|accept| Reveal[Phone number becomes visible<br/>call button appears]
    Decision -->|decline| Closed[Lead marked declined]

    Reveal --> Done[After the consult, citizen may leave a review]
    Done --> Check{Booking or payment id<br/>belongs to this lawyer?}
    Check -->|yes| Rating[Rating saved and average updated]
    Check -->|no| Deny[Review refused]
```

Ranking weights, applied in the directory:

| Signal | Why it matters | Points |
| --- | --- | --- |
| Same district court | The lawyer actually appears in that court | +50 |
| Office in the same locality | Chamber is near the citizen | +40 |
| Same city, or locality named inside the city | Territorial fit | +20 to +25 |
| Practice area matches the case category | A RERA matter prefers a RERA lawyer | +15 |

The brief sent with the match hides identity until acceptance: amount, dates, city, urgency, and the top statutory grounds. The citizen’s phone is stored on the lead and shown to the advocate only after they accept.

Reviews require a paid booking or payment id for that advocate. This stops anonymous ratings.

---

## 10. Language models, and life without them

Only two steps speak to a chat model. Search may call an embedding model. Everything else is rules.

```mermaid
flowchart TD
    Need[Need a citizen-facing paragraph]

    Need --> Hi{Hindi or Devanagari?}
    Hi -->|yes| Q1[Try Qwen first]
    Q1 -->|fails or no key| G[Try Gemini]
    Hi -->|no| G
    G -->|fails or no key| Q2[Try Qwen]
    Q2 -->|fails or no key| Det[Written explanation<br/>built from the retrieved sections]

    DraftNeed[Need notice text] --> G2{Gemini key?}
    G2 -->|yes| GD[Gemini draft]
    G2 -->|no or error| TD[Category template]
    GD -->|error| TD
```

The model is not asked to “know Indian law” on its own. The prompt is filled with the category, the extracted facts, and the sections the library already returned. If the model is down, the written fallback still quotes those same sections, limitation periods, and the next practical step (send a notice, call 1930, file an RTI, and so on).

If the intake step never found a city, the conversational step adds a short question asking for city or district, in English or Hindi.

---

## 11. Data the system remembers

```mermaid
erDiagram
    CASE ||--o{ MESSAGE : "chat history held by the browser"
    CASE {
        string case_id
        string category
        string urgency
        string amount
        string city
        string court
    }
    LEGAL_SECTION {
        string act_name
        string section_number
        string plain_summary
        string limitation
    }
    ADVOCATE ||--o{ REVIEW : has
    ADVOCATE ||--o{ LEAD : receives
    CASE ||--o| LEAD : "may become"
    LEAD {
        string lead_id
        string status
        string client_phone
        string preferred_mode
        string notice_text
    }
    ADVOCATE {
        string bar_council_id
        string city
        string district_court
        string practice_areas
        int consult_fee
    }
```

| Data | Where it lives today | Survives a restart? |
| --- | --- | --- |
| Chat transcript | Browser, sent back as `history` | Yes, until the tab is closed |
| Case facts (category, money, place) | Orchestrator memory in the API process | No |
| Legal sections | Built-in list; Supabase `legal_corpus` when configured | Yes for the built-in list; yes in Supabase if used |
| Advocate profiles added in the UI | API process list, plus built-in demo profiles | Custom registrations: no. Demo profiles: yes |
| Booked leads | API process list | No |
| Reviews | API process map | No |

Supabase, when URL and key are set, is the intended durable store for the legal corpus (with `pgvector` for similarity search) and can back the advocate directory. The consultation path in this codebase still keeps the live case and the lead inbox in process memory.

District and court names used by intake and by `GET /api/districts` come from a static catalog in the backend, mirrored for the UI.

---

## 12. The screens and the API they call

```mermaid
flowchart LR
    subgraph Citizen_journey
        A[Landing<br/>type a question] --> B[Desk · Chat]
        B --> C[Desk · Laws]
        B --> D[Desk · Notice]
        B --> E[Desk · Advocates]
        E --> F[Booking]
    end

    subgraph Advocate_journey
        G[Advocate login or register] --> H[Lead inbox]
        H --> I[Accept]
        I --> J[Call citizen]
    end

    B -->|POST /api/consult| API[(FastAPI)]
    C -->|GET /api/corpus| API
    E -->|GET /api/advocates| API
    F -->|POST /api/handoff| API
    G -->|POST /api/advocates/login or register| API
    H -->|GET /api/advocate/leads| API
    I -->|POST /api/advocate/leads/id/action| API
```

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Process is up; reports whether Supabase and Gemini are configured. |
| `POST /api/consult` | Full agent pipeline for one message. |
| `POST /api/draft` | Notice only, if a caller already has category and facts. |
| `GET /api/corpus` | List the built-in library for the Laws view. |
| `GET /api/districts` | Search states, districts, and courts. |
| `GET /api/advocates` | Filter and rank lawyers. |
| `POST /api/advocates/register` | Add a lawyer profile. |
| `POST /api/advocates/login` | Match Bar Council ID, email, or name. Returns a simple token string. |
| `POST /api/handoff` | Create a consultation lead. |
| `GET /api/advocate/leads` | Inbox, optionally for one advocate. |
| `POST /api/advocate/leads/{id}/action` | Accept or decline. |
| `POST /api/advocates/{id}/reviews` | Save a review after a paid booking. |
| `GET /api/advocates/{id}/reviews` | Read reviews. |

The browser talks only to this API (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`). The API allows browser calls from any origin so the local Next.js app on port 3000 can reach it.

---

## 13. Runtime shape

```mermaid
flowchart TB
    subgraph Laptop_or_server
        Next[Next.js :3000]
        Uvi[Uvicorn :8000]
        Mem[In-memory cases, leads, custom lawyers]
    end

    Next --> Uvi
    Uvi --> Mem

    Uvi -.->|optional| SB[(Supabase Postgres + pgvector)]
    Uvi -.->|optional| GM[Gemini API]
    Uvi -.->|optional| QW[Qwen API]
    Uvi -.->|optional| BG[BGE embedding API]

    Scripts[Ingest PDF / sync court data] -.-> SB
```

Two modes:

- **Zero-config.** No keys. Built-in statutes, demo advocates, template notices, template explanations. Enough to demonstrate the full citizen and advocate journey.
- **Connected.** Gemini and/or Qwen for wording, BGE for semantic ranking, Supabase for a larger corpus and the hybrid search function. If any of these calls fail, the same request continues on the zero-config path for that step.

There is one API process. It is a good fit for a demo and a single server. Case state and leads are not shared across multiple servers and are lost when the process stops.

---

## 14. Design choices, stated simply

**One coordinator, fixed order.** The user always gets laws, a check, a notice, a lawyer list, and a paragraph. A free-form swarm of agents would be harder to explain and easier to drift off the library.

**Rules before models.** Category, place, urgency, citation checks, and lawyer ranking do not depend on a model being awake or truthful.

**Library before prose.** The conversational and drafting steps are downstream of retrieval. They explain and format. They are not the source of the section numbers.

**Mask first.** Personal identifiers are stripped before search and before any outbound model call.

**Degrade, do not fail closed on wording.** A missing model key changes the tone of the paragraph and the notice. It does not remove the statutory hits or the lawyer list.

**Human at the end.** The product’s last mile is a Bar Council profile, a booking, and an accept action that reveals contact details. Emergency queries surface public helplines in the same response.

---

## 15. What this design does not claim

- Login is an identifier match. It does not verify a password against a secure store, and the token is not a signed session.
- “Verified advocate” in the demo data means the profile is present in the directory, not that a Bar Council API confirmed the enrolment.
- Payment and escrow are recorded on the lead. No payment gateway is called.
- The verifier checks the built-in corpus. A section that exists only in Supabase can be flagged even if retrieval returned it.
- Court and city mapping uses aliases and a district catalog. It is a helpful default, not a judicial determination of territorial jurisdiction.
- The system gives information and drafts. Filing, representation, and privileged advice stay with the advocate the citizen books.
